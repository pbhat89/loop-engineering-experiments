"""Graph state, operator request/response models, and the operator instruction texts.

The request/response contract the operator sees, and the graph state behind it:
one typed state a LangGraph node can update piecemeal, one Pydantic model per operator
step whose JSON schema is embedded in every request, and one request envelope that knows
where its request and response files live.

File protocol (``docs/OPERATOR_PROTOCOL.md``)::

    artifacts/uw/<run_id>/requests/<arm>/<phase>_case<NN>_<step>[_rN].json
    artifacts/uw/<run_id>/responses/<arm>/<same name>.json
"""
from __future__ import annotations

import operator
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator

from src.underwriting.scorer import normalise_class, normalise_decision
from src.utils import atomic_write_json, utc_now

CONDITIONS: tuple[str, ...] = ("new_joiner", "notebook", "written_rules", "precedent", "ask_senior")
PHASES: tuple[str, ...] = ("train", "holdout")
STEPS: tuple[str, ...] = ("ask", "decide", "reflect")

MEMORY_CONDITIONS: tuple[str, ...] = ("notebook", "written_rules", "precedent")
ASKING_CONDITIONS: tuple[str, ...] = ("ask_senior",)
REFLECTING_CONDITIONS: tuple[str, ...] = ("written_rules",)

# The default cap on the ask-a-senior questions. ``max_questions`` in
# config/underwriting.yaml overrides it for a run, and everything that depends on the cap -
# the instruction text, the response schema and the oracle's own limit - derives from the
# configured value rather than repeating this number. Defined here once; senior.py imports it.
MAX_QUESTIONS = 4
MAX_RATIONALE_WORDS = 80
MAX_REREQUESTS = 2  # the first request plus two re-requests; then the answer is scored as unparseable

Condition = Literal["new_joiner", "notebook", "written_rules", "precedent", "ask_senior"]


# --------------------------------------------------------------------------- operator instructions

DECIDE_INSTRUCTIONS = (
    "Rate this life-insurance application. The starter manual in this request is the whole of the written "
    "practice; work from it and from anything else this request gives you. Return the decision, the rating "
    "class, any modifiers (flat extras with their band, and exclusion riders naming the hazard), the factors "
    "that drove the rating, and a rationale of at most 80 words. Use only the decisions and class names the "
    "manual defines. Where the manual says refer to underwriting judgement, decide anyway and say in the "
    "rationale that you did. One attempt: there is no resubmission."
)
_NUMBER_WORDS: tuple[str, ...] = (
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
)


def _number_word(n: int) -> str:
    return _NUMBER_WORDS[n] if 0 <= n < len(_NUMBER_WORDS) else str(n)


def ask_instructions(max_questions: int = MAX_QUESTIONS) -> str:
    """The ask-step instructions for a run whose cap is ``max_questions``.

    The number is never hardcoded here: it is the same value :func:`ask_response_model`
    caps ``questions`` at and the same value the senior oracle will answer. A run
    configured for one question does not invite four and silently drop three, and a run
    configured for six does not say four and then reject the operator's fifth.
    """
    n = max(int(max_questions), 0)
    word = _number_word(n)
    noun = "question" if n == 1 else "questions"
    return (
        f"Before you rate this application you may ask a senior underwriter up to {word} {noun}. The senior "
        "answers each one narrowly and literally and will not rate the file for you. Ask none, or ask up to "
        f"{word} - how many is your call, and how many you used is recorded. Return the questions and nothing else."
    )


ASK_INSTRUCTIONS = ask_instructions()
REFLECT_INSTRUCTIONS = (
    "Here is your house-rule book as it stands, the application you have just rated, the answer you gave and "
    "the reviewer's markup on it. Rewrite the whole book, in your own words, so that someone reading only the "
    "book would have got this application right. At most 25 entries; each entry says when it applies, what to "
    "do, and why. Return the complete markdown, not a diff."
)
INSTRUCTIONS_BY_STEP: dict[str, str] = {
    "decide": DECIDE_INSTRUCTIONS,
    "ask": ASK_INSTRUCTIONS,
    "reflect": REFLECT_INSTRUCTIONS,
}


def instructions_for(step: str, max_questions: int = MAX_QUESTIONS) -> str:
    """The instruction text for one step. Only the ask step depends on the question cap."""
    if step == "ask":
        return ask_instructions(max_questions)
    return INSTRUCTIONS_BY_STEP[step]


# --------------------------------------------------------------------------- responses


class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore")


