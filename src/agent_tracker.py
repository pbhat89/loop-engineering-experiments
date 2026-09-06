"""Agent lifecycle tracker for the claims-skill-loop build.

Maintains two files that are safe for a handful of concurrent writers:

* ``logs/agent_status.json``  - atomic current-state snapshot (dashboard source)
* ``logs/agent_events.jsonl`` - append-only lifecycle event log

Every agent records its lifecycle through the CLI (run from the repo root)::

    uv run python -m src.agent_tracker register --agent A2 --role "Data steward" --units 5
    uv run python -m src.agent_tracker start --agent A2 --task "Inspect dataset licence"
    uv run python -m src.agent_tracker complete-unit --agent A2 --artifact data/README.md
    uv run python -m src.agent_tracker review --agent A2 --note "ready for lead acceptance"
    uv run python -m src.agent_tracker done --agent A2          # lead only (acceptance)

Progress and ETA rules:

* overall % = completed weighted units / total weighted units, capped at 99 %
  until ``gates --passed`` records that the acceptance gates passed;
* ETA = remaining units x median observed seconds per completed unit; it is
  reported as unavailable until at least two units have completed anywhere.

Never write secrets, credentials, or raw prompts through this module.
"""
from __future__ import annotations

import argparse
import statistics
import sys
from typing import Any, Callable

from src.utils import (
    LOGS_DIR,
    FileLock,
    append_jsonl,
    atomic_write_json,
    parse_ts,
    read_json,
    rel,
    utc_now,
)

STATUS_PATH = LOGS_DIR / "agent_status.json"
EVENTS_PATH = LOGS_DIR / "agent_events.jsonl"
LOCK_PATH = LOGS_DIR / ".agent_status.lock"

VALID_STATUSES = ("queued", "running", "blocked", "review", "done", "failed")
ETA_UNAVAILABLE = "ETA unavailable — insufficient completed work"
MIN_UNITS_FOR_ETA = 2


# --------------------------------------------------------------------------- state


def _default_status() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "updated_at": utc_now(),
        "acceptance_gates_passed": False,
        "agents": [],
        "overall": {},
        "sources": {"status": rel(STATUS_PATH), "events": rel(EVENTS_PATH)},
    }


def load_status() -> dict[str, Any]:
    status = read_json(STATUS_PATH, default=None)
    return status if isinstance(status, dict) and "agents" in status else _default_status()


def _find(status: dict, agent_id: str) -> dict | None:
    return next((a for a in status["agents"] if a["agent_id"] == agent_id), None)


def _new_agent(agent_id: str, role: str, units: float) -> dict[str, Any]:
    return {
        "agent_id": agent_id,
        "role": role,
        "status": "queued",
        "current_task": None,
        "started_at": None,
        "updated_at": utc_now(),
        "finished_at": None,
        "completed_work_units": 0.0,
        "total_work_units": float(units),
        "percent_complete": 0.0,
        "eta_minutes": None,
        "eta_label": ETA_UNAVAILABLE,
        "blocked_by": [],
        "last_artifact": None,
        "note": None,
        "unit_completions": [],
    }


def _unit_duration_samples(status: dict) -> list[float]:
    """Observed seconds per completed unit: gaps between an agent's start and its successive completions."""
    samples: list[float] = []
    for agent in status["agents"]:
        prev = agent.get("started_at")
        for ts in agent.get("unit_completions", []):
            if prev:
                delta = (parse_ts(ts) - parse_ts(prev)).total_seconds()
                if delta >= 0:
                    samples.append(delta)
            prev = ts
    return samples


def _recompute(status: dict) -> None:
    agents = status["agents"]
    total = sum(a["total_work_units"] for a in agents)
    completed = sum(min(a["completed_work_units"], a["total_work_units"]) for a in agents)
    n_units = sum(len(a.get("unit_completions", [])) for a in agents)
    samples = _unit_duration_samples(status)
    median = statistics.median(samples) if (n_units >= MIN_UNITS_FOR_ETA and samples) else None

    counts = {s: 0 for s in VALID_STATUSES}
    blocked_units = 0.0
    for agent in agents:
        counts[agent["status"]] += 1
        remaining = max(agent["total_work_units"] - agent["completed_work_units"], 0.0)
        if agent["total_work_units"]:
            agent["percent_complete"] = round(100.0 * agent["completed_work_units"] / agent["total_work_units"], 1)
        else:
            agent["percent_complete"] = 0.0
        if agent["status"] == "done":
            agent["percent_complete"] = 100.0
        if agent["status"] == "blocked":
            blocked_units += remaining
        if agent["status"] in ("done", "failed"):
            agent["eta_minutes"], agent["eta_label"] = None, "—"
        elif median is not None:
            agent["eta_minutes"] = round(remaining * median / 60.0, 1)
            agent["eta_label"] = f"rough ETA ≈ {agent['eta_minutes']} min"
        else:
            agent["eta_minutes"], agent["eta_label"] = None, ETA_UNAVAILABLE

    remaining_total = max(total - completed, 0.0)
    percent = 100.0 * completed / total if total else 0.0
    if not status.get("acceptance_gates_passed"):
        percent = min(percent, 99.0)  # 100 % is reserved for passed acceptance gates
    eta_minutes = round(remaining_total * median / 60.0, 1) if median is not None else None
    if eta_minutes is None:
        eta_label = ETA_UNAVAILABLE
    else:
        eta_label = f"rough ETA ≈ {eta_minutes} min"
        if blocked_units > 0:
            eta_label += f" (uncertain: {blocked_units:g} units blocked)"
    status["overall"] = {
        "total_work_units": total,
        "completed_work_units": completed,
        "remaining_work_units": remaining_total,
        "blocked_work_units": blocked_units,
        "percent_complete": round(percent, 1),
        "completed_unit_count": n_units,
        "median_seconds_per_unit": round(median, 1) if median is not None else None,
        "eta_minutes": eta_minutes,
        "eta_label": eta_label,
        "eta_uncertain_due_to_blocked": blocked_units > 0,
        "eta_computed_at": utc_now(),
        "counts": {"configured": len(agents), **counts},
    }
    status["updated_at"] = utc_now()


