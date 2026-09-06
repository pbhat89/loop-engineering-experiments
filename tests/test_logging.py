"""Logging tests (A5): round-trip of every record type the real graph produces, ``validate_logs`` diagnostics with
``file:line``, secret-key refusal, ``summarize_runs`` folding, and the atomic status snapshot.

``build_realistic_logs`` is shared with ``tests/test_dashboard.py`` and the chart verification: it runs the real
LangGraph graph with the route-test fakes (stub provider, fake store / executor / evaluator) for all four
conditions and writes the logs through ``ExperimentLogger``. All data is synthetic.
"""
from __future__ import annotations

import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.claims_graph import build_claims_skill_graph
from src.experiment_logger import (
    EXPERIMENT_EVENTS_FILE,
    FEEDBACK_EVENTS_FILE,
    GRAPH_EVENT_TYPES,
    GRAPH_EVENTS_FILE,
    LOG_FILES,
    SKILL_EVENT_NAMES,
    SKILL_EVENTS_FILE,
    STATUS_FILE,
    ExperimentLogger,
    LogValidationError,
    looks_like_secret_key,
    read_log,
    read_status,
    summarize_runs,
    validate_logs,
)
from src.utils import rel
from tests.test_graph_routes import FakeStore, make_services, make_state, stub

RUN_ID = "run_001"
CONDITIONS = ("baseline", "reflection_only", "skill_learning", "foundational_only")
# (task_id, task_index, remaining task ids) - three tasks so every learning curve has >= 2 points.
TASKS = (("T2", 1, ("T3", "T4")), ("T3", 2, ("T4",)), ("T4", 3, ()))
TASKS_TOTAL = len(TASKS)
# The synthetic status snapshot shows this condition waiting on an operator step for its third task,
# so the dashboard's pending-request branch is exercised; its logs therefore stop after two tasks.
WAITING_CONDITION = "reflection_only"
PENDING_REQUEST = f"artifacts/manual/{RUN_ID}/{WAITING_CONDITION}/T4_a2_revise_plan_1.request.json"
WAITING_FOR = timedelta(minutes=7, seconds=30)
FOUNDATIONAL_SKILL = {
    "skill_id": "foundational_003",
    "name": "descriptive_summary",
    "kind": "foundational",
    "version": 1,
    "tags": ["rates"],
    "sections": {"required_checks": ["denial_rate.denominator=adjudicated_claims and state it"]},
    "created_after_task_index": -1,
    "path": "skills/foundational/03_descriptive_summary.md",
}


class RecordingLogger(ExperimentLogger):
    """ExperimentLogger that also keeps every accepted record in memory, for round-trip assertions."""

    def __init__(self, logs_dir: Path):
        super().__init__(logs_dir)
        self.written: dict[str, list[dict]] = {name: [] for name in LOG_FILES}

    def _write(self, log_name: str, record: dict) -> dict:
        prepared = super()._write(log_name, record)
        self.written[log_name].append(prepared)
        return prepared


