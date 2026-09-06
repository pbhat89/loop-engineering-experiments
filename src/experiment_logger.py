"""Structured experiment logging for the claims skill loop (A5).

Four append-only JSONL logs plus the atomic ``experiment_status.json`` snapshot::

    logs/experiment_events.jsonl   one record per task attempt (status "attempt") and one final record per task (status "done")
    logs/graph_events.jsonl        node transitions and operator request / response / validation-error events
    logs/skill_events.jsonl        skill retrieval, proposal, validation, persistence, reuse and archive events
    logs/feedback_events.jsonl     evaluator feedback issued and later incorporated
    logs/experiment_status.json    per run / condition live snapshot written by the runner (LEAD §10 shape)

Every ``log_*`` writer validates the required fields with a Pydantic model that
ignores extra fields (the graph attaches many), fills ``timestamp`` when it is
missing, refuses records that contain keys that look like secrets, and appends
one JSON line via :func:`src.utils.append_jsonl`. The original record (not the
model's projection) is written, so extra fields survive.

:func:`validate_logs` re-checks every line on disk and returns human-readable
``file:line: problem`` strings; :func:`summarize_runs` folds the experiment log
into per run / condition / task final + attempt records for the dashboard and
charts. Nothing here reads environment variables or the network.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from src.utils import LOGS_DIR, append_jsonl, atomic_write_json, read_json, rel, utc_now

# --------------------------------------------------------------------------- names

EXPERIMENT_EVENTS_FILE = "experiment_events.jsonl"
GRAPH_EVENTS_FILE = "graph_events.jsonl"
SKILL_EVENTS_FILE = "skill_events.jsonl"
FEEDBACK_EVENTS_FILE = "feedback_events.jsonl"
STATUS_FILE = "experiment_status.json"
LOG_FILES: tuple[str, ...] = (EXPERIMENT_EVENTS_FILE, GRAPH_EVENTS_FILE, SKILL_EVENTS_FILE, FEEDBACK_EVENTS_FILE)

GRAPH_EVENT_TYPES: tuple[str, ...] = ("node_transition", "operator_request", "operator_response", "operator_validation_error")
SKILL_EVENT_NAMES: tuple[str, ...] = (
    "skill_retrieved",
    "skill_proposed",
    "skill_proposal_skipped",
    "skill_validated",
    "skill_rejected",
    "skill_revision_requested",
    "skill_persisted",
    "skill_reused",
    "skill_archived",
)
FEEDBACK_EVENT_NAMES: tuple[str, ...] = ("feedback_issued", "feedback_incorporated", "feedback_update", "feedback_resolved")
EXPERIMENT_STATUSES: tuple[str, ...] = ("attempt", "done")
FINAL_STATUS = "done"

# Keys that must never appear in a log record, at any nesting depth (matched on the key name only).
_SECRET_EXACT = {"api_key", "apikey", "token", "authorization", "secret", "password", "passwd", "bearer", "credentials"}
_SECRET_SUBSTRINGS = ("api_key", "apikey", "secret", "password", "authorization")
_SECRET_SUFFIXES = ("_token",)

_TASK_ID_RE = re.compile(r"^T(\d+)$")


class LogValidationError(ValueError):
    """A record was refused: missing required field, unknown event name, or a secret-looking key."""


# --------------------------------------------------------------------------- models (extra fields ignored)


class _Event(BaseModel):
    model_config = ConfigDict(extra="ignore")

    run_id: str
    condition: str
    task_id: str
    timestamp: str


class ExperimentAttemptRecord(_Event):
    """Per-attempt experiment record written by ``evaluate_output`` (``status == "attempt"``)."""

    attempt: int
    provider_mode: str
    model_identifier: str
    status: str


class ExperimentFinalRecord(ExperimentAttemptRecord):
    """Final per-task record written by ``finalize_task`` (``status == "done"``)."""

    input_hash: str
    files_used: list
    skills_retrieved: list
    skills_created: list
    skills_reused: list
    graph_route: list
    execution_attempts: int
    execution_errors: int
    evaluator_score_total: float | None
    evaluator_score_by_dimension: dict | None
    artifact_paths: list


class GraphEventRecord(_Event):
    event_type: Literal["node_transition", "operator_request", "operator_response", "operator_validation_error"]
    source_node: str
    destination_node: str
    route_reason: str
    retry_count: int
    status: str


class SkillEventRecord(_Event):
    event: Literal[
        "skill_retrieved",
        "skill_proposed",
        "skill_proposal_skipped",
        "skill_validated",
        "skill_rejected",
        "skill_revision_requested",
        "skill_persisted",
        "skill_reused",
        "skill_archived",
    ]


class FeedbackEventRecord(_Event):
    event: Literal["feedback_issued", "feedback_incorporated", "feedback_update", "feedback_resolved"]
    feedback_id: str
    incorporated: bool | None


class FeedbackIssuedRecord(FeedbackEventRecord):
    """``feedback_issued`` also carries the evaluator's feedback item (LEAD §7)."""

    criterion: str
    issue_type: str
    severity: str
    remediation: str
    related_components: list
    reusable: bool
    applicable_task_ids: list