def _refresh_dashboard() -> None:
    """Best-effort dashboard regeneration; the tracker must never fail because of it."""
    try:
        from src import dashboard  # local import: dashboard is optional during early bootstrap
    except ImportError:
        return
    try:
        dashboard.render()
    except Exception as exc:  # noqa: BLE001 - reported, not raised
        append_jsonl(
            EVENTS_PATH,
            {"timestamp": utc_now(), "agent_id": "tracker", "event": "dashboard_refresh_failed", "note": str(exc)[:300]},
        )


def _update(agent_id: str, event: str, mutate: Callable[[dict, dict], None], **fields: Any) -> dict:
    with FileLock(LOCK_PATH):
        status = load_status()
        agent = _find(status, agent_id)
        if agent is None:
            if event != "register":
                raise SystemExit(f"unknown agent {agent_id!r}; register it first")
            agent = _new_agent(agent_id, fields.get("role", agent_id), fields.get("units", 1.0))
            status["agents"].append(agent)
        mutate(agent, status)
        agent["updated_at"] = utc_now()
        _recompute(status)
        atomic_write_json(STATUS_PATH, status)
        record = {
            "timestamp": utc_now(),
            "agent_id": agent_id,
            "event": event,
            "status": agent["status"],
            "current_task": agent.get("current_task"),
            "completed_work_units": agent["completed_work_units"],
            "total_work_units": agent["total_work_units"],
            **{k: v for k, v in fields.items() if v not in (None, [], "")},
        }
        append_jsonl(EVENTS_PATH, record)
    _refresh_dashboard()
    return status


# --------------------------------------------------------------------------- public API


def register(agent_id: str, role: str, units: float) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        agent["role"] = role
        agent["total_work_units"] = float(units)

    return _update(agent_id, "register", mutate, role=role, units=float(units))