class ModifierResponse(_Lenient):
    type: str = Field(description="flat_extra or exclusion")
    detail: str = Field(description="The hazard the modifier applies to, e.g. aviation.")
    amount_per_1000: float | None = Field(default=None, description="flat_extra only: dollars per $1,000 of face.")


class DecideResponse(_Lenient):
    """The rating. ``rating_class`` is null only when the decision is postpone."""

    decision: str = Field(description="accept | accept_with_modification | postpone | decline")
    rating_class: str | None = Field(default=None, description="A class name from the manual, or null for a postpone.")
    modifiers: list[ModifierResponse] = Field(default_factory=list)
    drivers: list[str] = Field(default_factory=list, description="The factors that drove the rating.")
    rationale: str = Field(default="", description="At most 80 words.")

    @field_validator("decision")
    @classmethod
    def _decision_known(cls, value: str) -> str:
        if normalise_decision(value) is None:
            raise ValueError("must be one of accept, accept_with_modification, postpone, decline")
        return value

    @field_validator("rationale")
    @classmethod
    def _rationale_length(cls, value: str) -> str:
        if len(str(value).split()) > MAX_RATIONALE_WORDS:
            raise ValueError(f"at most {MAX_RATIONALE_WORDS} words")
        return value

    def cross_check(self) -> list[str]:
        """Checks the field validators cannot do on their own."""
        errors: list[str] = []
        decision = normalise_decision(self.decision)
        if decision != "postpone" and normalise_class(self.rating_class) is None:
            errors.append("rating_class: a class name from the manual is required unless the decision is postpone")
        for i, m in enumerate(self.modifiers):
            kind = str(m.type).strip().lower().replace("-", "_").replace(" ", "_")
            if kind not in ("flat_extra", "exclusion"):
                errors.append(f"modifiers[{i}].type: must be flat_extra or exclusion")
            elif kind == "flat_extra" and m.amount_per_1000 is None:
                errors.append(f"modifiers[{i}].amount_per_1000: a flat extra needs its band")
        return errors


class AskResponse(_Lenient):
    """Questions for the senior underwriter, capped at the default :data:`MAX_QUESTIONS`.

    A run configured with a different ``max_questions`` gets its own model from
    :func:`ask_response_model`; this is the default-cap case.
    """

    questions: list[str] = Field(default_factory=list, max_length=MAX_QUESTIONS)


class ReflectResponse(_Lenient):
    """The whole rewritten rule book."""

    rulebook_markdown: str = Field(min_length=1)


RESPONSE_MODELS: dict[str, type[BaseModel]] = {
    "decide": DecideResponse,
    "ask": AskResponse,
    "reflect": ReflectResponse,
}


@lru_cache(maxsize=None)
def ask_response_model(max_questions: int = MAX_QUESTIONS) -> type[BaseModel]:
    """The ask-step response model whose ``questions`` cap is ``max_questions``.

    Built rather than hardcoded, so the schema embedded in the request, the instruction
    text and the oracle's limit are all the one configured number.
    """
    n = max(int(max_questions), 0)
    if n == MAX_QUESTIONS:
        return AskResponse
    return create_model(
        f"AskResponse{n}",
        __base__=_Lenient,
        __doc__=f"At most {n} question(s) for the senior underwriter.",
        questions=(list[str], Field(default_factory=list, max_length=n)),
    )


def response_model_for(step: str, max_questions: int = MAX_QUESTIONS) -> type[BaseModel]:
    if step == "ask":
        return ask_response_model(max_questions)
    try:
        return RESPONSE_MODELS[step]
    except KeyError as exc:
        raise KeyError(f"{step!r} is not an operator step; expected one of {STEPS}") from exc


def response_schema_for(step: str, max_questions: int = MAX_QUESTIONS) -> dict:
    return response_model_for(step, max_questions).model_json_schema()


def questions_cap(schema: dict | None) -> int:
    """The question cap an ask request carries, read back out of its response schema.

    The schema is the operator-visible statement of the cap, so anything answering an ask
    request - the stub operator included - can honour the run's configured value without
    being handed it by a second route.
    """
    field = ((schema or {}).get("properties") or {}).get("questions") or {}
    try:
        return int(field["maxItems"])
    except (KeyError, TypeError, ValueError):
        return MAX_QUESTIONS