def build_status_snapshot(logs_dir: Path, run_id: str = RUN_ID, now: datetime | None = None) -> dict:
    """LEAD §10-shaped snapshot computed from the logs just written, plus the synthetic waiting_operator overlay."""
    now = now or datetime.now(timezone.utc)
    run = summarize_runs(logs_dir)["runs"][run_id]
    conditions: dict[str, dict] = {}
    for condition in CONDITIONS:
        cond = run["conditions"].get(condition) or {"tasks": {}}
        finals = {t: e["final"] for t, e in cond["tasks"].items() if e.get("final")}
        completed = len(finals)
        entry = {
            "status": "done" if completed >= TASKS_TOTAL else "running",
            "current_task": None if completed >= TASKS_TOTAL else TASKS[completed][0],
            "attempt": None,
            "current_node": None,
            "pending_request": None,
            "waiting_since": None,
            "tasks_completed": completed,
            "tasks_total": TASKS_TOTAL,
            "scores": {t: f.get("evaluator_score_total") for t, f in finals.items()},
            "first_attempt_pass": {t: f.get("first_attempt_passed") for t, f in finals.items()},
            "retries": sum(int(f.get("retry_count") or 0) for f in finals.values()),
            "execution_errors": sum(int(f.get("execution_errors") or 0) for f in finals.values()),
            "skills_created": sum(len(f.get("skills_created") or []) for f in finals.values()),
            "skills_retrieved": sum(len(f.get("skills_retrieved") or []) for f in finals.values()),
            "operator_steps_used": sum(int(f.get("operator_steps_used") or 0) for f in finals.values()),
            "operator_steps_cap": 40,
            "median_seconds_per_task": None,
            "eta_minutes": None,
            "eta_label": "ETA unavailable — insufficient completed tasks",
        }
        if condition == WAITING_CONDITION:
            entry.update(
                {
                    "status": "waiting_operator",
                    "current_task": "T4",
                    "attempt": 2,
                    "current_node": "revise_plan",
                    "pending_request": PENDING_REQUEST,
                    "waiting_since": (now - WAITING_FOR).isoformat(timespec="seconds"),
                }
            )
        conditions[condition] = entry
    return {
        "updated_at": now.isoformat(timespec="seconds"),
        "runs": {
            run_id: {
                "mode": "stub",
                # same shape as src.run_experiment.Runner.status_snapshot writes
                "provider": {"provider_mode": "stub", "operator": "deterministic-fixture", "model_identifier": "deterministic-fixture-v1"},
                "freeze_sha256": "test-freeze",
                "created_at": (now - timedelta(minutes=20)).isoformat(timespec="seconds"),
                "conditions": conditions,
            }
        },
    }


def build_realistic_logs(logs_dir: Path, run_id: str = RUN_ID) -> dict:
    """Run the real graph for all four conditions with the route-test fakes, logging through ExperimentLogger.

    Returns ``{"logger": RecordingLogger, "outputs": {(condition, task_id): final_state}, "status": snapshot}``.
    """
    logs_dir = Path(logs_dir)
    logger = RecordingLogger(logs_dir)
    outputs: dict[tuple[str, str], dict] = {}
    for condition in CONDITIONS:
        store = FakeStore()
        if condition == "foundational_only":
            store.skills.append(copy.deepcopy(FOUNDATIONAL_SKILL))
        graph = build_claims_skill_graph(make_services(stub(), store, logger))
        tasks = TASKS[:2] if condition == WAITING_CONDITION else TASKS
        for task_id, task_index, remaining in tasks:
            state = make_state(
                condition,
                task_id=task_id,
                task_index=task_index,
                remaining=remaining,
                run_id=run_id,
                output_dir=f"artifacts/tasks/{run_id}/{condition}/{task_id}",
            )
            outputs[(condition, task_id)] = graph.invoke(state)
    status = build_status_snapshot(logs_dir, run_id)
    logger.write_experiment_status(status)
    return {"logger": logger, "outputs": outputs, "status": status}


@pytest.fixture(scope="module")
def realistic(tmp_path_factory) -> dict:
    logs_dir = tmp_path_factory.mktemp("logs")
    built = build_realistic_logs(logs_dir)
    built["logs_dir"] = logs_dir
    return built


def _json_roundtrip(record: dict) -> dict:
    return json.loads(json.dumps(record, ensure_ascii=False, default=str))


# --------------------------------------------------------------------------- round trip of the graph's own records