def start(agent_id: str, task: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        agent["status"] = "running"
        agent["started_at"] = agent.get("started_at") or utc_now()
        agent["blocked_by"] = []
        if task:
            agent["current_task"] = task

    return _update(agent_id, "start", mutate, task=task)


def progress(agent_id: str, task: str | None = None, artifact: str | None = None, note: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        if agent["status"] in ("queued", "review"):
            agent["status"] = "running"
            agent["started_at"] = agent.get("started_at") or utc_now()
        if task:
            agent["current_task"] = task
        if artifact:
            agent["last_artifact"] = artifact
        if note:
            agent["note"] = note

    return _update(agent_id, "progress", mutate, task=task, artifact=artifact, note=note)


def complete_unit(
    agent_id: str, units: float = 1.0, artifact: str | None = None, note: str | None = None, task: str | None = None
) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        if agent["status"] in ("queued", "blocked"):
            agent["status"] = "running"
        agent["started_at"] = agent.get("started_at") or utc_now()
        agent["completed_work_units"] = min(agent["completed_work_units"] + float(units), agent["total_work_units"])
        agent.setdefault("unit_completions", []).append(utc_now())
        if artifact:
            agent["last_artifact"] = artifact
        if note:
            agent["note"] = note
        if task:
            agent["current_task"] = task

    return _update(agent_id, "complete_unit", mutate, units=float(units), artifact=artifact, note=note, task=task)


def block(agent_id: str, blocked_by: list[str], note: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        agent["status"] = "blocked"
        agent["blocked_by"] = sorted(set(blocked_by))
        if note:
            agent["note"] = note

    return _update(agent_id, "block", mutate, blocked_by=blocked_by, note=note)


def unblock(agent_id: str, note: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        agent["status"] = "running"
        agent["blocked_by"] = []
        if note:
            agent["note"] = note

    return _update(agent_id, "unblock", mutate, note=note)


def review(agent_id: str, note: str | None = None, artifact: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        agent["status"] = "review"
        agent["blocked_by"] = []
        if note:
            agent["note"] = note
        if artifact:
            agent["last_artifact"] = artifact

    return _update(agent_id, "review", mutate, note=note, artifact=artifact)


def done(agent_id: str, note: str | None = None, artifact: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        if agent["completed_work_units"] < agent["total_work_units"]:
            snapped = f" [units snapped {agent['completed_work_units']:g}->{agent['total_work_units']:g} at acceptance]"
            agent["note"] = (note or "") + snapped
            agent["completed_work_units"] = agent["total_work_units"]
            agent.setdefault("unit_completions", []).append(utc_now())
        elif note:
            agent["note"] = note
        agent["status"] = "done"
        agent["finished_at"] = utc_now()
        agent["blocked_by"] = []
        if artifact:
            agent["last_artifact"] = artifact

    return _update(agent_id, "done", mutate, note=note, artifact=artifact)


def fail(agent_id: str, note: str | None = None) -> dict:
    def mutate(agent: dict, _: dict) -> None:
        agent["status"] = "failed"
        agent["finished_at"] = utc_now()
        if note:
            agent["note"] = note

    return _update(agent_id, "fail", mutate, note=note)


def set_gates(passed: bool, note: str | None = None) -> dict:
    with FileLock(LOCK_PATH):
        status = load_status()
        status["acceptance_gates_passed"] = bool(passed)
        _recompute(status)
        atomic_write_json(STATUS_PATH, status)
        append_jsonl(
            EVENTS_PATH,
            {"timestamp": utc_now(), "agent_id": "lead", "event": "acceptance_gates", "passed": bool(passed), "note": note},
        )
    _refresh_dashboard()
    return status


def format_table(status: dict) -> str:
    rows = [f"{'agent':<6}{'status':<9}{'units':<11}{'pct':>6}  {'eta':<40} current task"]
    for a in status["agents"]:
        units = f"{a['completed_work_units']:g}/{a['total_work_units']:g}"
        rows.append(
            f"{a['agent_id']:<6}{a['status']:<9}{units:<11}{a['percent_complete']:>5.1f}%  "
            f"{a['eta_label']:<40} {a.get('current_task') or '-'}"
        )
    o = status.get("overall", {})
    rows.append(
        f"overall: {o.get('completed_work_units', 0):g}/{o.get('total_work_units', 0):g} units, "
        f"{o.get('percent_complete', 0)}% | {o.get('eta_label', ETA_UNAVAILABLE)} | "
        f"gates passed={status.get('acceptance_gates_passed')}"
    )
    return "\n".join(rows)


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="agent_tracker", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name: str, *, agent: bool = True, **opts: dict) -> argparse.ArgumentParser:
        sp = sub.add_parser(name)
        if agent:
            sp.add_argument("--agent", required=True)
        for flag, kw in opts.items():
            sp.add_argument(flag, **kw)
        return sp

    add("register", **{"--role": {"required": True}, "--units": {"type": float, "required": True}})
    add("start", **{"--task": {}})
    add("progress", **{"--task": {}, "--artifact": {}, "--note": {}})
    add("complete-unit", **{"--units": {"type": float, "default": 1.0}, "--artifact": {}, "--note": {}, "--task": {}})
    add("block", **{"--by": {"nargs": "+", "required": True}, "--note": {}})
    add("unblock", **{"--note": {}})
    add("review", **{"--note": {}, "--artifact": {}})
    add("done", **{"--note": {}, "--artifact": {}})
    add("fail", **{"--note": {}})
    gates = add("gates", agent=False, **{"--note": {}})
    g = gates.add_mutually_exclusive_group(required=True)
    g.add_argument("--passed", action="store_true")
    g.add_argument("--not-passed", action="store_true")
    add("show", agent=False)
    return p


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    args = build_parser().parse_args(argv)
    if args.cmd == "register":
        status = register(args.agent, args.role, args.units)
    elif args.cmd == "start":
        status = start(args.agent, args.task)
    elif args.cmd == "progress":
        status = progress(args.agent, args.task, args.artifact, args.note)
    elif args.cmd == "complete-unit":
        status = complete_unit(args.agent, args.units, args.artifact, args.note, args.task)
    elif args.cmd == "block":
        status = block(args.agent, args.by, args.note)
    elif args.cmd == "unblock":
        status = unblock(args.agent, args.note)
    elif args.cmd == "review":
        status = review(args.agent, args.note, args.artifact)
    elif args.cmd == "done":
        status = done(args.agent, args.note, args.artifact)
    elif args.cmd == "fail":
        status = fail(args.agent, args.note)
    elif args.cmd == "gates":
        status = set_gates(bool(args.passed), args.note)
    else:
        status = load_status()
    print(format_table(status))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
