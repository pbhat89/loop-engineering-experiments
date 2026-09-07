"""LangGraph node implementations for the claims skill loop.

Nodes are methods on :class:`ClaimsNodes` so they can share injected
:class:`Services` (provider, executor, evaluator, skill store, validator,
logger). Decision nodes (plan / revise / reflect / propose / revise proposal)
obtain their answer through ``provider.decide``; in ``manual`` mode that call
pauses the graph on an interrupt, and on resume LangGraph re-executes the node
from the top. Therefore everything *before* the provider call is pure, and all
side effects (logging, counters) happen only after the final answer is in hand.

Routing decisions are computed inside ``evaluate_output`` / ``validate_skill``
and stored in state as ``next_route`` so the conditional-edge functions in
``claims_graph.py`` stay trivial and the decision is visible in the logs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from src.graph_state import (
    MEMORY_CONDITIONS,
    SELF_REVIEW_CONDITIONS,
    SKILL_RETRIEVING_CONDITIONS,
    PlanResponse,
    ReflectionResponse,
    SelfEvaluationResponse,
    SkillProposalResponse,
)
from src.llm_provider import BaseProvider, OperatorRequest
from src.utils import REPO_ROOT, rel, sha256_text, utc_now

# --------------------------------------------------------------------------- services


@dataclass
class Services:
    """Everything the nodes need, injected so tests can use fakes and modules can land independently."""

    provider: BaseProvider
    execute_task: Callable[[dict, dict, dict], dict]  # task_runner.execute(task_spec, plan, run_context)
    evaluate: Callable[[dict, dict, dict, dict], dict]  # evaluator.evaluate(task_spec, execution_result, rubric, golden)
    skill_store: Any  # SkillStore-like (retrieve / render_for_operator / list_skills / persist / record_reuse)
    validate_skill: Callable[[dict, list, str, list[str]], dict]  # skill_validator.validate(...)
    logger: Any  # experiment_logger-like (log_graph_event / log_skill_event / log_feedback_event / log_experiment_event)
    rubric: dict
    load_golden: Callable[[dict], dict]  # task_spec -> golden dict
    manifest_summary: dict = field(default_factory=dict)
    retrieval_k: int = 6
    max_validation_retries: int = 2
    task_titles: dict[str, str] = field(default_factory=dict)  # task_id -> title, so operators can target lessons at remaining tasks
    # Experiment 3 (D-21): how much of the evaluator's verdict the operator gets to see per attempt.
    feedback_max_items: int | None = None  # None = every failed check; 3 = only the three most severe findings
    reveal_fixes: bool = True  # False hides `related_components` (the literal parameter fix) from the operator
    # Experiment 4 (D-22): builds the raw cross-task memory log for the memory arms; None disables memory entirely.
    memory_factory: Callable[[str, str], Any] | None = None  # (run_id, condition) -> FeedbackMemory-like


# --------------------------------------------------------------------------- operator instructions

PLAN_INSTRUCTIONS = (
    "Produce an analysis plan for this task by selecting components from the catalogue and setting their "
    "parameters. Use only catalogue component ids and declared parameter options; omitted parameters take their "
    "defaults. Deterministic code executes the plan exactly as written, and the result is scored against a frozen "
    "rubric (correctness, completeness, reproducibility, statistical discipline, communication) and a frozen golden "
    "reference. List in skills_applied the ids of any provided skills you actually used."
)
REVISE_INSTRUCTIONS = (
    "The previous plan was executed and evaluated; the evaluation summary, the feedback items and (when provided) "
    "a reflection are included. Return a complete revised plan - not a diff - that addresses the feedback, and "
    "summarise what changed in changes_summary."
)
REFLECT_INSTRUCTIONS = (
    "Review the plan, the execution result and the evaluator feedback. Return (a) concrete corrections for the "
    "current task, each tied to a feedback id, and (b) lessons that would be reusable in at least two of the "
    "remaining tasks, each citing the feedback ids it came from. Return empty lists when nothing generalises."
)
PROPOSE_INSTRUCTIONS = (
    "Turn at most one reusable lesson into a candidate skill following the embedded schema - only if it applies to "
    "at least two remaining tasks and does not duplicate an existing skill (existing skills are listed). Procedures "
    "must be general, safe (no code execution, network or credentials) and must not restate this task's findings. "
    "Otherwise return proposal: null with a reason."
)
REVISE_PROPOSAL_INSTRUCTIONS = (
    "The proposal failed validation; the failed checks are included. Return a corrected proposal, or null with a "
    "reason if it cannot be made valid without becoming a duplicate or a one-off."
)
SELF_EVALUATE_INSTRUCTIONS = (
    "You executed the plan below and produced the report and metrics shown. No external reviewer is available: "
    "review your own output against the brief and good analytical practice. Return verdict 'accept' if the "
    "output is ready to hand to the sponsor, or 'revise' with at most three findings (most important first), each "
    "naming the catalogue component/parameter change that would address it. Attempts are limited; do not revise "
    "for cosmetic reasons."
)
SELF_REVISE_NOTE = (
    "This revision follows your own review of the previous attempt (no external evaluation is available). "
    "Address the findings you raised."
)
PAST_FEEDBACK_NOTE = (
    "Comments recorded on earlier tasks in this run (checker findings for feedback_memory, your own reviews for "
    "self_refine_memory). They may or may not apply to this task."
)
SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
REPORT_EXCERPT_CHARS = 6000
METRICS_EXCERPT_CHARS = 6000

TASK_BRIEF_KEYS = ("task_id", "title", "objective", "tags", "input_tables", "required_artifacts")


# --------------------------------------------------------------------------- pure helpers


_NO_MATCH = object()


def match_option(options: list | None, value: Any) -> Any:
    """Return the declared option equal to ``value`` (string forms compared, so "30" matches 30); ``_NO_MATCH`` otherwise."""
    if options is None:
        return value
    for option in options:
        if option == value or (not isinstance(option, (list, dict)) and str(option) == str(value)):
            return option
    return _NO_MATCH


def catalogue_index(task_spec: dict) -> dict[str, dict]:
    return {c["id"]: c for c in task_spec.get("components", []) if isinstance(c, dict) and "id" in c}


def default_plan(task_spec: dict) -> dict:
    """The catalogue's naive defaults - used by the fixture baseline and after the operator-step cap."""
    steps = []
    for comp in task_spec.get("components", []):
        if comp.get("default_selected"):
            params = {n: s.get("default") for n, s in (comp.get("params") or {}).items() if "default" in s}
            steps.append({"component": comp["id"], "params": params})
    return {"steps": steps, "skills_applied": [], "rationale": "catalogue defaults", "changes_summary": None}