def model_for(log_name: str, record: dict) -> type[BaseModel]:
    """Pick the validation model for a record of ``log_name`` (some logs branch on status / event)."""
    if log_name == EXPERIMENT_EVENTS_FILE:
        return ExperimentFinalRecord if record.get("status") == FINAL_STATUS else ExperimentAttemptRecord
    if log_name == GRAPH_EVENTS_FILE:
        return GraphEventRecord
    if log_name == SKILL_EVENTS_FILE:
        return SkillEventRecord
    if log_name == FEEDBACK_EVENTS_FILE:
        return FeedbackIssuedRecord if record.get("event") == "feedback_issued" else FeedbackEventRecord
    raise KeyError(f"unknown log {log_name!r}; expected one of {LOG_FILES}")


# --------------------------------------------------------------------------- validation helpers


def looks_like_secret_key(key: str) -> bool:
    k = str(key).lower()
    return k in _SECRET_EXACT or any(s in k for s in _SECRET_SUBSTRINGS) or k.endswith(_SECRET_SUFFIXES)


def find_secret_keys(value: Any, path: str = "") -> list[str]:
    """Dotted paths of every secret-looking key in a nested dict / list structure."""
    found: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            here = f"{path}.{k}" if path else str(k)
            if looks_like_secret_key(k):
                found.append(here)
            found.extend(find_secret_keys(v, here))
    elif isinstance(value, (list, tuple)):
        for i, v in enumerate(value):
            found.extend(find_secret_keys(v, f"{path}[{i}]"))
    return found


def _format_validation_error(exc: ValidationError) -> list[str]:
    problems: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", ())) or "<record>"
        if err.get("type") == "missing":
            problems.append(f"missing required field '{loc}'")
        elif err.get("type", "").startswith("literal"):
            problems.append(f"unknown value for '{loc}': {err.get('input')!r} ({err.get('msg')})")
        else:
            problems.append(f"field '{loc}': {err.get('msg')} (got {err.get('input')!r})")
    return problems


def record_problems(log_name: str, record: Any) -> list[str]:
    """All problems with one parsed record; empty when the record is acceptable for ``log_name``."""
    if not isinstance(record, dict):
        return [f"record is {type(record).__name__}, expected a JSON object"]
    problems: list[str] = []
    secrets = find_secret_keys(record)
    if secrets:
        problems.append("secret-looking key(s) refused: " + ", ".join(secrets))
    try:
        model_for(log_name, record).model_validate(record)
    except ValidationError as exc:
        problems.extend(_format_validation_error(exc))
    if log_name == EXPERIMENT_EVENTS_FILE and record.get("status") not in EXPERIMENT_STATUSES:
        problems.append(f"unknown experiment status {record.get('status')!r} (expected one of {list(EXPERIMENT_STATUSES)})")
    return problems


# --------------------------------------------------------------------------- logger