def test_every_graph_record_round_trips_through_the_logger(realistic):
    logger: RecordingLogger = realistic["logger"]
    logs_dir: Path = realistic["logs_dir"]
    for name in LOG_FILES:
        written = logger.written[name]
        assert written, f"the graph wrote nothing to {name}"
        on_disk = read_log(logs_dir / name)
        assert on_disk == [_json_roundtrip(r) for r in written], f"{name}: disk content differs from what was accepted"
        assert all(r.get("timestamp") for r in on_disk)
        assert all(r.get("provider_mode") == "stub" and r.get("model_identifier") and r.get("operator") for r in on_disk)
    assert validate_logs(logs_dir) == []

    experiment = logger.written[EXPERIMENT_EVENTS_FILE]
    assert {r["condition"] for r in experiment} == set(CONDITIONS)
    for (condition, task_id), out in realistic["outputs"].items():
        statuses = [r["status"] for r in experiment if r["condition"] == condition and r["task_id"] == task_id]
        assert statuses == ["attempt"] * out["execution_attempts"] + ["done"]
    graph_events = logger.written[GRAPH_EVENTS_FILE]
    assert {r["event_type"] for r in graph_events} <= set(GRAPH_EVENT_TYPES)
    assert {r["destination_node"] for r in graph_events} >= {"load_context", "plan_task", "execute_task", "evaluate_output", "finalize_task"}
    skill_events = logger.written[SKILL_EVENTS_FILE]
    assert {r["event"] for r in skill_events} <= set(SKILL_EVENT_NAMES)
    assert {r["condition"] for r in skill_events} == {"skill_learning", "foundational_only"}
    assert [r["event"] for r in skill_events if r["condition"] == "skill_learning" and r["task_id"] == "T2"] == ["skill_proposed", "skill_validated", "skill_persisted"]
    feedback = logger.written[FEEDBACK_EVENTS_FILE]
    assert {r["event"] for r in feedback} >= {"feedback_issued", "feedback_incorporated"}
    issued = next(r for r in feedback if r["event"] == "feedback_issued")
    assert issued["criterion"] == "correctness" and issued["reusable"] is True and issued["incorporated"] is False


def test_logger_fills_timestamp_and_keeps_extra_fields(tmp_path):
    logger = ExperimentLogger(tmp_path)
    accepted = logger.log_skill_event({"run_id": "r", "condition": "skill_learning", "task_id": "T1", "event": "skill_retrieved", "skill_id": "foundational_001", "kind": "foundational", "score": 0.7})
    assert accepted["timestamp"]
    [on_disk] = logger.read_skill_events()
    assert on_disk["kind"] == "foundational" and on_disk["score"] == 0.7 and on_disk["timestamp"] == accepted["timestamp"]


# --------------------------------------------------------------------------- validation


def test_validate_logs_reports_broken_json_and_missing_fields_with_file_line(tmp_path):
    logger = ExperimentLogger(tmp_path)
    base = {"run_id": "r", "condition": "baseline", "task_id": "T1", "attempt": 1, "provider_mode": "stub", "model_identifier": "m", "operator": "o"}
    logger.log_experiment_event({**base, "status": "attempt"})
    logger.log_graph_event({**base, "event_type": "node_transition", "source_node": "START", "destination_node": "load_context", "route_reason": "", "retry_count": 0, "status": "running"})
    assert validate_logs(tmp_path) == []

    experiment_path = tmp_path / EXPERIMENT_EVENTS_FILE
    graph_path = tmp_path / GRAPH_EVENTS_FILE
    with open(experiment_path, "a", encoding="utf-8") as fh:
        fh.write('{"run_id": "r", "condition": "baseline", "task_id": "T1", "status": "attempt"\n')  # broken JSON (line 2)
    with open(graph_path, "a", encoding="utf-8") as fh:
        broken = {**base, "timestamp": "2026-09-06T00:00:00+00:00", "event_type": "node_transition", "destination_node": "plan_task", "route_reason": "", "retry_count": 0, "status": "running"}
        fh.write(json.dumps(broken) + "\n")  # missing source_node (line 2)
        fh.write(json.dumps({**broken, "source_node": "x", "event_type": "teleport"}) + "\n")  # unknown event_type (line 3)

    problems = validate_logs(tmp_path)
    assert any(p.startswith(f"{rel(experiment_path)}:2:") and "invalid JSON" in p for p in problems), problems
    assert any(p.startswith(f"{rel(graph_path)}:2:") and "missing required field 'source_node'" in p for p in problems), problems
    assert any(p.startswith(f"{rel(graph_path)}:3:") and "event_type" in p and "teleport" in p for p in problems), problems
    assert len(problems) == 3
    # readers skip the broken line instead of blanking everything; summarize_runs still sees the valid record
    assert len(read_log(experiment_path)) == 1
    assert summarize_runs(tmp_path)["runs"]["r"]["conditions"]["baseline"]["tasks"]["T1"]["attempts"][0]["attempt"] == 1