def validate_plan(raw: dict, task_spec: dict) -> tuple[dict | None, list[str]]:
    """Schema + catalogue validation. Returns (normalised plan dict, errors)."""
    try:
        plan = PlanResponse(**raw)
    except ValidationError as exc:
        return None, [f"schema: {e['loc']}: {e['msg']}" for e in exc.errors()]
    catalogue = catalogue_index(task_spec)
    errors: list[str] = []
    seen: set[str] = set()
    steps: list[dict] = []
    for step in plan.steps:
        comp = catalogue.get(step.component)
        if comp is None:
            errors.append(f"unknown component {step.component!r}; valid ids: {sorted(catalogue)}")
            continue
        if step.component in seen:
            errors.append(f"duplicate component {step.component!r}")
            continue
        seen.add(step.component)
        declared = comp.get("params") or {}
        params: dict[str, Any] = {}
        for name, value in step.params.items():
            spec = declared.get(name)
            if spec is None:
                errors.append(f"{step.component}: unknown parameter {name!r}; declared: {sorted(declared)}")
                continue
            options = spec.get("options")
            if spec.get("multi"):
                if not isinstance(value, list):
                    errors.append(f"{step.component}.{name}: expected a list of options")
                    continue
                matched = [match_option(options, v) for v in value]
                bad = [v for v, m in zip(value, matched) if m is _NO_MATCH]
                if bad:
                    errors.append(f"{step.component}.{name}: {bad} not in options {options}")
                    continue
                params[name] = list(dict.fromkeys(matched))
                continue
            matched = match_option(options, value)
            if matched is _NO_MATCH:
                errors.append(f"{step.component}.{name}: {value!r} not in options {options}")
                continue
            params[name] = matched
        for name, spec in declared.items():
            if name not in params and "default" in spec:
                params[name] = spec["default"]
        steps.append({"component": step.component, "params": params})
    if not steps and not errors:
        errors.append("plan has no valid steps")
    if errors:
        return None, errors
    return {
        "steps": steps,
        "skills_applied": list(dict.fromkeys(plan.skills_applied)),
        "rationale": plan.rationale,
        "changes_summary": plan.changes_summary,
    }, []


def task_brief(task_spec: dict) -> dict:
    return {k: task_spec.get(k) for k in TASK_BRIEF_KEYS if k in task_spec}


def select_feedback(feedback: list[dict], k: int | None) -> list[dict]:
    """The ``k`` most severe feedback items: critical/high first, then heavier rubric weight, then rubric order.

    With ``k=None`` every item is returned (experiments 1 and 2). Experiment 3 shows three per attempt so the
    verification loop has to iterate - a reviewer who lists the three biggest problems, not the whole checklist.
    """
    items = list(feedback or [])
    if k is None or k >= len(items):
        return items
    ranked = sorted(
        enumerate(items),
        key=lambda ix: (SEVERITY_RANK.get(str(ix[1].get("severity")), 9), -float(ix[1].get("weight") or 0), ix[0]),
    )
    keep = sorted(ix for ix, _ in ranked[: max(int(k), 0)])
    return [items[i] for i in keep]


def operator_feedback_view(feedback: list[dict], reveal_fixes: bool) -> list[dict]:
    """What the operator is shown: with ``reveal_fixes=False`` the literal component/parameter fix is withheld."""
    if reveal_fixes:
        return list(feedback or [])
    return [{k: v for k, v in item.items() if k != "related_components"} for item in (feedback or [])]


def evaluation_summary(evaluation: dict | None, shown_feedback: list[dict] | None = None) -> dict | None:
    """Scorecard for the operator. When ``shown_feedback`` is given, only those checks are itemised (the rest is a count)."""
    if not evaluation:
        return None
    failed = [c for c in evaluation.get("checks", []) if not c.get("passed")]
    if shown_feedback is not None:
        visible = {f.get("check_id") for f in shown_feedback if f.get("check_id")}
        # feedback ids are "<task>-<check name>" for check "<task>.<check name>"
        visible |= {str(f.get("feedback_id", "")).replace("-", ".", 1) for f in shown_feedback if f.get("feedback_id")}
        itemised = [c for c in failed if c.get("check_id") in visible]
    else:
        itemised = failed
    summary = {
        "score_total": evaluation.get("score_total"),
        "scores": evaluation.get("scores"),
        "passed": evaluation.get("passed"),
        "failed_checks": [{k: c.get(k) for k in ("check_id", "dimension", "critical", "observed", "expected", "detail")} for c in itemised],
    }
    if shown_feedback is not None:
        summary["n_failed_checks_total"] = len(failed)
        summary["n_failed_checks_shown"] = len(itemised)
        if len(failed) > len(itemised):
            summary["note"] = "only the most severe findings are itemised; further checks failed and will be reported once these are fixed"
    return summary


