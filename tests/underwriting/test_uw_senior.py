"""Experiment 7: the ask-a-senior oracle answers narrowly and literally."""
from __future__ import annotations

from src.underwriting.cases import build_dataset
from src.underwriting.engine import rule_relevance
from src.underwriting.house_rules import ORACLE_FALLBACK, RULES_BY_ID
from src.underwriting.manual import manual_sections
from src.underwriting.senior import answer_question, answer_questions, for_request, usage


def _case_firing(rule_id: str) -> dict:
    cases, goldens = build_dataset()
    for case, golden in zip(cases, goldens):
        if rule_id in golden["fired_rule_ids"]:
            return case
    raise AssertionError(f"no case fires {rule_id}")


def _clean_case() -> dict:
    cases, goldens = build_dataset()
    for case, golden in zip(cases, goldens):
        if golden["tier"] == "clean":
            return case
    raise AssertionError("no clean case")


def test_a_well_aimed_question_about_a_relevant_rule_returns_the_rule_verbatim():
    case = _case_firing("HR-01")
    answer = answer_question("How do I charge a treated blood pressure that is controlled?", case)
    assert answer["source"] == "senior"
    assert answer["rule_id"] == "HR-01"
    assert answer["answer"] == RULES_BY_ID["HR-01"].statement


def test_the_same_question_on_an_irrelevant_case_falls_back_to_the_manual():
    case = _clean_case()
    assert "HR-01" not in rule_relevance(case)
    answer = answer_question("How do I charge a treated blood pressure that is controlled?", case)
    assert answer["source"] == "manual"
    assert answer["rule_id"] is None
    assert manual_sections()["Blood pressure"] in answer["answer"]


def test_a_manual_topic_question_returns_the_manual_section_and_wastes_the_question():
    case = _clean_case()
    answer = answer_question("What are the BMI bands for build?", case)
    assert answer["source"] == "manual"
    assert manual_sections()["Build"] in answer["answer"]


def test_a_question_the_senior_cannot_place_gets_the_flat_refusal():
    case = _clean_case()
    answer = answer_question("Should we write this on a level or decreasing basis?", case)
    assert answer["source"] == "none"
    assert answer["answer"] == ORACLE_FALLBACK


def test_the_senior_knows_the_held_out_rules_too():
    case = _case_firing("HR-14")
    answer = answer_question("How is scuba rated at that depth, with cave penetration?", case)
    assert answer["rule_id"] == "HR-14"
    assert answer["answer"] == RULES_BY_ID["HR-14"].statement


def test_at_most_four_questions_are_answered_and_blanks_are_dropped():
    case = _case_firing("HR-01")
    answers = answer_questions(["a?", "  ", "b?", "c?", "d?", "e?"], case)
    assert len(answers) == 4
    assert all(a["question"].strip() for a in answers)


def test_the_request_view_hides_the_rule_id():
    case = _case_firing("HR-02")
    answers = answer_questions(["How is private aviation rated?"], case)
    shown = for_request(answers)
    assert shown == [{"question": answers[0]["question"], "answer": answers[0]["answer"]}]
    assert all("rule_id" not in entry for entry in shown)


def test_usage_counts_what_the_questions_bought():
    case = _case_firing("HR-02")
    answers = answer_questions(
        ["How is private aviation rated?", "What are the BMI bands?", "Is the sky blue?"], case
    )
    counts = usage(answers)
    assert counts["questions_asked"] == 3
    assert counts["answers_from_senior"] == 1
    assert counts["answers_from_manual"] == 1
    assert counts["answers_unavailable"] == 1
    assert counts["rule_ids_revealed"] == ["HR-02"]


def test_four_questions_cannot_cover_a_compound_case_by_accident():
    """The oracle answers what was asked, nothing more - one question, one rule at most."""
    case = _case_firing("HR-04")
    answers = answer_questions(["Is there an interaction charge when cardiac factors combine?"], case)
    assert len([a for a in answers if a["rule_id"]]) == 1
