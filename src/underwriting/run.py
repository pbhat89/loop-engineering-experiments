"""Experiment-7 runner: drives one arm through one phase, case by case.

    python -m src.underwriting.run --run-id uw_001 --condition notebook --phase train
    python -m src.underwriting.run --run-id uw_001 --condition notebook --phase train --mode stub
    python -m src.underwriting.run status --run-id uw_001
    python -m src.underwriting.run audit  --run-id uw_001

Manual mode follows the claims runner's protocol exactly (``src/run_experiment.py``): the
graph pauses on a LangGraph interrupt, the request is written to

    artifacts/uw/<run_id>/requests/<arm>/<phase>_case<NN>_<step>[_rN].json

and the runner returns, printing ``OPERATOR NEEDED``. The orchestrator spawns one fresh
operator subagent, which writes

    artifacts/uw/<run_id>/responses/<arm>/<same name>.json

and the same command is run again; it resumes from the checkpoint. With ``--poll`` the
runner waits for the response file itself instead of returning.

**Arms are independent.** Five runner processes can run at the same time: they share the
frozen data pack (read only) and touch nothing else in common. Within an arm, run
``--phase train`` to completion before ``--phase holdout``: the held-out phase reads the
memory training left behind and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from src.llm_provider import ManualProvider, ProviderError, ProviderSettings, read_response_file
from src.underwriting.audit import audit_run
from src.underwriting.data import goldens_by_case_id, load_cases, load_manual, verify_freeze
from src.underwriting.graph import build_underwriting_graph
from src.underwriting.nodes import Services
from src.underwriting.state import CONDITIONS, PHASES, UwRequest, initial_state
from src.underwriting.stub import STUB_OPERATORS, build_stub_provider
from src.utils import (
    CONFIG_DIR,
    REPO_ROOT,
    append_jsonl,
    atomic_write_json,
    ensure_dir,
    read_json,
    read_yaml,
    rel,
    utc_now,
)

CONFIG_PATH = CONFIG_DIR / "underwriting.yaml"
DEFAULT_ARTIFACTS_ROOT = REPO_ROOT / "artifacts" / "uw"


def load_config(path: Path = CONFIG_PATH) -> dict:
    return read_yaml(path) if Path(path).exists() else {}


def run_root(run_id: str, config: dict | None = None) -> Path:
    root = (config or {}).get("artifacts_root")
    if not root:
        return DEFAULT_ARTIFACTS_ROOT / run_id
    base = Path(root)
    return (base if base.is_absolute() else REPO_ROOT / base) / run_id


# --------------------------------------------------------------------------- run state


def _state_path(root: Path) -> Path:
    return root / "run.json"


def load_run_state(root: Path) -> dict:
    return read_json(_state_path(root), default={}) or {}


def init_run_state(root: Path, run_id: str, config: dict, mode: str, provider_meta: dict, freeze: str) -> dict:
    state = load_run_state(root)
    if not state:
        state = {
            "run_id": run_id,
            "created_at": utc_now(),
            "freeze_sha256": freeze,
            "config": {k: config.get(k) for k in ("seed", "max_rerequests", "precedent_k", "max_questions", "trailing_window")},
            "arms": {},
        }
    state["mode"] = mode
    state["provider"] = provider_meta
    atomic_write_json(_state_path(root), state)
    return state


def _arm(state: dict, condition: str, phase: str) -> dict:
    arms = state.setdefault("arms", {}).setdefault(condition, {})
    return arms.setdefault(
        phase,
        {"next_case_index": 1, "status": "pending", "pending_request": None, "cases_done": 0, "started_at": utc_now()},
    )


# --------------------------------------------------------------------------- services


def build_services(run_id: str, config: dict, mode: str, stub_operator: str, freeze: str) -> tuple[Services, dict]:
    root = run_root(run_id, config)
    ensure_dir(root)
    if mode == "stub":
        # the stub leaves the same transcript a manual run would, so the leakage audit has files to read
        provider = build_stub_provider(stub_operator, transcript_root=root)
    else:
        provider = ManualProvider(
            ProviderSettings(
                mode="manual",
                model_identifier=config.get("model_identifier"),
                operator=config.get("operator"),
            )
        )

    def log(condition: str, record: dict) -> None:
        append_jsonl(root / condition / "cases.jsonl", record)

    services = Services(
        provider=provider,
        manual=load_manual(),
        goldens=goldens_by_case_id(),
        run_root=root,
        log=log,
        max_rerequests=int(config.get("max_rerequests", 2)),
        precedent_k=int(config.get("precedent_k", 3)),
        extra_log_fields={"freeze_sha256": freeze},
    )
    return services, provider.describe()


# --------------------------------------------------------------------------- the loop


def advance(
    run_id: str,
    condition: str,
    phase: str,
    *,
    mode: str = "manual",
    stub_operator: str = "learner",
    config: dict | None = None,
    max_cases: int | None = None,
    poll: bool = False,
    poll_interval: float | None = None,
    poll_timeout: float | None = None,
    quiet: bool = False,
) -> dict:
    """Run ``condition`` through ``phase`` until it needs an operator or finishes."""
    config = config if config is not None else load_config()
    if condition not in CONDITIONS:
        raise SystemExit(f"unknown condition {condition!r}; expected one of {CONDITIONS}")
    if phase not in PHASES:
        raise SystemExit(f"unknown phase {phase!r}; expected one of {PHASES}")

    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.types import Command

    freeze, drift = verify_freeze()
    if drift:
        raise SystemExit("frozen data pack has drifted:\n  " + "\n  ".join(drift))

    root = run_root(run_id, config)
    services, provider_meta = build_services(run_id, config, mode, stub_operator, freeze)
    state = init_run_state(root, run_id, config, mode, provider_meta, freeze)
    arm = _arm(state, condition, phase)

    cases = load_cases(phase)
    interval = float(poll_interval if poll_interval is not None else config.get("poll_interval_seconds", 5))
    timeout = float(poll_timeout if poll_timeout is not None else config.get("poll_timeout_seconds", 3600))

    ensure_dir(root / "checkpoints")
    conn = str(root / "checkpoints" / f"{condition}_{phase}.sqlite")
    done_here = 0
    with SqliteSaver.from_conn_string(conn) as saver:
        graph = build_underwriting_graph(services, checkpointer=saver)
        while True:
            index = int(arm["next_case_index"])
            if index > len(cases):
                arm.update({"status": "done", "pending_request": None, "finished_at": utc_now()})
                atomic_write_json(_state_path(root), state)
                if not quiet:
                    print(f"DONE [{condition}/{phase}] {arm['cases_done']} cases")
                return {"status": "done", "condition": condition, "phase": phase, "pending_request": None}
            if max_cases is not None and done_here >= max_cases:
                atomic_write_json(_state_path(root), state)
                return {"status": arm["status"], "condition": condition, "phase": phase, "pending_request": arm.get("pending_request")}

            case = cases[index - 1]
            thread = {"configurable": {"thread_id": f"{run_id}:{condition}:{phase}:case{index:02d}"}}
            snapshot = graph.get_state(thread)
            pending = [i for t in (snapshot.tasks or ()) for i in (t.interrupts or ())]

            if pending:
                resumed = _serve(services, root, state, arm, pending[-1].value, poll, interval, timeout, quiet)
                if resumed is None:
                    return {"status": "waiting_operator", "condition": condition, "phase": phase,
                            "pending_request": arm.get("pending_request")}
                result = graph.invoke(Command(resume=resumed), config=thread)
            elif snapshot.values and snapshot.values.get("status") == "done":
                result = dict(snapshot.values)
            else:
                arm.update({"status": "running", "current_case": case["case_id"]})
                atomic_write_json(_state_path(root), state)
                result = graph.invoke(
                    initial_state(
                        run_id=run_id,
                        condition=condition,
                        phase=phase,
                        case=case,
                        manual=services.manual,
                        memory_root=rel(root),
                        mode=mode,
                        operator_name=provider_meta["operator"],
                        model_identifier=provider_meta["model_identifier"],
                    ),
                    config=thread,
                )

            while "__interrupt__" in result:
                resumed = _serve(services, root, state, arm, result["__interrupt__"][-1].value, poll, interval, timeout, quiet)
                if resumed is None:
                    return {"status": "waiting_operator", "condition": condition, "phase": phase,
                            "pending_request": arm.get("pending_request")}
                result = graph.invoke(Command(resume=resumed), config=thread)

            arm.update(
                {
                    "next_case_index": index + 1,
                    "cases_done": int(arm["cases_done"]) + 1,
                    "status": "running",
                    "pending_request": None,
                    "current_case": None,
                }
            )
            atomic_write_json(_state_path(root), state)
            done_here += 1


def _serve(services, root: Path, state: dict, arm: dict, value: dict, poll: bool, interval: float, timeout: float, quiet: bool):
    """Write the pending request, then wait for (or report) its response file."""
    request = UwRequest(**value)
    request_path = request.request_path(root)
    if not request_path.exists():
        request.write_request_file(root)
    response_path = request.response_path(root)
    ensure_dir(response_path.parent)
    arm.update({"status": "waiting_operator", "pending_request": rel(request_path), "waiting_since": utc_now()})
    atomic_write_json(_state_path(root), state)

    deadline = time.monotonic() + timeout
    while not response_path.exists():
        if not poll:
            if not quiet:
                print(f"OPERATOR NEEDED [{request.condition}/{request.phase}] -> {rel(request_path)}")
                print(f"                 response -> {rel(response_path)}")
            return None
        if time.monotonic() > deadline:
            raise SystemExit(f"timed out waiting for {rel(response_path)}")
        time.sleep(interval)
    try:
        response, _ = read_response_file(response_path)
    except ProviderError as exc:
        raise SystemExit(str(exc)) from exc
    arm.update({"status": "running", "pending_request": None, "waiting_since": None})
    atomic_write_json(_state_path(root), state)
    return response


# --------------------------------------------------------------------------- status and audit


def status(run_id: str, config: dict | None = None) -> dict:
    root = run_root(run_id, config if config is not None else load_config())
    return load_run_state(root)


def print_status(run_id: str, config: dict | None = None) -> None:
    state = status(run_id, config)
    if not state:
        print(f"run {run_id} has not started")
        return
    print(f"run {run_id} | mode {state.get('mode')} | freeze {(state.get('freeze_sha256') or '')[:12]} | {state.get('provider')}")
    print(f"{'arm':<16}{'phase':<10}{'status':<18}{'done':>6}  pending")
    for condition, phases in (state.get("arms") or {}).items():
        for phase, arm in phases.items():
            print(f"{condition:<16}{phase:<10}{arm.get('status', ''):<18}{arm.get('cases_done', 0):>6}  {arm.get('pending_request') or '-'}")


def audit(run_id: str, config: dict | None = None) -> list[str]:
    root = run_root(run_id, config if config is not None else load_config())
    goldens = goldens_by_case_id()
    markups: dict[str, str] = {}
    for path in sorted(root.rglob("notebook/markups.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                markups[record["case_id"]] = record["markup"]
    return audit_run(root, goldens, markups)


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", default="run", choices=("run", "status", "audit"))
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--condition", default=None)
    ap.add_argument("--phase", default=None, choices=(*PHASES, None))
    ap.add_argument("--mode", default=None, choices=("manual", "stub"))
    ap.add_argument("--stub-operator", default=None, choices=STUB_OPERATORS)
    ap.add_argument("--max-cases", type=int, default=None)
    ap.add_argument("--poll", action="store_true", help="wait for each response file instead of returning")
    ap.add_argument("--poll-interval", type=float, default=None)
    ap.add_argument("--poll-timeout", type=float, default=None)
    args = ap.parse_args(argv)

    config = load_config()
    if args.command == "status":
        print_status(args.run_id, config)
        return 0
    if args.command == "audit":
        problems = audit(args.run_id, config)
        for line in problems:
            print(f"LEAK: {line}")
        print(f"leakage audit: {len(problems)} problem(s)")
        return 1 if problems else 0

    if not args.condition or not args.phase:
        ap.error("--condition and --phase are required to run an arm")
    result = advance(
        args.run_id,
        args.condition,
        args.phase,
        mode=args.mode or config.get("mode", "manual"),
        stub_operator=args.stub_operator or config.get("stub_operator", "learner"),
        config=config,
        max_cases=args.max_cases,
        poll=args.poll,
        poll_interval=args.poll_interval,
        poll_timeout=args.poll_timeout,
    )
    return 0 if result["status"] in ("done", "running") else 0


if __name__ == "__main__":
    sys.exit(main())
