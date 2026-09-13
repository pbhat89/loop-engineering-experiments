"""The two deterministic stub operators. Smoke tests only - never a reported result.

``naive``
    Answers with :func:`src.underwriting.engine.rate_manual_only` every time: a careful
    reader of the starter manual who has learned nothing. This is the new joiner's floor.

``learner``
    Reads its memory block and its senior answers, switches on any house rule whose
    markup sentence or spoken statement it can find there, and rates with those. With an
    empty memory block it is exactly ``naive``, which is what makes the five arms
    comparable in a stub run: the arms differ only in what reaches the memory block.

Neither stub reads a golden. The learner is an *upper* bound on what an arm's memory
could deliver, not a prediction of what a model will do.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.underwriting.provider import BaseProvider, ProviderSettings
from src.underwriting.engine import rate, rate_manual_only
from src.underwriting.house_rules import HOUSE_RULES
from src.underwriting.memory import EMPTY_RULEBOOK
from src.underwriting.state import MAX_QUESTIONS, questions_cap
from src.utils import atomic_write_json

STUB_OPERATORS: tuple[str, ...] = ("naive", "learner")


def answer_from(answer) -> dict:
    """An engine :class:`Answer` as an operator response."""
    return {
        "decision": answer.decision,
        "rating_class": answer.rating_class,
        "modifiers": [
            {"type": m["type"], "detail": m["detail"], "amount_per_1000": m.get("amount_per_1000")}
            for m in answer.modifiers
        ],
        "drivers": list(answer.drivers),
        "rationale": "Rated from the manual tables and whatever practice this file was given.",
    }


def _known_rules(payload: dict) -> set[str]:
    """House rules whose wording the operator can find in what it was handed."""
    text = json.dumps(
        {"memory": payload.get("memory"), "senior_answers": payload.get("senior_answers")},
        ensure_ascii=False,
        default=str,
    ).lower()
    known = set()
    for rule in HOUSE_RULES:
        if rule.markup_sentence.lower() in text or rule.statement.lower() in text:
            known.add(rule.rule_id)
    return known


# --------------------------------------------------------------------------- questions

# (predicate over the case, question). Order is the priority order; the first
# MAX_QUESTIONS whose predicate holds are asked.
QUESTION_BANK: tuple[tuple[str, str], ...] = (
    ("bp_treated", "How is blood pressure that is treated and now controlled charged?"),
    ("aviation", "How is private aviation rated for a low-hours private pilot?"),
    ("older_family", "Does the family-history charge still apply for an applicant of this age?"),
    ("diabetes", "Is there any allowance for type 2 diabetes diagnosed late with a controlled A1c?"),
    ("class_c_avocation", "Occupation class C alongside a hazardous avocation - exclusion rider or flat extra?"),
    ("lipids_disagree", "The total cholesterol band and the ratio band disagree - which one governs?"),
    ("big_face", "The face amount is large relative to income - how should that be handled?"),
    ("weight_loss", "The applicant has lost weight this year - does that change the build band?"),
    ("recent_dui", "There is a recent DUI on the record - how is that treated?"),
    ("cpap", "Sleep apnea with documented CPAP compliance - is there still a debit?"),
    ("mild_liver", "Mildly elevated liver enzymes with no alcohol history - any debit?"),
    ("cardiac_stack", "Several cardiac risk factors appear together - is there an interaction charge?"),
    ("scuba", "How is scuba rated at this depth?"),
    ("always", "Which build band governs this BMI?"),
)


def _flags(case: dict) -> dict[str, bool]:
    from src.underwriting.engine import rate_house
    from src.underwriting.house_rules import qualifying_family_events

    av = str((case.get("avocation") or {}).get("type") or "none")
    house = rate_house(case)
    return {
        "bp_treated": bool(case.get("bp_treated")),
        "aviation": av == "aviation",
        "older_family": int(case["age"]) > 58 and bool(qualifying_family_events(case)),
        "diabetes": case.get("diabetes_dx_year") is not None,
        "class_c_avocation": case.get("occupation_class") == "C" and av != "none",
        "lipids_disagree": True,
        "big_face": float(case["face_amount"]) >= 1_000_000,
        "weight_loss": float(case.get("weight_change_lb_12mo") or 0) < 0,
        "recent_dui": case.get("dui_year") is not None,
        "cpap": bool(case.get("sleep_apnea")),
        "mild_liver": str(case.get("liver_enzymes") or "normal") != "normal",
        "cardiac_stack": "cardiac risk interaction" in house.drivers or len(house.drivers) >= 4,
        "scuba": av == "scuba",
        "always": True,
    }


def stub_questions(case: dict, limit: int = MAX_QUESTIONS) -> list[str]:
    flags = _flags(case)
    return [q for key, q in QUESTION_BANK if flags.get(key)][:limit]


# --------------------------------------------------------------------------- the provider


class UwStubProvider(BaseProvider):
    """Answers every operator step deterministically. ``operator_style`` is naive or learner.

    When ``transcript_root`` is set the provider writes the same request and response files a
    manual-mode run would leave behind, so the leakage audit has something to audit and the
    smoke run archives like a real one.
    """

    def __init__(
        self,
        settings: ProviderSettings | None = None,
        operator_style: str = "learner",
        transcript_root: Path | str | None = None,
    ):
        super().__init__(settings or ProviderSettings(mode="stub"))
        if operator_style not in STUB_OPERATORS:
            raise ValueError(f"unknown stub operator {operator_style!r}; expected one of {STUB_OPERATORS}")
        self.operator_style = operator_style
        self.model_identifier = f"deterministic-{operator_style}-v1"
        self.operator = f"stub-{operator_style}"
        self.transcript_root = Path(transcript_root) if transcript_root else None

    def decide(self, request) -> dict:
        if self.transcript_root is not None:
            request.write_request_file(self.transcript_root)
        answer = self._answer(request)
        if self.transcript_root is not None:
            atomic_write_json(request.response_path(self.transcript_root), answer)
        return answer

    def _answer(self, request) -> dict:
        payload = request.payload
        case = (payload.get("case") or {}).get("fields") or {}
        if request.step == "ask":
            # The cap is read back out of the request's own response schema, so the stub
            # honours the run's configured ``max_questions`` instead of the module default.
            limit = questions_cap(request.response_schema)
            return {"questions": stub_questions(case, limit) if self.operator_style == "learner" else []}
        if request.step == "reflect":
            return {"rulebook_markdown": self._rulebook(payload)}
        if self.operator_style == "naive":
            return answer_from(rate_manual_only(case))
        return answer_from(rate(case, frozenset(_known_rules(payload))))

    @staticmethod
    def _rulebook(payload: dict) -> str:
        context = payload.get("reflection_context") or {}
        existing = str((payload.get("memory") or {}).get("rulebook_markdown") or EMPTY_RULEBOOK)
        markup = str(context.get("markup") or "")
        lines = [
            f"- {rule.markup_sentence}"
            for rule in HOUSE_RULES
            if rule.markup_sentence.lower() in markup.lower() and rule.markup_sentence.lower() not in existing.lower()
        ]
        if not lines:
            return existing
        head = existing if existing.strip() != EMPTY_RULEBOOK.strip() else "# House rule book\n"
        return head.rstrip() + "\n" + "\n".join(lines) + "\n"


def build_stub_provider(operator_style: str = "learner", transcript_root: Path | str | None = None) -> UwStubProvider:
    return UwStubProvider(ProviderSettings(mode="stub"), operator_style=operator_style, transcript_root=transcript_root)