def test_validate_logs_reports_status_snapshot_problems(tmp_path):
    (tmp_path / STATUS_FILE).write_text('{"updated_at": "x", "runs": []}', encoding="utf-8")
    problems = validate_logs(tmp_path)
    assert any(p.startswith(f"{rel(tmp_path / STATUS_FILE)}:1:") and "'runs'" in p for p in problems), problems
    (tmp_path / STATUS_FILE).write_text("{not json", encoding="utf-8")
    assert any("invalid JSON" in p for p in validate_logs(tmp_path))


def test_logger_refuses_missing_required_fields_and_unknown_names(tmp_path):
    logger = ExperimentLogger(tmp_path)
    with pytest.raises(LogValidationError, match="missing required field 'task_id'"):
        logger.log_experiment_event({"run_id": "r", "condition": "baseline", "attempt": 1, "provider_mode": "stub", "model_identifier": "m", "status": "attempt"})
    with pytest.raises(LogValidationError, match="event"):
        logger.log_skill_event({"run_id": "r", "condition": "skill_learning", "task_id": "T1", "event": "skill_teleported"})
    with pytest.raises(LogValidationError, match="unknown experiment status"):
        logger.log_experiment_event({"run_id": "r", "condition": "baseline", "task_id": "T1", "attempt": 1, "provider_mode": "stub", "model_identifier": "m", "status": "maybe"})
    with pytest.raises(LogValidationError):
        logger.log_graph_event(["not", "a", "dict"])  # type: ignore[arg-type]
    assert not (tmp_path / EXPERIMENT_EVENTS_FILE).exists() and not (tmp_path / SKILL_EVENTS_FILE).exists()


def test_logger_refuses_secret_looking_keys_anywhere(tmp_path):
    logger = ExperimentLogger(tmp_path)
    valid = {"run_id": "r", "condition": "baseline", "task_id": "T1", "event_type": "node_transition", "source_node": "START", "destination_node": "load_context", "route_reason": "", "retry_count": 0, "status": "running"}
    for poison in ({"api_key": "sk-x"}, {"payload": {"Authorization": "Bearer x"}}, {"settings": [{"anthropic_api_key": "x"}]}, {"refresh_token": "x"}, {"password": "x"}):
        with pytest.raises(LogValidationError, match="secret-looking key"):
            logger.log_graph_event({**valid, **poison})
    assert not (tmp_path / GRAPH_EVENTS_FILE).exists()
    with pytest.raises(LogValidationError, match="secret-looking key"):
        logger.write_experiment_status({"runs": {}, "token": "x"})
    assert not (tmp_path / STATUS_FILE).exists()
    # ordinary telemetry names are not secrets
    assert not any(looks_like_secret_key(k) for k in ("model_identifier", "tokens_used", "operator", "freeze_sha256", "input_hash"))
    assert all(looks_like_secret_key(k) for k in ("API_KEY", "apiKey", "client_secret", "x_token", "credentials"))


# --------------------------------------------------------------------------- summaries


def test_summarize_runs_returns_final_done_record_and_attempt_list(realistic):
    summary = summarize_runs(realistic["logs_dir"])
    assert summary["run_ids"] == [RUN_ID]
    assert summary["conditions"] == sorted(CONDITIONS)
    assert summary["task_ids"] == ["T2", "T3", "T4"]
    assert summary["skipped_records"] == 0
    run = summary["runs"][RUN_ID]
    assert run["provider_modes"] == ["stub"] and run["model_identifiers"] == ["deterministic-fixture-v1"]
    for (condition, task_id), out in realistic["outputs"].items():
        task = run["conditions"][condition]["tasks"][task_id]
        assert task["final"]["status"] == "done"
        assert task["final"]["execution_attempts"] == out["execution_attempts"]
        assert task["final"]["evaluator_score_total"] == out["evaluation"]["score_total"]
        assert [a["attempt"] for a in task["attempts"]] == list(range(1, out["execution_attempts"] + 1))
        assert all(a["status"] == "attempt" for a in task["attempts"])
    baseline = run["conditions"]["baseline"]
    assert baseline["task_ids"] == ["T2", "T3", "T4"] and baseline["tasks_done"] == 3
    assert baseline["retries"] == sum(o["retry_count"] for (c, _), o in realistic["outputs"].items() if c == "baseline")
    assert baseline["skills_created"] == [] and baseline["mean_score"] is not None
    assert run["conditions"][WAITING_CONDITION]["tasks_done"] == 2
    learning = run["conditions"]["skill_learning"]
    assert learning["skills_created"] == ["evolved_test_001"] and learning["skills_reused"] == ["evolved_test_001"]
    assert learning["first_attempt_passes"] >= 1
    assert run["conditions"]["foundational_only"]["skills_reused"] == ["foundational_003"]