def validate_response(step: str, raw: object, max_questions: int = MAX_QUESTIONS) -> tuple[dict | None, list[str]]:
    """Validate one operator answer. Returns ``(normalised answer or None, errors)``."""
    from pydantic import ValidationError

    model = response_model_for(step, max_questions) if step in RESPONSE_MODELS else None
    if model is None:
        return None, [f"unknown step {step!r}"]
    if not isinstance(raw, dict):
        return None, ["response must be a JSON object"]
    try:
        parsed = model(**raw)
    except ValidationError as exc:
        return None, [f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
    errors = parsed.cross_check() if isinstance(parsed, DecideResponse) else []
    return (None, errors) if errors else (parsed.model_dump(), [])


# --------------------------------------------------------------------------- the request envelope


class UwRequest(BaseModel):
    """One operator decision, and where its files live. Contains no golden and no rule id."""

    request_id: str
    run_id: str
    condition: str
    phase: str
    case_index: int
    case_id: str
    step: str
    attempt: int = 1
    created_at: str = Field(default_factory=utc_now)
    instructions: str
    payload: dict
    response_schema: dict

    @classmethod
    def build(
        cls,
        *,
        run_id: str,
        condition: str,
        phase: str,
        case_index: int,
        case_id: str,
        step: str,
        attempt: int,
        payload: dict,
        max_questions: int = MAX_QUESTIONS,
    ) -> "UwRequest":
        if step not in STEPS:
            raise ValueError(f"{step!r} is not an operator step; expected one of {STEPS}")
        if condition not in CONDITIONS:
            raise ValueError(f"unknown condition {condition!r}; expected one of {CONDITIONS}")
        if phase not in PHASES:
            raise ValueError(f"unknown phase {phase!r}; expected one of {PHASES}")
        return cls(
            request_id=f"{run_id}:{condition}:{phase}:case{case_index:02d}:{step}:a{attempt}",
            run_id=run_id,
            condition=condition,
            phase=phase,
            case_index=case_index,
            case_id=case_id,
            step=step,
            attempt=attempt,
            instructions=instructions_for(step, max_questions),
            payload=payload,
            response_schema=response_schema_for(step, max_questions),
        )

    def file_stem(self) -> str:
        suffix = "" if self.attempt <= 1 else f"_r{self.attempt}"
        return f"{self.phase}_case{self.case_index:02d}_{self.step}{suffix}"

    def request_path(self, root: Path | str) -> Path:
        return Path(root) / "requests" / self.condition / f"{self.file_stem()}.json"

    def response_path(self, root: Path | str) -> Path:
        return Path(root) / "responses" / self.condition / f"{self.file_stem()}.json"

    def write_request_file(self, root: Path | str) -> Path:
        return atomic_write_json(self.request_path(root), self.model_dump(mode="json"))


# --------------------------------------------------------------------------- graph state


class UwGraphState(TypedDict, total=False):
    # identity and configuration
    run_id: str
    condition: str
    phase: str
    case_index: int
    case_id: str
    case: dict
    manual: str
    memory_root: str
    mode: str
    operator: str
    model_identifier: str
    # working values
    senior_answers: list[dict]
    senior_usage: dict
    answer: dict | None
    answer_invalid: bool
    validation_errors: list[str]
    rerequests: int
    scores: dict | None
    markup: str | None
    rulebook_pending: str | None
    rulebook_version: int | None
    memory_size: int
    nearest_distance: float | None
    request_files: Annotated[list[str], operator.add]
    response_files: Annotated[list[str], operator.add]
    route_history: Annotated[list[str], operator.add]
    status: str


def initial_state(
    *,
    run_id: str,
    condition: str,
    phase: str,
    case: dict,
    manual: str,
    memory_root: str,
    mode: str,
    operator_name: str,
    model_identifier: str,
) -> UwGraphState:
    if condition not in CONDITIONS:
        raise ValueError(f"unknown condition {condition!r}; expected one of {CONDITIONS}")
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; expected one of {PHASES}")
    return UwGraphState(
        run_id=run_id,
        condition=condition,
        phase=phase,
        case_index=int(case["case_index"]),
        case_id=str(case["case_id"]),
        case=case,
        manual=manual,
        memory_root=memory_root,
        mode=mode,
        operator=operator_name,
        model_identifier=model_identifier,
        senior_answers=[],
        senior_usage={},
        answer=None,
        answer_invalid=False,
        validation_errors=[],
        rerequests=0,
        scores=None,
        markup=None,
        rulebook_pending=None,
        rulebook_version=None,
        memory_size=0,
        nearest_distance=None,
        request_files=[],
        response_files=[],
        route_history=[],
        status="running",
    )
