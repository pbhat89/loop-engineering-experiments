"""Experiment 7: the reviewer markup - correct answer, material factors, no point values."""
from __future__ import annotations

from src.underwriting.cases import build_dataset
from src.underwriting.engine import rate_manual_only
from src.underwriting.markup import build_markup, forbidden_digits
from src.underwriting.scorer import score_answer


def _pairs():
    cases, goldens = build_dataset()
    return list(zip(cases, goldens))


def answer_from(answer) -> dict:
    """An engine answer shaped like an operator response."""
    return {
        "decision": answer.decision,
        "rating_class": answer.rating_class,
        "modifiers": [dict(m) for m in answer.modifiers],
        "drivers": list(answer.drivers),
        "rationale": "",
    }


# --------------------------------------------------------------------------- markup


def test_no_markup_carries_a_digit_beyond_the_case_id_and_the_class_names():
    for case, golden in _pairs():
        naive = answer_from(rate_manual_only(case))
        for answer in (naive, None, {"decision": "decline", "rating_class": "Decline", "drivers": []}):
            scores = score_answer(answer, golden, unparseable=answer is None)
            text = build_markup(golden, answer, scores)
            assert forbidden_digits(text) == [], f"{golden['case_id']}: {text}"


def test_a_correct_answer_gets_a_one_line_confirmation_naming_the_material_factors():
    for _case, golden in _pairs():
        answer = {
            "decision": golden["decision"],
            "rating_class": golden["rating_class"],
            "modifiers": golden["modifiers"],
            "drivers": golden["drivers"],
        }
        scores = score_answer(answer, golden)
        text = build_markup(golden, answer, scores)
        assert text.startswith(f"{golden['case_id']}: correct.")
        assert "\n" not in text


def test_a_wrong_clean_case_is_told_the_manual_covered_it():
    for case, golden in _pairs():
        if golden["tier"] != "clean":
            continue
        wrong = {"decision": "decline", "rating_class": "Decline", "modifiers": [], "drivers": []}
        text = build_markup(golden, wrong, score_answer(wrong, golden))
        assert "The manual covers this case" in text
        assert "band was misread" in text
        break


def test_a_wrong_rated_case_carries_the_practice_sentence_for_every_rule_that_fired():
    from src.underwriting.house_rules import RULES_BY_ID

    for case, golden in _pairs():
        if not golden["fired_rule_ids"]:
            continue
        naive = answer_from(rate_manual_only(case))
        scores = score_answer(naive, golden)
        if scores["decision_match"] and scores["ladder_distance"] == 0:
            continue
        text = build_markup(golden, naive, scores)
        for rule_id in golden["fired_rule_ids"]:
            assert RULES_BY_ID[rule_id].markup_sentence in text, f"{golden['case_id']} missing {rule_id}"


def test_direction_words_follow_the_sign_of_the_distance():
    golden = {"case_id": "UW-T99", "decision": "accept", "rating_class": "Table 2",
              "modifiers": [], "drivers": ["build"], "fired_rule_ids": []}
    too_severe = {"decision": "accept", "rating_class": "Table 6", "drivers": []}
    too_lenient = {"decision": "accept", "rating_class": "Standard", "drivers": []}
    assert "too severe" in build_markup(golden, too_severe, score_answer(too_severe, golden))
    assert "too lenient" in build_markup(golden, too_lenient, score_answer(too_lenient, golden))