class ExperimentLogger:
    """Typed writers and readers for the four JSONL logs and the status snapshot under ``logs_dir``."""

    def __init__(self, logs_dir: Path | str = LOGS_DIR):
        self.logs_dir = Path(logs_dir)

    # ---- paths ------------------------------------------------------------------------
    def path(self, log_name: str) -> Path:
        return self.logs_dir / log_name

    @property
    def experiment_events_path(self) -> Path:
        return self.path(EXPERIMENT_EVENTS_FILE)

    @property
    def graph_events_path(self) -> Path:
        return self.path(GRAPH_EVENTS_FILE)

    @property
    def skill_events_path(self) -> Path:
        return self.path(SKILL_EVENTS_FILE)

    @property
    def feedback_events_path(self) -> Path:
        return self.path(FEEDBACK_EVENTS_FILE)

    @property
    def status_path(self) -> Path:
        return self.path(STATUS_FILE)

    # ---- writers ------------------------------------------------------------------------
    def _write(self, log_name: str, record: dict) -> dict:
        if not isinstance(record, dict):
            raise LogValidationError(f"{log_name}: record must be a dict, got {type(record).__name__}")
        prepared = dict(record)
        if not prepared.get("timestamp"):
            prepared["timestamp"] = utc_now()
        problems = record_problems(log_name, prepared)
        if problems:
            raise LogValidationError(f"{log_name}: refused record: " + "; ".join(problems))
        append_jsonl(self.path(log_name), prepared)
        return prepared

    def log_experiment_event(self, record: dict) -> dict:
        return self._write(EXPERIMENT_EVENTS_FILE, record)

    def log_graph_event(self, record: dict) -> dict:
        return self._write(GRAPH_EVENTS_FILE, record)

    def log_skill_event(self, record: dict) -> dict:
        return self._write(SKILL_EVENTS_FILE, record)

    def log_feedback_event(self, record: dict) -> dict:
        return self._write(FEEDBACK_EVENTS_FILE, record)

    def write_experiment_status(self, snapshot: dict) -> Path:
        """Atomically write ``logs/experiment_status.json`` (temp file + ``os.replace``)."""
        if not isinstance(snapshot, dict):
            raise LogValidationError(f"{STATUS_FILE}: snapshot must be a dict, got {type(snapshot).__name__}")
        secrets = find_secret_keys(snapshot)
        if secrets:
            raise LogValidationError(f"{STATUS_FILE}: secret-looking key(s) refused: {', '.join(secrets)}")
        prepared = dict(snapshot)
        prepared.setdefault("runs", {})
        prepared["updated_at"] = prepared.get("updated_at") or utc_now()
        return atomic_write_json(self.status_path, prepared)

    # ---- readers ------------------------------------------------------------------------
    def read_experiment_events(self) -> list[dict]:
        return read_log(self.experiment_events_path)

    def read_graph_events(self) -> list[dict]:
        return read_log(self.graph_events_path)

    def read_skill_events(self) -> list[dict]:
        return read_log(self.skill_events_path)

    def read_feedback_events(self) -> list[dict]:
        return read_log(self.feedback_events_path)

    def read_status(self) -> dict:
        return read_status(self.logs_dir)


# --------------------------------------------------------------------------- module-level readers


