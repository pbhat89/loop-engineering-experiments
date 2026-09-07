"""Experiment runner: sequences T1..T8 per condition, drives the checkpointed LangGraph, and handles manual-mode operator steps.

Usage (from the repo root)::

    uv run python -m src.run_experiment freeze                               # Phase 1.5: hash data + goldens + tasks + rubric
    uv run python -m src.run_experiment init     --run-id run_001 --conditions baseline,reflection_only,skill_learning --mode manual
    uv run python -m src.run_experiment advance  --run-id run_001 --condition skill_learning
    uv run python -m src.run_experiment resume   --run-id run_001 --condition skill_learning --response <path>
    uv run python -m src.run_experiment pending  --run-id run_001
    uv run python -m src.run_experiment status   --run-id run_001
    uv run python -m src.run_experiment run-stub --run-id stub_001            # full deterministic run, no interrupts

``advance`` runs a condition until it either needs an operator (it prints the
request file path and returns) or finishes all tasks. When a response file
already exists for the pending request, ``advance`` resumes automatically;
``resume`` only copies a response into place and then advances.

Per-condition state (next task, operator steps used, per-task results) lives
in ``logs/runs/<run_id>.json``; LangGraph checkpoints live in
``logs/checkpoints/<run_id>.sqlite``; ``logs/experiment_status.json`` is the
dashboard snapshot (shape: docs/LEAD_DESIGN_DECISIONS.md §10).
"""
from __future__ import annotations

import argparse
import json
import shutil
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.graph_state import CONDITIONS, DEFAULT_CONDITIONS, initial_state
from src.llm_provider import (
    DEFAULT_MODEL_BY_MODE,
    DEFAULT_OPERATOR_BY_MODE,
    MANUAL_ROOT,
    OperatorRequest,
    ProviderError,
    ProviderSettings,
    get_provider,
    read_response_file,
)
from src.utils import (
    ARTIFACTS_DIR,
    CONFIG_DIR,
    DATA_DIR,
    GOLDENS_DIR,
    LOGS_DIR,
    REPO_ROOT,
    SKILLS_DIR,
    atomic_write_json,
    ensure_dir,
    parse_ts,
    read_json,
    read_yaml,
    rel,
    sha256_file,
    sha256_text,
    utc_now,
)

FREEZE_MANIFEST_PATH = CONFIG_DIR / "freeze_manifest.json"
ETA_UNAVAILABLE = "ETA unavailable — insufficient completed tasks"


@dataclass
class RunnerPaths:
    runs_dir: Path = LOGS_DIR / "runs"
    checkpoint_dir: Path = LOGS_DIR / "checkpoints"
    status_path: Path = LOGS_DIR / "experiment_status.json"
    manual_root: Path = MANUAL_ROOT
    tasks_root: Path = ARTIFACTS_DIR / "tasks"
    render_dashboard: bool = True


@dataclass
class RunConfig:
    run_id: str
    mode: str
    conditions: list[str]
    task_order: list[str]
    seed: int = 42
    max_retries: int = 2
    pass_threshold: float = 3.5
    max_operator_steps_per_condition: int = 40
    retrieval_k: int = 6
    model_identifier: str | None = None
    operator: str | None = None
    freeze_sha256: str = "unfrozen"
    # experiment 3 (D-21): capped, fix-free feedback and an empty starting skill library
    feedback_max_items: int | None = None
    reveal_fixes: bool = True
    foundational_skills: bool = True
    created_at: str = field(default_factory=utc_now)

    @classmethod
    def from_experiment_yaml(cls, run_id: str, mode: str, conditions: list[str], path: Path = CONFIG_DIR / "experiment.yaml") -> "RunConfig":
        cfg = read_yaml(path) if path.exists() else {}
        return cls(
            run_id=run_id,
            mode=mode,
            conditions=conditions,
            task_order=list(cfg.get("task_order") or ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"]),
            seed=int(cfg.get("seed", 42)),
            max_retries=int(cfg.get("max_retries", 2)),
            pass_threshold=float(cfg.get("pass_threshold", 3.5)),
            max_operator_steps_per_condition=int(cfg.get("max_operator_steps_per_condition", 40)),
            retrieval_k=int(cfg.get("retrieval_k", 6)),
            model_identifier=cfg.get("model_identifier") if mode == "manual" else None,
            operator=cfg.get("operator") if mode == "manual" else None,
            feedback_max_items=(int(cfg["feedback_max_items"]) if cfg.get("feedback_max_items") is not None else None),
            # the fixture and the rule learner apply the literal fix by construction; hiding it only makes sense for a model
            reveal_fixes=bool(cfg.get("reveal_fixes", True)) if mode == "manual" else True,
            foundational_skills=bool(cfg.get("foundational_skills", True)),
        )

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}  # type: ignore[attr-defined]


