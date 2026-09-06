"""Typed LangGraph state and the operator response models for the claims skill loop.

The state is a ``TypedDict`` so LangGraph can merge partial node updates. List
fields that only ever grow (route history, artifacts, errors, histories) use an
additive reducer, so nodes return just the new items.

The response models define what an operator (a stateless Claude Code subagent in
``manual`` mode, or the deterministic fixture in ``stub`` mode) must return for
each LLM-decision node. Their JSON schema is embedded in every operator request.
Nothing in this module reads secrets or performs IO.
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field

# The brief's three conditions plus an optional control, `foundational_only`, which retrieves the
# curated foundational skills but never reflects across tasks, proposes, or persists - it separates
# "having a skill library" from "learning new skills" (decision D-11). Not run by default.
CONDITIONS: tuple[str, ...] = ("baseline", "reflection_only", "skill_learning", "foundational_only")
DEFAULT_CONDITIONS: tuple[str, ...] = ("baseline", "reflection_only", "skill_learning")
SKILL_RETRIEVING_CONDITIONS: tuple[str, ...] = ("skill_learning", "foundational_only")
Condition = Literal["baseline", "reflection_only", "skill_learning", "foundational_only"]

LLM_DECISION_NODES: tuple[str, ...] = (
    "plan_task",
    "revise_plan",
    "reflect_on_feedback",
    "propose_skill",
    "revise_skill_proposal",
)


class ClaimsGraphState(TypedDict, total=False):
    # --- identity and configuration -------------------------------------------------
    run_id: str
    condition: str
    task_id: str
    task_index: int
    task_spec: dict
    dataset_manifest: dict
    seed: int
    output_dir: str
    golden_path: str
    freeze_sha256: str
    max_retries: int
    pass_threshold: float
    max_operator_steps: int
    remaining_task_ids: list[str]
    # --- provider metadata (recorded on every event) -------------------------------
    provider_mode: str
    operator: str
    model_identifier: str
    # --- working values (replaced by nodes) ------------------------------------------
    available_skills: list[dict]
    retrieved_skills: list[dict]
    analysis_plan: dict | None
    execution_result: dict | None
    evaluation: dict | None
    feedback: list[dict]
    reflection: dict | None
    skill_proposal: dict | None
    skill_validation: dict | None
    retry_count: int
    proposal_revisions: int
    operator_steps_used: int
    execution_attempts: int
    execution_errors: int
    status: str  # running | done | failed
    stop_reason: str | None  # passed | retry_budget_exhausted | operator_cap | None
    next_route: str | None  # decision recorded by evaluate_output / validate_skill for the routing functions
    # --- append-only histories ------------------------------------------------------
    route_history: Annotated[list[str], operator.add]
    artifacts: Annotated[list[str], operator.add]
    errors: Annotated[list[dict], operator.add]
    skills_created: Annotated[list[str], operator.add]
    plan_history: Annotated[list[dict], operator.add]
    evaluation_history: Annotated[list[dict], operator.add]


def initial_state(
    *,
    run_id: str,
    condition: str,
    task_id: str,
    task_index: int,
    task_spec: dict,
    dataset_manifest: dict,
    seed: int,
    output_dir: str,
    golden_path: str,
    freeze_sha256: str,
    max_retries: int,
    pass_threshold: float,
    max_operator_steps: int,
    remaining_task_ids: list[str],
    provider_mode: str,
    operator: str,
    model_identifier: str,
    operator_steps_used: int = 0,
) -> ClaimsGraphState:
    """Build the state for one task invocation. ``operator_steps_used`` carries the per-condition counter in."""
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; expected one of {CONDITIONS}")
    return ClaimsGraphState(
        run_id=run_id,
        condition=condition,
        task_id=task_id,
        task_index=task_index,
        task_spec=task_spec,
        dataset_manifest=dataset_manifest,
        seed=seed,
        output_dir=output_dir,
        golden_path=golden_path,
        freeze_sha256=freeze_sha256,
        max_retries=max_retries,
        pass_threshold=pass_threshold,
        max_operator_steps=max_operator_steps,
        remaining_task_ids=list(remaining_task_ids),
        provider_mode=provider_mode,
        operator=operator,
        model_identifier=model_identifier,
        available_skills=[],
        retrieved_skills=[],
        analysis_plan=None,
        execution_result=None,
        evaluation=None,
        feedback=[],
        reflection=None,
        skill_proposal=None,
        skill_validation=None,
        retry_count=0,
        proposal_revisions=0,
        operator_steps_used=operator_steps_used,
        execution_attempts=0,
        execution_errors=0,
        status="running",
        stop_reason=None,
        route_history=[],
        artifacts=[],
        errors=[],
        skills_created=[],
        plan_history=[],
        evaluation_history=[],
    )


# --------------------------------------------------------------------------- operator responses


class _Lenient(BaseModel):
    """Required fields are enforced; unknown extra fields are ignored rather than rejected."""

    model_config = ConfigDict(extra="ignore")


class PlanStep(_Lenient):
    component: str = Field(description="Component id from the task's catalogue.")
    params: dict[str, Any] = Field(default_factory=dict, description="Parameter values; only declared options are valid.")


class PlanResponse(_Lenient):
    """Answer for ``plan_task`` and ``revise_plan``. A revised plan is a complete plan, not a diff."""

    steps: list[PlanStep] = Field(min_length=1)
    skills_applied: list[str] = Field(default_factory=list, description="Skill ids the operator actually used.")
    rationale: str = ""
    changes_summary: str | None = Field(default=None, description="revise_plan only: what changed and why.")


class ReusableLesson(_Lenient):
    lesson: str
    applicable_task_ids: list[str] = Field(default_factory=list)
    source_feedback_ids: list[str] = Field(default_factory=list)


class Correction(_Lenient):
    feedback_id: str
    correction: str


class ReflectionResponse(_Lenient):
    """Answer for ``reflect_on_feedback``."""

    reusable_lessons: list[ReusableLesson] = Field(default_factory=list)
    current_task_corrections: list[Correction] = Field(default_factory=list)


class SkillProposalBody(_Lenient):
    name: str = Field(min_length=3)
    tags: list[str] = Field(default_factory=list)
    trigger: str = Field(min_length=10)
    objective: str = Field(min_length=10)
    procedure: list[str] = Field(min_length=2)
    required_checks: list[str] = Field(default_factory=list)
    expected_artifacts: list[str] = Field(default_factory=list)
    failure_modes: list[str] = Field(default_factory=list)
    example: str = ""
    applicable_task_ids: list[str] = Field(default_factory=list)
    source_feedback_ids: list[str] = Field(default_factory=list)


class SkillProposalResponse(_Lenient):
    """Answer for ``propose_skill`` and ``revise_skill_proposal``; ``proposal`` may be null with a reason."""

    proposal: SkillProposalBody | None = None
    reason_if_null: str | None = None


RESPONSE_MODELS: dict[str, type[BaseModel]] = {
    "plan_task": PlanResponse,
    "revise_plan": PlanResponse,
    "reflect_on_feedback": ReflectionResponse,
    "propose_skill": SkillProposalResponse,
    "revise_skill_proposal": SkillProposalResponse,
}


def response_schema_for(node: str) -> dict:
    """JSON schema embedded in the operator request for ``node``."""
    try:
        return RESPONSE_MODELS[node].model_json_schema()
    except KeyError as exc:
        raise KeyError(f"{node!r} is not an LLM-decision node; expected one of {LLM_DECISION_NODES}") from exc