def iter_log_lines(path: Path | str) -> Iterable[tuple[int, str]]:
    p = Path(path)
    if not p.exists():
        return
    with open(p, "r", encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            stripped = line.strip()
            if stripped:
                yield lineno, stripped


def read_log(path: Path | str, *, skip_invalid: bool = True) -> list[dict]:
    """Parsed JSON objects of one JSONL log. Invalid lines are skipped (validate_logs reports them) unless ``skip_invalid`` is False."""
    records: list[dict] = []
    for lineno, line in iter_log_lines(path):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            if skip_invalid:
                continue
            raise ValueError(f"{rel(path)}:{lineno}: invalid JSON line ({exc.msg})") from exc
        if isinstance(obj, dict):
            records.append(obj)
    return records


def read_status(logs_dir: Path | str = LOGS_DIR) -> dict:
    data = read_json(Path(logs_dir) / STATUS_FILE, default=None)
    if not isinstance(data, dict):
        return {"updated_at": None, "runs": {}}
    data.setdefault("runs", {})
    data.setdefault("updated_at", None)
    return data


# --------------------------------------------------------------------------- validation of files on disk


def validate_logs(logs_dir: Path | str = LOGS_DIR) -> list[str]:
    """Human-readable problems (``file:line: problem``) across the four JSONL logs and the status snapshot; empty = valid."""
    logs_dir = Path(logs_dir)
    problems: list[str] = []
    for log_name in LOG_FILES:
        path = logs_dir / log_name
        label = rel(path)
        for lineno, line in iter_log_lines(path):
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                problems.append(f"{label}:{lineno}: invalid JSON ({exc.msg} at column {exc.colno})")
                continue
            for problem in record_problems(log_name, record):
                problems.append(f"{label}:{lineno}: {problem}")
    status_path = logs_dir / STATUS_FILE
    if status_path.exists():
        label = rel(status_path)
        try:
            with open(status_path, "r", encoding="utf-8") as fh:
                snapshot = json.load(fh)
        except json.JSONDecodeError as exc:
            problems.append(f"{label}:{exc.lineno}: invalid JSON ({exc.msg})")
        else:
            if not isinstance(snapshot, dict):
                problems.append(f"{label}:1: snapshot is {type(snapshot).__name__}, expected a JSON object")
            else:
                if not isinstance(snapshot.get("runs"), dict):
                    problems.append(f"{label}:1: missing required field 'runs' (object)")
                if not snapshot.get("updated_at"):
                    problems.append(f"{label}:1: missing required field 'updated_at'")
                for secret in find_secret_keys(snapshot):
                    problems.append(f"{label}:1: secret-looking key refused: {secret}")
    return problems


# --------------------------------------------------------------------------- summaries for dashboard and charts


def task_sort_key(task_id: Any) -> tuple[int, int | str]:
    """Natural order for task ids: T1 < T2 < ... < T10, then anything else alphabetically."""
    m = _TASK_ID_RE.match(str(task_id))
    return (0, int(m.group(1))) if m else (1, str(task_id))


def summarize_runs(logs_dir: Path | str = LOGS_DIR) -> dict:
    """Fold ``experiment_events.jsonl`` into ``{"runs": {run_id: {"conditions": {condition: {"tasks": {task_id: {...}}}}}}}``.

    Each task entry holds ``final`` (the last record with ``status == "done"`` or ``None``)
    and ``attempts`` (the ``status == "attempt"`` records in file order). Records that fail
    validation are counted in ``skipped`` rather than raised, so a damaged line never blanks
    the dashboard; ``validate_logs`` is the place that reports it.
    """
    logs_dir = Path(logs_dir)
    path = logs_dir / EXPERIMENT_EVENTS_FILE
    runs: dict[str, dict] = {}
    task_ids: set[str] = set()
    conditions: set[str] = set()
    skipped = 0
    for record in read_log(path):
        if record_problems(EXPERIMENT_EVENTS_FILE, record):
            skipped += 1
            continue
        run_id, condition, task_id = str(record["run_id"]), str(record["condition"]), str(record["task_id"])
        run = runs.setdefault(run_id, {"conditions": {}, "provider_modes": [], "model_identifiers": [], "operators": []})
        for key, field in (("provider_modes", "provider_mode"), ("model_identifiers", "model_identifier"), ("operators", "operator")):
            value = record.get(field)
            if value and value not in run[key]:
                run[key].append(value)
        cond = run["conditions"].setdefault(condition, {"tasks": {}})
        task = cond["tasks"].setdefault(task_id, {"final": None, "attempts": []})
        if record.get("status") == FINAL_STATUS:
            task["final"] = record
        else:
            task["attempts"].append(record)
        task_ids.add(task_id)
        conditions.add(condition)
    for run in runs.values():
        for cond in run["conditions"].values():
            cond["task_ids"] = sorted(cond["tasks"], key=task_sort_key)
            finals = [t["final"] for t in cond["tasks"].values() if t["final"]]
            cond["tasks_done"] = len(finals)
            cond["attempt_count"] = sum(len(t["attempts"]) for t in cond["tasks"].values())
            cond["execution_errors"] = sum(int(f.get("execution_errors") or 0) for f in finals)
            cond["retries"] = sum(int(f.get("retry_count") or max(int(f.get("execution_attempts") or 1) - 1, 0)) for f in finals)
            cond["skills_created"] = sorted({s for f in finals for s in (f.get("skills_created") or [])})
            cond["skills_reused"] = sorted({s for f in finals for s in (f.get("skills_reused") or [])})
            scores = [float(f["evaluator_score_total"]) for f in finals if isinstance(f.get("evaluator_score_total"), (int, float))]
            cond["mean_score"] = round(sum(scores) / len(scores), 3) if scores else None
            cond["first_attempt_passes"] = sum(1 for f in finals if f.get("first_attempt_passed"))
            cond["last_timestamp"] = max((str(f.get("timestamp") or "") for f in finals), default="")
    return {
        "source": rel(path),
        "runs": runs,
        "run_ids": sorted(runs),
        "conditions": sorted(conditions),
        "task_ids": sorted(task_ids, key=task_sort_key),
        "skipped_records": skipped,
    }


__all__ = [
    "EXPERIMENT_EVENTS_FILE",
    "GRAPH_EVENTS_FILE",
    "SKILL_EVENTS_FILE",
    "FEEDBACK_EVENTS_FILE",
    "STATUS_FILE",
    "LOG_FILES",
    "GRAPH_EVENT_TYPES",
    "SKILL_EVENT_NAMES",
    "FEEDBACK_EVENT_NAMES",
    "EXPERIMENT_STATUSES",
    "ExperimentLogger",
    "LogValidationError",
    "ExperimentAttemptRecord",
    "ExperimentFinalRecord",
    "GraphEventRecord",
    "SkillEventRecord",
    "FeedbackEventRecord",
    "FeedbackIssuedRecord",
    "find_secret_keys",
    "looks_like_secret_key",
    "record_problems",
    "read_log",
    "read_status",
    "validate_logs",
    "summarize_runs",
    "task_sort_key",
]