# --------------------------------------------------------------------------- freeze (Phase 1.5)


def build_freeze_manifest(write: bool = True) -> dict:
    """Hash the task suite, rubric, golden pack and raw data files; optionally write config/freeze_manifest.json."""
    entries: dict[str, str] = {}
    for path in [CONFIG_DIR / "tasks.yaml", CONFIG_DIR / "rubric.yaml"]:
        if path.exists():
            entries[rel(path)] = sha256_file(path)
    for folder, pattern in ((GOLDENS_DIR, "*"), (DATA_DIR / "raw", "*.csv")):
        if folder.exists():
            for path in sorted(folder.glob(pattern)):
                if path.is_file() and not path.name.startswith("."):
                    entries[rel(path)] = sha256_file(path)
    manifest = {"frozen_at": utc_now(), "files": entries}
    manifest["freeze_sha256"] = sha256_text(json.dumps(entries, sort_keys=True))
    if write:
        atomic_write_json(FREEZE_MANIFEST_PATH, manifest)
    return manifest


def verify_freeze() -> tuple[str, list[str]]:
    """Return (freeze_sha256, drift messages). Drift = missing manifest, changed, added or removed files."""
    stored = read_json(FREEZE_MANIFEST_PATH, default=None)
    if not stored:
        return "", [f"{rel(FREEZE_MANIFEST_PATH)} does not exist - run `python -m src.run_experiment freeze` after the golden review"]
    current = build_freeze_manifest(write=False)["files"]
    drift = [f"changed or added: {p}" for p, h in current.items() if stored["files"].get(p) != h]
    drift += [f"removed: {p}" for p in stored["files"] if p not in current]
    return stored.get("freeze_sha256", ""), drift


# --------------------------------------------------------------------------- services


def summarize_manifest(manifest: dict) -> dict:
    """Operator-facing view of the data manifest: names, dtypes, keys, dates - no row values beyond short samples."""
    tables = {}
    for name, t in (manifest.get("tables") or {}).items():
        tables[name] = {
            "rows": t.get("rows"),
            "columns": [{"name": c.get("name"), "dtype": c.get("dtype"), "null_count": c.get("null_count")} for c in t.get("columns", [])],
            "candidate_keys": t.get("candidate_keys", []),
            "date_columns": t.get("date_columns", []),
            "date_ranges": t.get("date_ranges", {}),
        }
    return {"tables": tables, "relationships": list(manifest.get("relationships") or [])}


def load_tasks(path: Path = CONFIG_DIR / "tasks.yaml") -> dict[str, dict]:
    suite = read_yaml(path)
    return {t["task_id"]: t for t in suite.get("tasks", [])}


def load_golden_file(task_spec: dict) -> dict:
    path = REPO_ROOT / task_spec["golden_file"]
    if path.suffix in (".yaml", ".yml"):
        return read_yaml(path)
    return read_json(path, default={})