def test_summarize_runs_keeps_the_last_done_record_per_task(realistic, tmp_path):
    final = copy.deepcopy(summarize_runs(realistic["logs_dir"])["runs"][RUN_ID]["conditions"]["baseline"]["tasks"]["T2"]["final"])
    logger = ExperimentLogger(tmp_path)
    logger.log_experiment_event({**final, "evaluator_score_total": 1.25, "timestamp": "2026-01-01T00:00:00+00:00"})
    logger.log_experiment_event({**final, "evaluator_score_total": 3.75, "timestamp": "2026-01-01T00:05:00+00:00"})
    task = summarize_runs(tmp_path)["runs"][RUN_ID]["conditions"]["baseline"]["tasks"]["T2"]
    assert task["final"]["evaluator_score_total"] == 3.75 and task["attempts"] == []


def test_summarize_runs_on_empty_directory(tmp_path):
    summary = summarize_runs(tmp_path)
    assert summary["runs"] == {} and summary["run_ids"] == [] and summary["task_ids"] == []
    assert read_status(tmp_path) == {"updated_at": None, "runs": {}}


# --------------------------------------------------------------------------- status snapshot


def test_write_experiment_status_is_atomic_and_fills_updated_at(tmp_path):
    logger = ExperimentLogger(tmp_path)
    path = logger.write_experiment_status({"runs": {"run_x": {"mode": "stub", "conditions": {}}}})
    assert path == tmp_path / STATUS_FILE
    first = json.loads(path.read_text(encoding="utf-8"))
    assert first["updated_at"] and first["runs"]["run_x"]["mode"] == "stub"
    assert [p.name for p in tmp_path.iterdir()] == [STATUS_FILE], "temp file must be replaced, not left behind"

    logger.write_experiment_status({"updated_at": "2026-09-06T00:00:00+00:00", "runs": {"run_y": {"conditions": {}}}})
    second = read_status(tmp_path)
    assert second["updated_at"] == "2026-09-06T00:00:00+00:00" and list(second["runs"]) == ["run_y"]
    # a refused snapshot leaves the previous file untouched
    with pytest.raises(LogValidationError):
        logger.write_experiment_status({"runs": {}, "api_key": "x"})
    assert read_status(tmp_path) == second
    assert [p.name for p in tmp_path.iterdir()] == [STATUS_FILE]
    assert validate_logs(tmp_path) == []


def test_realistic_status_snapshot_matches_lead_shape(realistic):
    status = read_status(realistic["logs_dir"])
    run = status["runs"][RUN_ID]
    assert run["mode"] == "stub" and set(run["conditions"]) == set(CONDITIONS)
    waiting = run["conditions"][WAITING_CONDITION]
    assert waiting["status"] == "waiting_operator" and waiting["pending_request"] == PENDING_REQUEST and waiting["waiting_since"]
    for name, cond in run["conditions"].items():
        for key in ("status", "current_task", "attempt", "current_node", "pending_request", "waiting_since", "tasks_completed", "tasks_total", "scores", "first_attempt_pass", "retries", "execution_errors", "skills_created", "skills_retrieved", "operator_steps_used", "operator_steps_cap", "median_seconds_per_task", "eta_minutes", "eta_label"):
            assert key in cond, f"{name} misses {key}"
        assert cond["tasks_completed"] == len(cond["scores"]) == len(cond["first_attempt_pass"])