def _read_text_artifact(result: dict | None, name: str, limit: int) -> str | None:
    """Text of an output file (e.g. report.md) from the execution result, truncated to ``limit`` characters."""
    if not result:
        return None
    candidates = [a for a in (result.get("artifacts") or []) if Path(str(a)).name == name]
    if name == "report.md" and result.get("report_path"):
        candidates.append(result["report_path"])
    if result.get("output_dir"):
        candidates.append(f"{result['output_dir']}/{name}")
    for c in candidates:
        path = Path(str(c))
        path = path if path.is_absolute() else REPO_ROOT / path
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            return text if len(text) <= limit else text[:limit] + f"\n... [truncated, {len(text) - limit} more characters]"
    return None


def output_preview(result: dict | None) -> dict:
    """What a self-reviewing operator gets to look at: its own report and metrics, nothing from the evaluator."""
    metrics = (result or {}).get("metrics") or {}
    metrics_json = json.dumps({k: v for k, v in metrics.items() if k != "plan"}, default=str, ensure_ascii=False, indent=1)
    if len(metrics_json) > METRICS_EXCERPT_CHARS:
        metrics_json = metrics_json[:METRICS_EXCERPT_CHARS] + f"\n... [truncated, {len(metrics_json) - METRICS_EXCERPT_CHARS} more characters]"
    return {"report_md": _read_text_artifact(result, "report.md", REPORT_EXCERPT_CHARS), "metrics_json": metrics_json}


def self_findings_as_feedback(task_id: str, attempt: int, response: dict) -> list[dict]:
    """The operator's own findings in the feedback-item shape the revise step already understands."""
    out = []
    for i, f in enumerate((response or {}).get("findings") or [], 1):
        out.append(
            {
                "feedback_id": f"{task_id}-self-a{attempt}-{i}",
                "check_id": None,
                "criterion": "self_review",
                "issue_type": "self_finding",
                "severity": f.get("severity", "medium"),
                "remediation": f.get("suggested_change") or f.get("issue"),
                "related_components": [],
                "reusable": False,
                "applicable_task_ids": [],
                "observed": None,
                "expected": None,
                "detail": f.get("issue"),
                "source": "self",
            }
        )
    return out


def self_review_items(history: list[dict] | None) -> list[dict]:
    """Every finding of every self-review, each carrying that review's attempt, verdict and summary.

    The self-review arm's memory is exactly what the operator told itself, in the item shape
    :class:`~src.feedback_memory.FeedbackMemory` writes (``issue`` becomes the record's ``text``).
    """
    items: list[dict] = []
    for i, review in enumerate(history or [], 1):
        for finding in review.get("findings") or []:
            items.append(
                {
                    "source": "self",
                    "attempt": review.get("attempt") or i,
                    "severity": finding.get("severity", "medium"),
                    "criterion": "self_review",
                    "issue": finding.get("issue"),
                    "detail": review.get("summary"),
                    "verdict": review.get("verdict"),
                }
            )
    return items


def execution_summary(result: dict | None) -> dict | None:
    if not result:
        return None
    return {
        "status": result.get("status"),
        "components_executed": result.get("components_executed"),
        "components_failed": result.get("components_failed"),
        "errors": result.get("errors"),
        "artifacts": [Path(a).name for a in result.get("artifacts", [])],
        "metric_keys": sorted(k for k in (result.get("metrics") or {}) if isinstance((result.get("metrics") or {}).get(k), dict)),
    }


def _feedback_applied(feedback_item: dict, plan: dict) -> bool:
    """A feedback item counts as incorporated when every recommended component/param appears in the plan."""
    recs = feedback_item.get("related_components") or []
    if not recs:
        return False
    by_id = {s["component"]: s.get("params", {}) for s in plan.get("steps", [])}
    for rec in recs:
        params = by_id.get(rec.get("component"))
        if params is None:
            return False
        for k, v in (rec.get("params") or {}).items():
            if params.get(k) != v:
                return False
    return True


# --------------------------------------------------------------------------- nodes