def build_services(config: RunConfig):
    """Wire the real modules. Imported lazily so this module loads even while other agents' modules are in progress."""
    from src.evaluator import evaluate
    from src.experiment_logger import ExperimentLogger
    from src.graph_nodes import Services
    from src.skill_store import SkillStore
    from src.skill_validator import validate as validate_skill
    from src.task_runner import execute as execute_task

    provider = get_provider(ProviderSettings(mode=config.mode, model_identifier=config.model_identifier, operator=config.operator))
    manifest = read_json(DATA_DIR / "processed" / "manifest.json", default={}) or {}
    tasks = load_tasks()
    return Services(
        provider=provider,
        execute_task=execute_task,
        evaluate=evaluate,
        skill_store=SkillStore(SKILLS_DIR, run_id=config.run_id, include_foundational=config.foundational_skills),
        validate_skill=validate_skill,
        logger=ExperimentLogger(LOGS_DIR),
        rubric=read_yaml(CONFIG_DIR / "rubric.yaml"),
        load_golden=load_golden_file,
        manifest_summary=summarize_manifest(manifest),
        retrieval_k=config.retrieval_k,
        task_titles={tid: spec.get("title", "") for tid, spec in tasks.items()},
        feedback_max_items=config.feedback_max_items,
        reveal_fixes=config.reveal_fixes,
    )


# --------------------------------------------------------------------------- runner


