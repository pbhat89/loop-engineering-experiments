"""The ask-a-senior oracle: deterministic code, not a model.

A senior answers **narrowly and literally**. For each question, in order:

1. If a house rule's keyword sets are all present *and* that rule is relevant to the
   case in hand, the senior says the rule out loud - numbers included, because a senior
   would. The senior knows the held-out rules too.
2. Otherwise, if the question hits a topic the manual already covers, the senior reads
   that section of the manual back. The question was wasted: it was in the manual all
   along, which is the point of this arm.
3. Otherwise: "Not something I can answer from here; use the manual."

Knowing what to ask is itself the expertise this arm lacks. The question cap (four by
default, ``max_questions`` in config/underwriting.yaml) cannot cover fourteen house rules,
and a compound case fires three at once.
"""
from __future__ import annotations

from src.underwriting.engine import rule_relevance
from src.underwriting.house_rules import HOUSE_RULES, MANUAL_TOPIC_KEYWORDS, ORACLE_FALLBACK
from src.underwriting.manual import manual_sections
from src.underwriting.state import MAX_QUESTIONS  # one definition of the default cap, in state.py

SOURCE_RULE = "senior"
SOURCE_MANUAL = "manual"
SOURCE_NONE = "none"


def answer_question(question: str, case: dict, relevant: set[str] | None = None) -> dict:
    """One answer. ``rule_id`` is for the run log only - it never reaches a request payload."""
    text = str(question or "").strip()
    relevant = rule_relevance(case) if relevant is None else relevant
    if text:
        for rule in HOUSE_RULES:
            if rule.rule_id in relevant and rule.matches_question(text):
                return {"question": text, "answer": rule.statement, "source": SOURCE_RULE, "rule_id": rule.rule_id}
        sections = manual_sections()
        lowered = text.lower()
        for title, keywords in MANUAL_TOPIC_KEYWORDS.items():
            if title in sections and any(k in lowered for k in keywords):
                return {
                    "question": text,
                    "answer": f"That is in the manual, under {title}. " + sections[title],
                    "source": SOURCE_MANUAL,
                    "rule_id": None,
                }
    return {"question": text, "answer": ORACLE_FALLBACK, "source": SOURCE_NONE, "rule_id": None}


def answer_questions(questions: list[str] | None, case: dict, limit: int = MAX_QUESTIONS) -> list[dict]:
    """At most ``limit`` answers, in the order asked. Blank questions are dropped."""
    asked = [str(q).strip() for q in (questions or []) if str(q).strip()][: max(int(limit), 0)]
    relevant = rule_relevance(case)
    return [answer_question(q, case, relevant) for q in asked]


def for_request(answers: list[dict]) -> list[dict]:
    """The senior's answers as the operator sees them - question and answer, nothing else."""
    return [{"question": a["question"], "answer": a["answer"]} for a in answers]


def usage(answers: list[dict]) -> dict:
    """What the run log records about one round of questions."""
    return {
        "questions_asked": len(answers),
        "answers_from_senior": sum(1 for a in answers if a["source"] == SOURCE_RULE),
        "answers_from_manual": sum(1 for a in answers if a["source"] == SOURCE_MANUAL),
        "answers_unavailable": sum(1 for a in answers if a["source"] == SOURCE_NONE),
        "rule_ids_revealed": [a["rule_id"] for a in answers if a["rule_id"]],
    }