class ClaimsNodes:
    def __init__(self, services: Services):
        self.s = services

    # ---- shared -----------------------------------------------------------------------
    def _meta(self, state: dict) -> dict:
        return {
            "run_id": state["run_id"],
            "condition": state["condition"],
            "task_id": state["task_id"],
            "attempt": state.get("retry_count", 0) + 1,
            "provider_mode": state.get("provider_mode"),
            "operator": state.get("operator"),
            "model_identifier": state.get("model_identifier"),
        }

    def _graph_event(self, state: dict, node: str, route_reason: str, **extra: Any) -> None:
        history = state.get("route_history") or []
        self.s.logger.log_graph_event(
            {
                **self._meta(state),
                "timestamp": utc_now(),
                "event_type": "node_transition",
                "source_node": history[-1] if history else "START",
                "destination_node": node,
                "route_reason": route_reason,
                "retry_count": state.get("retry_count", 0),
                "operator_steps_used": state.get("operator_steps_used", 0),
                "status": state.get("status", "running"),
                **extra,
            }
        )

    def _budget_exhausted(self, state: dict) -> bool:
        return state.get("operator_steps_used", 0) >= state.get("max_operator_steps", 10**9)

    def _decide(
        self, state: dict, node: str, instructions: str, payload: dict, model: type[BaseModel]
    ) -> tuple[dict | None, int, list[list[str]]]:
        """Ask the provider, re-asking with validation errors up to ``max_validation_retries`` times.

        Pure apart from ``provider.decide`` (which may interrupt); returns
        ``(validated response or None, operator steps consumed, error history)``.
        """
        history: list[list[str]] = []
        attempt_no = state.get("retry_count", 0) + 1
        for i in range(self.s.max_validation_retries + 1):
            p = dict(payload)
            if history:
                p["validation_errors"] = history[-1]
            request = OperatorRequest.build(
                run_id=state["run_id"],
                condition=state["condition"],
                task_id=state["task_id"],
                attempt=attempt_no,
                node=node,
                seq=i + 1,
                instructions=instructions,
                payload=p,
            )
            raw = self.s.provider.decide(request)
            if node in ("plan_task", "revise_plan"):
                parsed, errors = validate_plan(raw if isinstance(raw, dict) else {}, state["task_spec"])
            else:
                try:
                    parsed, errors = model(**(raw if isinstance(raw, dict) else {})).model_dump(), []
                except ValidationError as exc:
                    parsed, errors = None, [f"schema: {e['loc']}: {e['msg']}" for e in exc.errors()]
            if not errors:
                return parsed, i + 1, history
            history.append(errors)
        return None, self.s.max_validation_retries + 1, history

    @staticmethod
    def _task_feedback(state: dict) -> list[dict]:
        """Feedback across every attempt of this task; items absent from the final evaluation are marked resolved.

        Used on the learn path: a task that passed after a revision carries its lesson in the
        feedback it fixed, not in the (empty) feedback of the passing attempt.
        """
        history = state.get("evaluation_history") or []
        final_ids = {f.get("feedback_id") for f in (state.get("feedback") or [])}
        merged: dict[str, dict] = {}
        for attempt_no, evaluation in enumerate(history, 1):
            shown = evaluation.get("feedback_shown")
            for item in (shown if shown is not None else evaluation.get("feedback")) or []:
                entry = merged.setdefault(item.get("feedback_id"), {**item, "first_seen_attempt": attempt_no})
                entry["last_seen_attempt"] = attempt_no
        for fid, entry in merged.items():
            entry["status"] = "open" if fid in final_ids else f"resolved_after_attempt_{entry['last_seen_attempt']}"
        return list(merged.values())

    def _memory(self, state: dict) -> Any | None:
        """The raw memory log for this run and condition, or None when the arm has no memory."""
        if state["condition"] not in MEMORY_CONDITIONS or self.s.memory_factory is None:
            return None
        return self.s.memory_factory(state["run_id"], state["condition"])

    def _with_past_feedback(self, state: dict, payload: dict) -> dict:
        """Add the recalled memory to an operator payload, for the memory arms only."""
        if state["condition"] in MEMORY_CONDITIONS:
            payload["past_feedback"] = list(state.get("past_feedback") or [])
            payload["past_feedback_note"] = PAST_FEEDBACK_NOTE
        return payload

    def _rendered_skills(self, state: dict) -> list[dict]:
        skills = state.get("retrieved_skills") or []
        render = getattr(self.s.skill_store, "render_for_operator", None)
        return render(skills) if callable(render) and skills else skills

    def _base_payload(self, state: dict) -> dict:
        spec = state["task_spec"]
        tables = spec.get("input_tables") or list(self.s.manifest_summary.get("tables", {}).keys())
        summary = self.s.manifest_summary or {}
        return {
            "task_id": state["task_id"],
            "condition": state["condition"],
            "task_spec": task_brief(spec),
            "component_catalogue": spec.get("components", []),
            "manifest_summary": {
                "tables": {t: summary.get("tables", {}).get(t) for t in tables if t in summary.get("tables", {})},
                "relationships": [
                    r for r in summary.get("relationships", []) if any(str(r.get("from", "")).startswith(f"{t}.") for t in tables)
                ],
            },
            "remaining_task_ids": list(state.get("remaining_task_ids") or []),
            "remaining_tasks": [
                {"task_id": t, "title": self.s.task_titles.get(t)} for t in (state.get("remaining_task_ids") or [])
            ],
        }

    # ---- load_context ----------------------------------------------------------------
    def load_context(self, state: dict) -> dict:
        missing = [k for k in ("task_spec", "task_id", "condition", "run_id") if not state.get(k)]
        if missing:
            raise ValueError(f"load_context: state is missing {missing}")
        available: list[dict] = []
        if state["condition"] in SKILL_RETRIEVING_CONDITIONS:
            lister = getattr(self.s.skill_store, "list_skills", None)
            if callable(lister):
                available = [
                    {"skill_id": getattr(s, "skill_id", None) or s.get("skill_id"), "kind": getattr(s, "kind", None) or s.get("kind")}
                    for s in lister()
                ]
        past_feedback: list[dict] = []
        memory = self._memory(state)
        if memory is not None:
            past_feedback = list(memory.recall(state["task_id"]) or [])
            self.s.logger.log_skill_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "memory_retrieved", "count": len(past_feedback)}
            )
        self._graph_event(
            state, "load_context", "start", available_skill_count=len(available), past_feedback_count=len(past_feedback)
        )
        return {
            "route_history": ["load_context"],
            "available_skills": available,
            "past_feedback": past_feedback,
            "status": "running",
        }

    # ---- retrieve_skills -------------------------------------------------------------
    def retrieve_skills(self, state: dict) -> dict:
        retrieved = list(self.s.skill_store.retrieve(state["task_spec"], state.get("task_index", 0), self.s.retrieval_k) or [])
        if state["condition"] == "foundational_only":  # the control never sees evolved skills
            retrieved = [s for s in retrieved if s.get("kind") == "foundational"]
        for skill in retrieved:
            self.s.logger.log_skill_event(
                {
                    **self._meta(state),
                    "timestamp": utc_now(),
                    "event": "skill_retrieved",
                    "skill_id": skill.get("skill_id"),
                    "skill_name": skill.get("name"),
                    "kind": skill.get("kind"),
                    "version": skill.get("version"),
                    "score": skill.get("score"),
                    "matched_terms": skill.get("matched_terms"),
                }
            )
        self._graph_event(state, "retrieve_skills", f"condition={state['condition']}", retrieved=[s.get("skill_id") for s in retrieved])
        return {"route_history": ["retrieve_skills"], "retrieved_skills": retrieved}

    # ---- plan_task -------------------------------------------------------------------
    def plan_task(self, state: dict) -> dict:
        if self._budget_exhausted(state):
            plan = default_plan(state["task_spec"])
            self._graph_event(state, "plan_task", "operator_cap: default plan", operator_steps=0)
            return {"route_history": ["plan_task"], "analysis_plan": plan, "plan_history": [plan], "stop_reason": "operator_cap"}
        payload = self._with_past_feedback(state, self._base_payload(state))
        if state["condition"] in SKILL_RETRIEVING_CONDITIONS:
            payload["retrieved_skills"] = self._rendered_skills(state)
        plan, steps, errors = self._decide(state, "plan_task", PLAN_INSTRUCTIONS, payload, PlanResponse)
        reason = "operator plan"
        if plan is None:
            plan = default_plan(state["task_spec"])
            reason = f"operator response invalid {len(errors)}x; default plan"
        self._graph_event(state, "plan_task", reason, operator_steps=steps, validation_failures=len(errors))
        return {
            "route_history": ["plan_task"],
            "analysis_plan": plan,
            "plan_history": [plan],
            "operator_steps_used": state.get("operator_steps_used", 0) + steps,
        }

    # ---- execute_task ----------------------------------------------------------------
    def execute_task(self, state: dict) -> dict:
        attempt = state.get("retry_count", 0) + 1
        run_context = {
            "run_id": state["run_id"],
            "condition": state["condition"],
            "task_id": state["task_id"],
            "attempt": attempt,
            "seed": state.get("seed", 42),
            "output_dir": str(Path(state["output_dir"]) / f"attempt_{attempt}"),
            "manifest_path": (state.get("dataset_manifest") or {}).get("_path"),
            "data_dir": (state.get("dataset_manifest") or {}).get("_data_dir"),
        }
        plan = state.get("analysis_plan") or default_plan(state["task_spec"])
        try:
            result = self.s.execute_task(state["task_spec"], plan, run_context)
        except Exception as exc:  # noqa: BLE001 - executor bugs become recorded errors, never a crash
            result = {
                "status": "error",
                "task_id": state["task_id"],
                "attempt": attempt,
                "output_dir": run_context["output_dir"],
                "artifacts": [],
                "metrics": {},
                "components_executed": [],
                "components_failed": [s["component"] for s in plan.get("steps", [])],
                "errors": [{"type": "runtime_error", "component": None, "message": f"{type(exc).__name__}: {exc}"[:500]}],
                "seed": run_context["seed"],
                "duration_seconds": 0.0,
            }
        errors = list(result.get("errors") or [])
        self._graph_event(
            state, "execute_task", f"attempt {attempt}", execution_status=result.get("status"), error_count=len(errors)
        )
        return {
            "route_history": ["execute_task"],
            "execution_result": result,
            "execution_attempts": state.get("execution_attempts", 0) + 1,
            "execution_errors": state.get("execution_errors", 0) + len(errors),
            "artifacts": list(result.get("artifacts") or []),
            "errors": [{"attempt": attempt, **e} for e in errors],
        }

    # ---- evaluate_output -------------------------------------------------------------
    def evaluate_output(self, state: dict) -> dict:
        golden = self.s.load_golden(state["task_spec"])
        evaluation = self.s.evaluate(state["task_spec"], state.get("execution_result") or {}, self.s.rubric, golden)
        all_feedback = list(evaluation.get("feedback") or [])
        # rubric weights travel with the feedback so the cap can rank by severity, then weight
        weights = {c.get("check_id"): c.get("weight", 1) for c in evaluation.get("checks", [])}
        for item in all_feedback:
            item.setdefault("weight", weights.get(item.get("check_id"), 1))
        self_refine = state["condition"] in SELF_REVIEW_CONDITIONS
        # the self-reviewing condition never sees the evaluator; it is scored for the record only
        feedback = [] if self_refine else select_feedback(all_feedback, self.s.feedback_max_items)
        evaluation["feedback_shown"] = feedback
        evaluation["n_feedback_total"] = len(all_feedback)
        attempt = state.get("retry_count", 0) + 1
        for item in feedback:
            self.s.logger.log_feedback_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "feedback_issued", "incorporated": False, "source": "evaluator", **item}
            )
        passed = bool(evaluation.get("passed"))
        can_retry = state.get("retry_count", 0) < state.get("max_retries", 0) and not self._budget_exhausted(state)
        if state["condition"] == "skill_learning":
            next_route = "learn" if passed or not can_retry else "retry"
        elif self_refine:
            next_route = "self_evaluate" if can_retry else "completed"
        else:
            next_route = "completed" if passed or not can_retry else "retry"
        # per-attempt experiment record (the final record with status "done" is written by finalize_task)
        self.s.logger.log_experiment_event(
            {
                **self._meta(state),
                "timestamp": utc_now(),
                "status": "attempt",
                "attempt": attempt,
                "passed": passed,
                "evaluator_score_total": evaluation.get("score_total"),
                "evaluator_score_by_dimension": evaluation.get("scores"),
                "n_checks": evaluation.get("n_checks"),
                "n_failed_checks": len(all_feedback),
                "n_feedback_shown": len(feedback),
                "critical_failures": list(evaluation.get("critical_failures") or []),
                "skills_applied": list((state.get("analysis_plan") or {}).get("skills_applied") or []),
                "execution_errors": len((state.get("execution_result") or {}).get("errors") or []),
                "graph_route": list(state.get("route_history") or []) + ["evaluate_output"],
                "freeze_sha256": state.get("freeze_sha256"),
                "evaluator_version": evaluation.get("evaluator_version"),
                "rubric_version": evaluation.get("rubric_version"),
            }
        )
        self._graph_event(
            state,
            "evaluate_output",
            f"passed={passed} score={evaluation.get('score_total')} -> {next_route}",
            score_total=evaluation.get("score_total"),
            passed=passed,
            next_route=next_route,
            n_failed_checks=len(all_feedback),
            n_feedback_shown=len(feedback),
        )
        return {
            "route_history": ["evaluate_output"],
            "evaluation": evaluation,
            "evaluation_history": [evaluation],
            "feedback": feedback,
            "next_route": next_route,
        }

    # ---- self_evaluate (self_refine only) ------------------------------------------------
    def self_evaluate(self, state: dict) -> dict:
        attempt = state.get("retry_count", 0) + 1
        if self._budget_exhausted(state):
            verdict = {"verdict": "accept", "findings": [], "summary": "operator_cap: accepted by default"}
            self._graph_event(state, "self_evaluate", "operator_cap: default accept", operator_steps=0)
            return {
                "route_history": ["self_evaluate"], "self_evaluation": verdict, "self_evaluation_history": [verdict],
                "feedback": [], "next_route": "completed", "stop_reason": "operator_cap",
            }
        payload = self._base_payload(state)
        payload.update(
            {
                "plan": state.get("analysis_plan"),
                "execution_summary": execution_summary(state.get("execution_result")),
                "output": output_preview(state.get("execution_result")),
                "attempt": attempt,
                "attempts_remaining": max(int(state.get("max_retries", 0)) - int(state.get("retry_count", 0)), 0),
                "previous_self_reviews": list(state.get("self_evaluation_history") or []),
            }
        )
        response, steps, errors = self._decide(state, "self_evaluate", SELF_EVALUATE_INSTRUCTIONS, payload, SelfEvaluationResponse)
        reason = "operator self-review"
        if response is None:
            response = {"verdict": "accept", "findings": [], "summary": f"invalid response {len(errors)}x; accepted by default"}
            reason = f"operator response invalid {len(errors)}x; default accept"
        response = {**response, "attempt": attempt, "findings": list(response.get("findings") or [])[:3]}
        feedback = self_findings_as_feedback(state["task_id"], attempt, response)
        for item in feedback:
            self.s.logger.log_feedback_event({**self._meta(state), "timestamp": utc_now(), "event": "feedback_issued", "incorporated": False, **item})
        next_route = "retry" if response.get("verdict") == "revise" else "completed"
        frozen = (state.get("evaluation") or {})
        self._graph_event(
            state, "self_evaluate", f"{reason}: verdict={response.get('verdict')} -> {next_route}",
            operator_steps=steps, validation_failures=len(errors), verdict=response.get("verdict"), findings=len(feedback),
            frozen_score_total=frozen.get("score_total"), frozen_passed=frozen.get("passed"),
        )
        return {
            "route_history": ["self_evaluate"],
            "self_evaluation": response,
            "self_evaluation_history": [response],
            "feedback": feedback,
            "next_route": next_route,
            "operator_steps_used": state.get("operator_steps_used", 0) + steps,
        }

    # ---- reflect_on_feedback ---------------------------------------------------------
    def reflect_on_feedback(self, state: dict) -> dict:
        if self._budget_exhausted(state):
            reflection = {"reusable_lessons": [], "current_task_corrections": []}
            self._graph_event(state, "reflect_on_feedback", "operator_cap: empty reflection", operator_steps=0)
            return {"route_history": ["reflect_on_feedback"], "reflection": reflection, "stop_reason": "operator_cap"}
        learning = state.get("next_route") == "learn"
        payload = self._base_payload(state)
        payload.update(
            {
                "purpose": "learn: extract reusable lessons from the whole task" if learning else "retry: correct the current attempt",
                "plan": state.get("analysis_plan"),
                "plan_history": list(state.get("plan_history") or []),
                "execution_summary": execution_summary(state.get("execution_result")),
                "evaluation_summary": evaluation_summary(state.get("evaluation"), state.get("feedback") or []),
                "feedback": operator_feedback_view(
                    self._task_feedback(state) if learning else (state.get("feedback") or []), self.s.reveal_fixes
                ),
                "attempts": state.get("execution_attempts", 0),
                "attempts_remaining": max(int(state.get("max_retries", 0)) - int(state.get("retry_count", 0)), 0),
            }
        )
        reflection, steps, errors = self._decide(state, "reflect_on_feedback", REFLECT_INSTRUCTIONS, payload, ReflectionResponse)
        if reflection is None:
            reflection = {"reusable_lessons": [], "current_task_corrections": []}
        self._graph_event(
            state,
            "reflect_on_feedback",
            f"route={state.get('next_route')}",
            operator_steps=steps,
            validation_failures=len(errors),
            reusable_lessons=len(reflection.get("reusable_lessons") or []),
        )
        return {
            "route_history": ["reflect_on_feedback"],
            "reflection": reflection,
            "operator_steps_used": state.get("operator_steps_used", 0) + steps,
        }

    # ---- revise_plan -----------------------------------------------------------------
    def revise_plan(self, state: dict) -> dict:
        payload = self._with_past_feedback(state, self._base_payload(state))
        payload.update(
            {
                "prior_plan": state.get("analysis_plan"),
                "execution_summary": execution_summary(state.get("execution_result")),
                "attempt": state.get("retry_count", 0) + 2,
                "attempts_remaining": max(int(state.get("max_retries", 0)) - int(state.get("retry_count", 0)) - 1, 0),
            }
        )
        instructions = REVISE_INSTRUCTIONS
        if state["condition"] in SELF_REVIEW_CONDITIONS:  # its own review is the only feedback it gets
            payload.update({"self_review": state.get("self_evaluation"), "feedback": state.get("feedback") or [], "note": SELF_REVISE_NOTE})
            instructions = REVISE_INSTRUCTIONS + " " + SELF_REVISE_NOTE
        else:
            payload.update(
                {
                    "evaluation_summary": evaluation_summary(state.get("evaluation"), state.get("feedback") or []),
                    "feedback": operator_feedback_view(state.get("feedback") or [], self.s.reveal_fixes),
                }
            )
        if state["condition"] != "baseline" and state["condition"] not in SELF_REVIEW_CONDITIONS:
            payload["reflection"] = state.get("reflection")
        if state["condition"] in SKILL_RETRIEVING_CONDITIONS:
            payload["retrieved_skills"] = self._rendered_skills(state)
        plan, steps, errors = self._decide(state, "revise_plan", instructions, payload, PlanResponse)
        reason = "operator revision"
        if plan is None:
            plan = state.get("analysis_plan") or default_plan(state["task_spec"])
            reason = f"operator response invalid {len(errors)}x; plan unchanged"
        incorporated = [f.get("feedback_id") for f in state.get("feedback") or [] if _feedback_applied(f, plan)]
        for fid in incorporated:
            self.s.logger.log_feedback_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "feedback_incorporated", "feedback_id": fid, "incorporated": True}
            )
        self._graph_event(
            state, "revise_plan", reason, operator_steps=steps, validation_failures=len(errors), feedback_incorporated=incorporated
        )
        return {
            "route_history": ["revise_plan"],
            "analysis_plan": plan,
            "plan_history": [plan],
            "retry_count": state.get("retry_count", 0) + 1,
            "operator_steps_used": state.get("operator_steps_used", 0) + steps,
        }

    # ---- propose_skill ---------------------------------------------------------------
    def _existing_skills_brief(self) -> list[dict]:
        lister = getattr(self.s.skill_store, "list_skills", None)
        if not callable(lister):
            return []
        out = []
        for s in lister():
            get = (lambda k: getattr(s, k, None)) if not isinstance(s, dict) else s.get
            sections = get("sections") or {}
            out.append(
                {
                    "skill_id": get("skill_id"),
                    "name": get("name"),
                    "kind": get("kind"),
                    "objective": sections.get("objective"),
                    "procedure": sections.get("procedure"),
                    "required_checks": sections.get("required_checks"),
                }
            )
        return out

    def propose_skill(self, state: dict) -> dict:
        reflection = state.get("reflection") or {}
        lessons = reflection.get("reusable_lessons") or []
        remaining = set(state.get("remaining_task_ids") or [])
        eligible = [l for l in lessons if len(set(l.get("applicable_task_ids") or []) & remaining) >= 2]
        skip_reason = None
        if self._budget_exhausted(state):
            skip_reason = "operator_cap"
        elif not eligible:
            skip_reason = "no lesson reusable in >= 2 remaining tasks"
        if skip_reason:
            self.s.logger.log_skill_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "skill_proposal_skipped", "reason": skip_reason}
            )
            self._graph_event(state, "propose_skill", f"skipped: {skip_reason}", operator_steps=0)
            update = {"route_history": ["propose_skill"], "skill_proposal": None}
            if skip_reason == "operator_cap":
                update["stop_reason"] = "operator_cap"
            return update
        payload = self._base_payload(state)
        payload.update(
            {
                "plan": state.get("analysis_plan"),
                "evaluation_summary": evaluation_summary(state.get("evaluation"), state.get("feedback") or []),
                "feedback": operator_feedback_view(self._task_feedback(state), self.s.reveal_fixes),
                "reflection": reflection,
                "existing_skills": self._existing_skills_brief(),
            }
        )
        response, steps, errors = self._decide(state, "propose_skill", PROPOSE_INSTRUCTIONS, payload, SkillProposalResponse)
        proposal = (response or {}).get("proposal")
        self.s.logger.log_skill_event(
            {
                **self._meta(state),
                "timestamp": utc_now(),
                "event": "skill_proposed" if proposal else "skill_proposal_skipped",
                "proposal_name": (proposal or {}).get("name"),
                "reason": None if proposal else (response or {}).get("reason_if_null") or f"invalid response {len(errors)}x",
                "applicable_task_ids": (proposal or {}).get("applicable_task_ids"),
                "source_feedback_ids": (proposal or {}).get("source_feedback_ids"),
            }
        )
        self._graph_event(
            state, "propose_skill", "proposal" if proposal else "null proposal", operator_steps=steps, validation_failures=len(errors)
        )
        return {
            "route_history": ["propose_skill"],
            "skill_proposal": proposal,
            "operator_steps_used": state.get("operator_steps_used", 0) + steps,
        }

    # ---- validate_skill --------------------------------------------------------------
    def validate_skill(self, state: dict) -> dict:
        proposal = state.get("skill_proposal")
        if not proposal:
            validation = {"decision": "rejected", "checks": [], "reasons": ["no proposal"], "duplicate_of": None, "similarity": None}
        else:
            lister = getattr(self.s.skill_store, "list_skills", None)
            existing = list(lister()) if callable(lister) else []
            validation = self.s.validate_skill(proposal, existing, state["task_id"], list(state.get("remaining_task_ids") or []))
        decision = validation.get("decision", "rejected")
        if decision == "retry_revision" and state.get("proposal_revisions", 0) >= 1:
            decision = "rejected"
            validation = {**validation, "decision": "rejected", "reasons": list(validation.get("reasons") or []) + ["revision budget exhausted"]}
        if decision == "retry_revision" and self._budget_exhausted(state):
            decision = "rejected"
            validation = {**validation, "decision": "rejected", "reasons": list(validation.get("reasons") or []) + ["operator_cap"]}
        self.s.logger.log_skill_event(
            {
                **self._meta(state),
                "timestamp": utc_now(),
                "event": "skill_validated" if decision == "accepted" else "skill_rejected" if decision == "rejected" else "skill_revision_requested",
                "proposal_name": (proposal or {}).get("name"),
                "decision": decision,
                "checks": validation.get("checks"),
                "duplicate_of": validation.get("duplicate_of"),
                "similarity": validation.get("similarity"),
                "reasons": validation.get("reasons"),
            }
        )
        self._graph_event(state, "validate_skill", f"decision={decision}", decision=decision)
        return {"route_history": ["validate_skill"], "skill_validation": {**validation, "decision": decision}, "next_route": decision}

    # ---- revise_skill_proposal -------------------------------------------------------
    def revise_skill_proposal(self, state: dict) -> dict:
        payload = self._base_payload(state)
        payload.update({"proposal": state.get("skill_proposal"), "validation": state.get("skill_validation"), "existing_skills": self._existing_skills_brief()})
        response, steps, errors = self._decide(
            state, "revise_skill_proposal", REVISE_PROPOSAL_INSTRUCTIONS, payload, SkillProposalResponse
        )
        proposal = (response or {}).get("proposal")
        self._graph_event(
            state, "revise_skill_proposal", "revised" if proposal else "withdrawn", operator_steps=steps, validation_failures=len(errors)
        )
        return {
            "route_history": ["revise_skill_proposal"],
            "skill_proposal": proposal,
            "proposal_revisions": state.get("proposal_revisions", 0) + 1,
            "operator_steps_used": state.get("operator_steps_used", 0) + steps,
        }

    # ---- persist_skill ---------------------------------------------------------------
    def persist_skill(self, state: dict) -> dict:
        proposal = state["skill_proposal"]
        provenance = {
            "run_id": state["run_id"],
            "condition": state["condition"],
            "task_id": state["task_id"],
            "created_after_task": state["task_id"],
            "created_after_task_index": state.get("task_index"),
            "source_feedback_ids": list(proposal.get("source_feedback_ids") or []),
            "evaluation_score_total": (state.get("evaluation") or {}).get("score_total"),
            "provider_mode": state.get("provider_mode"),
            "operator": state.get("operator"),
            "model_identifier": state.get("model_identifier"),
        }
        skill = self.s.skill_store.persist(proposal, provenance)
        get = (lambda k: getattr(skill, k, None)) if not isinstance(skill, dict) else skill.get
        skill_id, path = get("skill_id"), get("path")
        self.s.logger.log_skill_event(
            {
                **self._meta(state),
                "timestamp": utc_now(),
                "event": "skill_persisted",
                "skill_id": skill_id,
                "skill_name": get("name"),
                "version": get("version"),
                "path": rel(path) if path else None,
                "provenance": provenance,
            }
        )
        self._graph_event(state, "persist_skill", "accepted", skill_id=skill_id)
        return {"route_history": ["persist_skill"], "skills_created": [skill_id]}

    # ---- finalize_task ---------------------------------------------------------------
    def finalize_task(self, state: dict) -> dict:
        evaluation = state.get("evaluation") or {}
        passed = bool(evaluation.get("passed"))
        self_reviews = list(state.get("self_evaluation_history") or [])
        self_accepted = bool(self_reviews) and self_reviews[-1].get("verdict") == "accept"
        if state.get("stop_reason"):
            stop_reason = state["stop_reason"]
        elif state["condition"] in SELF_REVIEW_CONDITIONS:  # the operator's own verdict ended the loop, not the evaluator's
            stop_reason = "self_accepted" if self_accepted else "retry_budget_exhausted"
        else:
            stop_reason = "passed" if passed else "retry_budget_exhausted"
        retrieved_ids = [s.get("skill_id") for s in state.get("retrieved_skills") or []]
        applied: list[str] = []
        for plan in state.get("plan_history") or []:
            applied.extend(plan.get("skills_applied") or [])
        reused = sorted(set(applied) & set(retrieved_ids))
        recorder = getattr(self.s.skill_store, "record_reuse", None)
        for skill_id in reused:
            if callable(recorder):
                recorder(skill_id, state["task_id"])
            self.s.logger.log_skill_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "skill_reused", "skill_id": skill_id}
            )
        memory = self._memory(state)
        if memory is not None:
            items = (
                self_review_items(self_reviews)
                if state["condition"] in SELF_REVIEW_CONDITIONS
                else self._task_feedback(state)
            )
            written = memory.append(state["task_id"], (state.get("task_spec") or {}).get("title", ""), items)
            self.s.logger.log_skill_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "memory_written", "count": written}
            )
        history = list(state.get("evaluation_history") or [])
        first_attempt_passed = bool(history[0].get("passed")) if history else False
        attempts_to_pass = next((i for i, e in enumerate(history, 1) if e.get("passed")), None)
        record = {
            **self._meta(state),
            "attempt": state.get("execution_attempts", 0),
            "timestamp": utc_now(),
            "input_hash": sha256_text(json.dumps(state.get("task_spec"), sort_keys=True, default=str) + str(state.get("freeze_sha256"))),
            "files_used": list((state.get("task_spec") or {}).get("input_tables") or []),
            "skills_retrieved": retrieved_ids,
            "skills_created": list(state.get("skills_created") or []),
            "skills_reused": reused,
            "graph_route": list(state.get("route_history") or []) + ["finalize_task"],
            "execution_attempts": state.get("execution_attempts", 0),
            "execution_errors": state.get("execution_errors", 0),
            "retry_count": state.get("retry_count", 0),
            "evaluator_score_total": evaluation.get("score_total"),
            "evaluator_score_by_dimension": evaluation.get("scores"),
            "passed": passed,
            "first_attempt_passed": first_attempt_passed,
            "attempts_to_pass": attempts_to_pass,
            "first_attempt_score_total": history[0].get("score_total") if history else None,
            "score_by_attempt": [e.get("score_total") for e in history],
            "self_declared_pass": self_accepted if state["condition"] in SELF_REVIEW_CONDITIONS else None,
            "past_feedback_count": len(state.get("past_feedback") or []),  # memory items this task was planned with
            "artifact_paths": list(state.get("artifacts") or []),
            "operator_steps_used": state.get("operator_steps_used", 0),
            "stop_reason": stop_reason,
            "freeze_sha256": state.get("freeze_sha256"),
            "evaluator_version": evaluation.get("evaluator_version"),
            "rubric_version": evaluation.get("rubric_version"),
            "status": "done",
        }
        self.s.logger.log_experiment_event(record)
        self._graph_event(state, "finalize_task", stop_reason, destination="END")
        return {"route_history": ["finalize_task"], "status": "done", "stop_reason": stop_reason}