class Runner:
    def __init__(
        self,
        run_id: str,
        *,
        services_factory: Callable[[RunConfig], Any] = build_services,
        tasks: dict[str, dict] | None = None,
        manifest: dict | None = None,
        paths: RunnerPaths | None = None,
    ):
        self.run_id = run_id
        self.paths = paths or RunnerPaths()
        self.services_factory = services_factory
        self._tasks = tasks
        self._manifest = manifest
        self._services = None
        self.manifest_path = self.paths.runs_dir / f"{run_id}.json"
        self.run: dict = read_json(self.manifest_path, default=None) or {}

    # ---- lifecycle -------------------------------------------------------------------
    @classmethod
    def init(
        cls,
        run_id: str,
        conditions: list[str],
        mode: str,
        *,
        config: RunConfig | None = None,
        require_freeze: bool | None = None,
        **kwargs: Any,
    ) -> "Runner":
        for c in conditions:
            if c not in CONDITIONS:
                raise SystemExit(f"unknown condition {c!r}; expected {CONDITIONS}")
        config = config or RunConfig.from_experiment_yaml(run_id, mode, conditions)
        config.conditions = list(conditions)
        # reported runs (manual operator, rule learner) need the frozen golden pack; stub demos do not
        must_freeze = mode in ("manual", "rule_learner") if require_freeze is None else require_freeze
        if must_freeze:
            sha, drift = verify_freeze()
            if drift:
                raise SystemExit("freeze check failed - comparative runs need a frozen golden pack:\n  " + "\n  ".join(drift))
            config.freeze_sha256 = sha
        elif FREEZE_MANIFEST_PATH.exists():
            config.freeze_sha256 = read_json(FREEZE_MANIFEST_PATH).get("freeze_sha256", "unfrozen")
        runner = cls(run_id, **kwargs)
        if runner.run:
            raise SystemExit(f"run {run_id!r} already exists at {rel(runner.manifest_path)}")
        runner.run = {
            "run_id": run_id,
            "config": config.to_dict(),
            "provider": {
                "provider_mode": mode,
                "operator": config.operator or DEFAULT_OPERATOR_BY_MODE[mode],
                "model_identifier": config.model_identifier or DEFAULT_MODEL_BY_MODE[mode],
            },
            "conditions": {
                c: {
                    "status": "queued",
                    "next_task_index": 0,
                    "operator_steps_used": 0,
                    "current_task": None,
                    "current_node": None,
                    "pending_request": None,
                    "waiting_since": None,
                    "task_started_at": None,
                    "task_results": {},
                    "written_requests": [],
                }
                for c in conditions
            },
            "created_at": utc_now(),
            "updated_at": utc_now(),
        }
        runner._save()
        runner.write_status()
        return runner

    def _save(self) -> None:
        self.run["updated_at"] = utc_now()
        atomic_write_json(self.manifest_path, self.run)

    @property
    def config(self) -> RunConfig:
        return RunConfig(**self.run["config"])

    @property
    def services(self):
        if self._services is None:
            self._services = self.services_factory(self.config)
        return self._services

    @property
    def tasks(self) -> dict[str, dict]:
        if self._tasks is None:
            self._tasks = load_tasks()
        return self._tasks

    @property
    def manifest(self) -> dict:
        if self._manifest is None:
            self._manifest = read_json(DATA_DIR / "processed" / "manifest.json", default={}) or {}
        return self._manifest

    def _require_run(self) -> None:
        if not self.run:
            raise SystemExit(f"run {self.run_id!r} not found - run `init` first")

    # ---- graph helpers ---------------------------------------------------------------
    def _graph(self, saver):
        from src.claims_graph import build_claims_skill_graph

        return build_claims_skill_graph(self.services, checkpointer=saver)

    def _thread(self, condition: str, task_id: str) -> dict:
        return {"configurable": {"thread_id": f"{self.run_id}:{condition}:{task_id}"}}

    def _initial_state(self, condition: str, task_index: int) -> dict:
        cfg = self.config
        task_id = cfg.task_order[task_index]
        spec = self.tasks[task_id]
        manifest = dict(self.manifest)
        manifest["_path"] = rel(DATA_DIR / "processed" / "manifest.json")
        manifest["_data_dir"] = rel(DATA_DIR / "raw")
        provider = self.run["provider"]
        return initial_state(
            run_id=self.run_id,
            condition=condition,
            task_id=task_id,
            task_index=task_index,
            task_spec=spec,
            dataset_manifest=manifest,
            seed=cfg.seed,
            output_dir=rel(self.paths.tasks_root / self.run_id / condition / task_id),
            golden_path=spec.get("golden_file", ""),
            freeze_sha256=cfg.freeze_sha256,
            max_retries=cfg.max_retries,
            pass_threshold=cfg.pass_threshold,
            max_operator_steps=cfg.max_operator_steps_per_condition,
            remaining_task_ids=list(cfg.task_order[task_index + 1 :]),
            provider_mode=provider["provider_mode"],
            operator=provider["operator"],
            model_identifier=provider["model_identifier"],
            operator_steps_used=self.run["conditions"][condition]["operator_steps_used"],
        )

    def _log_operator_event(self, request: OperatorRequest, event_type: str, **extra: Any) -> None:
        logger = getattr(self.services, "logger", None)
        if logger is None or not hasattr(logger, "log_graph_event"):
            return
        logger.log_graph_event(
            {
                "run_id": request.run_id,
                "condition": request.condition,
                "task_id": request.task_id,
                "attempt": request.attempt,
                "timestamp": utc_now(),
                "event_type": event_type,
                "source_node": request.node,
                "destination_node": request.node,
                "route_reason": f"{event_type} seq={request.seq}",
                "request_id": request.request_id,
                "retry_count": request.attempt - 1,
                "status": "waiting_operator" if event_type != "operator_response" else "running",
                **self.run["provider"],
                **extra,
            }
        )

    def _write_request(self, condition: str, value: dict) -> OperatorRequest:
        request = OperatorRequest(**value)
        path = request.request_path(self.paths.manual_root)
        cond = self.run["conditions"][condition]
        if request.request_id not in cond["written_requests"]:
            request.write_request_file(self.paths.manual_root)
            cond["written_requests"].append(request.request_id)
            self._log_operator_event(request, "operator_request", request_path=rel(path))
            if request.payload.get("validation_errors"):
                self._log_operator_event(request, "operator_validation_error", validation_errors=request.payload["validation_errors"])
        cond.update(
            {
                "status": "waiting_operator",
                "current_task": request.task_id,
                "current_node": request.node,
                "pending_request": rel(path),
                "waiting_since": cond.get("waiting_since") if cond.get("pending_request") == rel(path) else utc_now(),
            }
        )
        return request

    # ---- advance / resume -------------------------------------------------------------
    def advance(self, condition: str, max_tasks: int | None = None) -> dict:
        """Run ``condition`` until an operator is needed or all tasks are done. Returns a summary dict."""
        self._require_run()
        if condition not in self.run["conditions"]:
            raise SystemExit(f"condition {condition!r} is not part of run {self.run_id!r}")
        from langgraph.checkpoint.sqlite import SqliteSaver
        from langgraph.types import Command

        ensure_dir(self.paths.checkpoint_dir)
        cfg = self.config
        cond = self.run["conditions"][condition]
        tasks_run = 0
        with SqliteSaver.from_conn_string(str(self.paths.checkpoint_dir / f"{self.run_id}.sqlite")) as saver:
            graph = self._graph(saver)
            while True:
                idx = cond["next_task_index"]
                if idx >= len(cfg.task_order):
                    cond.update({"status": "done", "current_task": None, "current_node": None, "pending_request": None, "waiting_since": None})
                    self._save()
                    self.write_status()
                    return {"status": "done", "condition": condition, "pending_request": None}
                if max_tasks is not None and tasks_run >= max_tasks:
                    self._save()
                    self.write_status()
                    return {"status": cond["status"], "condition": condition, "pending_request": cond.get("pending_request")}
                task_id = cfg.task_order[idx]
                thread = self._thread(condition, task_id)
                snapshot = graph.get_state(thread)
                interrupts = [i for t in (snapshot.tasks or ()) for i in (t.interrupts or ())]
                if interrupts:
                    request = self._write_request(condition, interrupts[-1].value)
                    response_path = request.response_path(self.paths.manual_root)
                    if not response_path.exists():
                        self._save()
                        self.write_status()
                        return {"status": "waiting_operator", "condition": condition, "pending_request": rel(request.request_path(self.paths.manual_root))}
                    response, digest = read_response_file(response_path)
                    self._log_operator_event(request, "operator_response", response_path=rel(response_path), response_sha256=digest)
                    cond.update({"status": "running", "pending_request": None, "waiting_since": None, "current_node": None})
                    result = graph.invoke(Command(resume=response), config=thread)
                elif snapshot.values and snapshot.values.get("status") == "done":
                    result = dict(snapshot.values)
                else:
                    cond.update({"status": "running", "current_task": task_id, "task_started_at": utc_now(), "current_node": "load_context"})
                    self._save()
                    self.write_status()
                    result = graph.invoke(self._initial_state(condition, idx), config=thread)
                if "__interrupt__" in result:
                    request = self._write_request(condition, result["__interrupt__"][-1].value)
                    self._save()
                    self.write_status()
                    return {"status": "waiting_operator", "condition": condition, "pending_request": rel(request.request_path(self.paths.manual_root))}
                self._record_task_result(condition, task_id, result)
                tasks_run += 1

    def _record_task_result(self, condition: str, task_id: str, result: dict) -> None:
        cond = self.run["conditions"][condition]
        started = cond.get("task_started_at")
        finished = utc_now()
        duration = (parse_ts(finished) - parse_ts(started)).total_seconds() if started else None
        evaluation = result.get("evaluation") or {}
        cond["task_results"][task_id] = {
            "score_total": evaluation.get("score_total"),
            "scores": evaluation.get("scores"),
            "passed": bool(evaluation.get("passed")),
            "first_attempt_passed": bool((result.get("evaluation_history") or [{}])[0].get("passed")),
            "execution_attempts": result.get("execution_attempts"),
            "execution_errors": result.get("execution_errors"),
            "retry_count": result.get("retry_count"),
            "skills_created": list(result.get("skills_created") or []),
            "skills_retrieved": [s.get("skill_id") for s in result.get("retrieved_skills") or []],
            "score_by_attempt": [e.get("score_total") for e in (result.get("evaluation_history") or [])],
            "stop_reason": result.get("stop_reason"),
            "operator_steps_used_after": result.get("operator_steps_used"),
            "started_at": started,
            "finished_at": finished,
            "duration_seconds": duration,
        }
        cond.update(
            {
                "operator_steps_used": int(result.get("operator_steps_used") or cond["operator_steps_used"]),
                "next_task_index": cond["next_task_index"] + 1,
                "current_task": None,
                "current_node": None,
                "pending_request": None,
                "waiting_since": None,
                "task_started_at": None,
                "status": "running",
            }
        )
        self._save()
        self.write_status()
        self._refresh_figures()

    def _refresh_figures(self) -> None:
        """Best-effort regeneration of the log-derived figures after each completed task (A5's charts)."""
        if not self.paths.render_dashboard:
            return
        try:
            from src.charts import render_all

            render_all(LOGS_DIR, ARTIFACTS_DIR / "figures")
        except Exception:  # noqa: BLE001 - figures never block the run
            pass

    def resume(self, condition: str, response_path: Path | str) -> dict:
        """Copy an operator response into place for the pending request, then advance."""
        self._require_run()
        cond = self.run["conditions"][condition]
        pending = cond.get("pending_request")
        if not pending:
            raise SystemExit(f"{condition} has no pending operator request")
        request = OperatorRequest(**read_json(REPO_ROOT / pending))
        target = request.response_path(self.paths.manual_root)
        source = Path(response_path)
        try:
            read_response_file(source)  # validates JSON before it is accepted
        except ProviderError as exc:
            raise SystemExit(str(exc)) from exc
        if source.resolve() != target.resolve():
            ensure_dir(target.parent)
            shutil.copyfile(source, target)
        return self.advance(condition)

    def pending(self) -> dict[str, str | None]:
        self._require_run()
        return {c: v.get("pending_request") for c, v in self.run["conditions"].items()}

    def advance_all(self) -> dict[str, dict]:
        """Advance every unfinished condition once (resuming any that have a response file) and return per-condition summaries."""
        self._require_run()
        return {c: self.advance(c) for c, v in self.run["conditions"].items() if v.get("status") != "done"}

    # ---- status snapshot --------------------------------------------------------------
    def status_snapshot(self) -> dict:
        cfg = self.config
        conditions: dict[str, dict] = {}
        for name, cond in self.run["conditions"].items():
            results = cond["task_results"]
            durations = [r["duration_seconds"] for r in results.values() if r.get("duration_seconds") is not None]
            completed = len(results)
            remaining = len(cfg.task_order) - completed
            median = statistics.median(durations) if len(durations) >= 2 else None
            eta_minutes = round(remaining * median / 60.0, 1) if median is not None else None
            conditions[name] = {
                "status": cond["status"],
                "current_task": cond.get("current_task"),
                "attempt": None,
                "current_node": cond.get("current_node"),
                "pending_request": cond.get("pending_request"),
                "waiting_since": cond.get("waiting_since"),
                "tasks_completed": completed,
                "tasks_total": len(cfg.task_order),
                "scores": {t: r.get("score_total") for t, r in results.items()},
                "first_attempt_pass": {t: r.get("first_attempt_passed") for t, r in results.items()},
                "retries": sum(int(r.get("retry_count") or 0) for r in results.values()),
                "execution_errors": sum(int(r.get("execution_errors") or 0) for r in results.values()),
                "skills_created": sum(len(r.get("skills_created") or []) for r in results.values()),
                "skills_retrieved": sum(len(r.get("skills_retrieved") or []) for r in results.values()),
                "operator_steps_used": cond["operator_steps_used"],
                "operator_steps_cap": cfg.max_operator_steps_per_condition,
                "median_seconds_per_task": round(median, 1) if median is not None else None,
                "eta_minutes": eta_minutes,
                "eta_label": f"rough ETA ≈ {eta_minutes} min" if eta_minutes is not None else ETA_UNAVAILABLE,
            }
        existing = read_json(self.paths.status_path, default=None) or {"runs": {}}
        existing.setdefault("runs", {})[self.run_id] = {
            "mode": cfg.mode,
            "provider": self.run["provider"],
            "freeze_sha256": cfg.freeze_sha256,
            "created_at": self.run.get("created_at"),
            "conditions": conditions,
        }
        existing["updated_at"] = utc_now()
        return existing

    def write_status(self) -> Path:
        snapshot = self.status_snapshot()
        writer = getattr(getattr(self, "_services", None), "logger", None)
        if writer is not None and hasattr(writer, "write_experiment_status"):
            writer.write_experiment_status(snapshot)
        else:
            atomic_write_json(self.paths.status_path, snapshot)
        if self.paths.render_dashboard:
            try:
                from src import dashboard

                dashboard.render()
            except Exception:  # noqa: BLE001 - the dashboard is best-effort
                pass
        return self.paths.status_path


