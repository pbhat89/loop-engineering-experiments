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
    SKILL_RETRIEVING_CONDITIONS,
    PlanResponse,
    ReflectionResponse,
    SkillProposalResponse,
)
from src.llm_provider import BaseProvider, OperatorRequest
from src.utils import rel, sha256_text, utc_now

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


def evaluation_summary(evaluation: dict | None) -> dict | None:
    if not evaluation:
        return None
    return {
        "score_total": evaluation.get("score_total"),
        "scores": evaluation.get("scores"),
        "passed": evaluation.get("passed"),
        "failed_checks": [
            {k: c.get(k) for k in ("check_id", "dimension", "critical", "observed", "expected", "detail")}
            for c in evaluation.get("checks", [])
            if not c.get("passed")
        ],
    }


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
            for item in evaluation.get("feedback") or []:
                entry = merged.setdefault(item.get("feedback_id"), {**item, "first_seen_attempt": attempt_no})
                entry["last_seen_attempt"] = attempt_no
        for fid, entry in merged.items():
            entry["status"] = "open" if fid in final_ids else f"resolved_after_attempt_{entry['last_seen_attempt']}"
        return list(merged.values())

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
        self._graph_event(state, "load_context", "start", available_skill_count=len(available))
        return {"route_history": ["load_context"], "available_skills": available, "status": "running"}

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
        payload = self._base_payload(state)
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
        feedback = list(evaluation.get("feedback") or [])
        attempt = state.get("retry_count", 0) + 1
        for item in feedback:
            self.s.logger.log_feedback_event(
                {**self._meta(state), "timestamp": utc_now(), "event": "feedback_issued", "incorporated": False, **item}
            )
        passed = bool(evaluation.get("passed"))
        can_retry = state.get("retry_count", 0) < state.get("max_retries", 0) and not self._budget_exhausted(state)
        if state["condition"] == "skill_learning":
            next_route = "learn" if passed or not can_retry else "retry"
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
        )
        return {
            "route_history": ["evaluate_output"],
            "evaluation": evaluation,
            "evaluation_history": [evaluation],
            "feedback": feedback,
            "next_route": next_route,
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
                "evaluation_summary": evaluation_summary(state.get("evaluation")),
                "feedback": self._task_feedback(state) if learning else (state.get("feedback") or []),
                "attempts": state.get("execution_attempts", 0),
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
        payload = self._base_payload(state)
        payload.update(
            {
                "prior_plan": state.get("analysis_plan"),
                "execution_summary": execution_summary(state.get("execution_result")),
                "evaluation_summary": evaluation_summary(state.get("evaluation")),
                "feedback": state.get("feedback") or [],
            }
        )
        if state["condition"] != "baseline":
            payload["reflection"] = state.get("reflection")
        if state["condition"] in SKILL_RETRIEVING_CONDITIONS:
            payload["retrieved_skills"] = self._rendered_skills(state)
        plan, steps, errors = self._decide(state, "revise_plan", REVISE_INSTRUCTIONS, payload, PlanResponse)
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
                "evaluation_summary": evaluation_summary(state.get("evaluation")),
                "feedback": self._task_feedback(state),
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
        stop_reason = state.get("stop_reason") or ("passed" if passed else "retry_budget_exhausted")
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
        history = list(state.get("evaluation_history") or [])
        first_attempt_passed = bool(history[0].get("passed")) if history else False
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