# --------------------------------------------------------------------------- CLI


def _print_status(runner: Runner) -> None:
    snap = runner.status_snapshot()["runs"][runner.run_id]
    print(f"run {runner.run_id} | mode {snap['mode']} | freeze {snap['freeze_sha256'][:12]}")
    for name, c in snap["conditions"].items():
        scores = ", ".join(f"{t}:{s:.2f}" if isinstance(s, (int, float)) else f"{t}:-" for t, s in c["scores"].items()) or "-"
        print(
            f"  {name:<16} {c['status']:<16} tasks {c['tasks_completed']}/{c['tasks_total']} | steps {c['operator_steps_used']}/{c['operator_steps_cap']}"
            f" | retries {c['retries']} | {c['eta_label']}"
        )
        print(f"  {'':<16} scores: {scores}")
        if c["pending_request"]:
            print(f"  {'':<16} waiting on operator: {c['pending_request']} (since {c['waiting_since']})")


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    p = argparse.ArgumentParser(prog="run_experiment", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    sp = sub.add_parser("init")
    sp.add_argument("--run-id", required=True)
    sp.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS), help=f"subset of {CONDITIONS}")
    sp.add_argument("--mode", default="manual", choices=["manual", "stub", "rule_learner"])
    sp.add_argument("--allow-unfrozen", action="store_true", help="skip the freeze check (never for reported runs)")
    for name in ("advance", "resume"):
        sp = sub.add_parser(name)
        sp.add_argument("--run-id", required=True)
        sp.add_argument("--condition", required=True)
        if name == "resume":
            sp.add_argument("--response", required=True)
        else:
            sp.add_argument("--max-tasks", type=int, default=None)
    for name in ("status", "pending", "advance-all"):
        sub.add_parser(name).add_argument("--run-id", required=True)
    for name in ("run-stub", "run-auto"):
        sp = sub.add_parser(name, help="run every condition to completion without interrupts (stub fixtures or the rule learner)")
        sp.add_argument("--run-id", required=True)
        sp.add_argument("--conditions", default=",".join(DEFAULT_CONDITIONS), help=f"subset of {CONDITIONS}")
        if name == "run-auto":
            sp.add_argument("--mode", default="rule_learner", choices=["stub", "rule_learner"])
    args = p.parse_args(argv)

    if args.cmd == "freeze":
        manifest = build_freeze_manifest(write=True)
        print(f"frozen {len(manifest['files'])} files -> {rel(FREEZE_MANIFEST_PATH)} | freeze_sha256 {manifest['freeze_sha256']}")
        return 0
    if args.cmd == "init":
        conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
        runner = Runner.init(args.run_id, conditions, args.mode, require_freeze=False if args.allow_unfrozen else None)
        print(f"initialised run {args.run_id} ({args.mode}) with conditions {conditions}")
        _print_status(runner)
        return 0
    if args.cmd in ("run-stub", "run-auto"):
        conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
        mode = "stub" if args.cmd == "run-stub" else args.mode
        runner = Runner.init(args.run_id, conditions, mode)
        for c in conditions:
            summary = runner.advance(c)
            print(f"{c}: {summary['status']}")
        _print_status(runner)
        return 0
    runner = Runner(args.run_id)
    if args.cmd == "advance-all":
        summaries = runner.advance_all()
        print(json.dumps(summaries, indent=1))
        pending = {c: s["pending_request"] for c, s in summaries.items() if s.get("pending_request")}
        for c, path in pending.items():
            print(f"\nOPERATOR NEEDED [{c}] -> {path}")
        if not pending:
            print("\nno operator requests pending")
        return 0
    if args.cmd == "advance":
        summary = runner.advance(args.condition, max_tasks=args.max_tasks)
    elif args.cmd == "resume":
        summary = runner.resume(args.condition, args.response)
    elif args.cmd == "pending":
        print(json.dumps(runner.pending(), indent=1))
        return 0
    else:
        _print_status(runner)
        return 0
    print(json.dumps(summary, indent=1))
    if summary.get("pending_request"):
        print(f"\nOPERATOR NEEDED -> {summary['pending_request']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
