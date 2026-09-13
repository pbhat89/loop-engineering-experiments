"""Experiment 7: the manual, the two engines and the scorer."""
from __future__ import annotations

import pytest

from src.underwriting import manual as manual_mod
from src.underwriting.cases import build_dataset
from src.underwriting.engine import (
    NO_RULES,
    modifier_key,
    rate,
    rate_house,
    rate_manual_only,
    tier_for,
)
from src.underwriting.house_rules import ALL_RULE_IDS, HOUSE_RULES, RULES_BY_ID
from src.underwriting.scorer import (
    driver_scores,
    ladder_distance,
    modifier_scores,
    normalise_class,
    normalise_decision,
    normalise_driver,
    score_answer,
    trailing_mean,
)
from src.underwriting.tables import (
    A1C_BANDS,
    ALCOHOL_TREATMENT_DEBITS,
    AVIATION_DEFAULT_DEBITS,
    BP_TREATMENT_DEBITS,
    BUILD_BANDS,
    CLIMBING_DEBITS,
    DEBIT_BANDS,
    DIASTOLIC_BANDS,
    DUI_DEBITS,
    LADDER,
    LIPID_RATIO_BANDS,
    LIVER_ENZYME_DEBITS,
    MVR_VIOLATION_BANDS,
    SCUBA_DEPTH_BANDS,
    SLEEP_APNEA_DEBITS,
    SYSTOLIC_BANDS,
    TOBACCO_DEBITS,
    TOTAL_CHOLESTEROL_BANDS,
    class_for_debits,
)


# --------------------------------------------------------------------------- the manual matches the tables


def test_manual_prints_every_band_table_verbatim():
    text = manual_mod.build_manual()
    rendered = {
        "build": manual_mod.render_bands(BUILD_BANDS, manual_mod.fmt_one_dp),
        "systolic": manual_mod.render_bands(SYSTOLIC_BANDS),
        "diastolic": manual_mod.render_bands(DIASTOLIC_BANDS),
        "total cholesterol": manual_mod.render_bands(TOTAL_CHOLESTEROL_BANDS),
        "lipid ratio": manual_mod.render_bands(LIPID_RATIO_BANDS, manual_mod.fmt_one_dp),
        "a1c": manual_mod.render_bands(A1C_BANDS, manual_mod.fmt_one_dp),
        "scuba": manual_mod.render_bands(SCUBA_DEPTH_BANDS, unit=" ft"),
        "mvr": manual_mod.render_bands(MVR_VIOLATION_BANDS),
    }
    for name, block in rendered.items():
        assert block in text, f"the manual does not print the {name} table as the engine reads it"


def test_manual_prints_every_scalar_and_class_name():
    text = manual_mod.build_manual()
    for value in (
        BP_TREATMENT_DEBITS, AVIATION_DEFAULT_DEBITS, CLIMBING_DEBITS, DUI_DEBITS,
        LIVER_ENZYME_DEBITS, ALCOHOL_TREATMENT_DEBITS, SLEEP_APNEA_DEBITS,
        TOBACCO_DEBITS["quit_1_5y"], TOBACCO_DEBITS["current"],
    ):
        assert str(value) in text
    for low, high, name in DEBIT_BANDS:
        assert name in text
        assert str(low) in text
    for name in LADDER:
        assert name in text


def test_manual_is_ascii_and_about_nine_hundred_words():
    text = manual_mod.build_manual()
    assert text.isascii(), "the manual must survive a cp1252 console"
    assert 800 <= manual_mod.word_count(text) <= 1150


def test_manual_names_a_gap_for_every_hidden_rule_area_without_naming_the_rule():
    text = manual_mod.build_manual()
    assert text.count("refer to underwriting judgement") >= 10
    for rule in HOUSE_RULES:
        assert rule.statement not in text
        assert rule.rule_id not in text


# --------------------------------------------------------------------------- the two engines


def test_manual_only_ignores_every_house_rule():
    cases, _ = build_dataset()
    for case in cases:
        assert rate_manual_only(case).to_record() == rate(case, NO_RULES).to_record()


def test_clean_cases_have_manual_only_equal_to_the_golden():
    cases, goldens = build_dataset()
    for case, golden in zip(cases, goldens):
        if golden["tier"] != "clean":
            continue
        assert rate_manual_only(case).outcome() == rate_house(case).outcome(), golden["case_id"]


def test_fired_rules_are_exactly_the_rules_that_change_the_answer():
    cases, goldens = build_dataset()
    for case, golden in zip(cases, goldens):
        house = rate_house(case)
        for rule_id in ALL_RULE_IDS:
            without = rate(case, frozenset(ALL_RULE_IDS) - {rule_id})
            changed = without.outcome() != house.outcome()
            assert changed == (rule_id in golden["fired_rule_ids"]), f"{golden['case_id']} {rule_id}"


def test_tier_is_read_off_the_fired_count():
    assert tier_for([]) == "clean"
    assert tier_for(["HR-01"]) == "judgement"
    assert tier_for(["HR-01", "HR-02"]) == "compound"
    assert tier_for(["HR-01", "HR-02", "HR-03"]) == "compound"
    assert tier_for(["HR-01", "HR-02", "HR-03", "HR-04"]) is None


def test_a_decline_band_declines_whatever_the_total():
    case = _minimal_case()
    case.update({"a1c": 9.4})
    answer = rate_house(case)
    assert answer.decision == "decline" and answer.rating_class == "Decline"


def test_nicotine_positive_lab_overrides_a_declared_never():
    case = _minimal_case()
    case["nicotine_lab"] = "positive"
    assert rate_house(case).debits.get("tobacco") == TOBACCO_DEBITS["current"]


def test_debit_bands_map_to_classes():
    assert class_for_debits(0) == "Standard"
    assert class_for_debits(49) == "Standard"
    assert class_for_debits(50) == "Table 2"
    assert class_for_debits(249) == "Table 8"
    assert class_for_debits(250) == "Decline"


# --------------------------------------------------------------------------- the scorer


def test_ladder_distance_counts_steps():
    assert ladder_distance("accept", "Standard", "accept", "Standard") == 0
    assert ladder_distance("accept", "Table 2", "accept", "Standard") == 1
    assert ladder_distance("accept", "Preferred Plus", "decline", "Decline") == len(LADDER) - 1


def test_postpone_sits_off_the_ladder():
    assert ladder_distance("postpone", None, "postpone", None) == 0
    assert ladder_distance("postpone", None, "accept", "Table 6") == 2
    assert ladder_distance("accept", "Table 6", "postpone", None) == 2
    assert ladder_distance("accept", "Standard", "postpone", None) == 2


def test_class_and_decision_aliases_are_accepted():
    assert normalise_class("Std+") == "Standard Plus"
    assert normalise_class("tab 4") == "Table 4"
    assert normalise_class(None) is None
    assert normalise_decision("accept with modification") == "accept_with_modification"
    assert normalise_decision("Declined") == "decline"
    assert normalise_decision("nonsense") is None


def test_modifier_f1_counts_the_band():
    golden = [{"type": "flat_extra", "detail": "aviation", "amount_per_1000": 2.50}]
    exact = modifier_scores([{"type": "flat_extra", "detail": "aviation", "amount_per_1000": 2.5}], golden)
    assert exact["f1"] == 1.0
    wrong_band = modifier_scores([{"type": "flat_extra", "detail": "aviation", "amount_per_1000": 5.0}], golden)
    assert wrong_band["f1"] == 0.0
    assert modifier_scores([], [])["f1"] == 1.0


def test_driver_recall_uses_synonyms():
    scores = driver_scores(["BMI", "HbA1c", "cholesterol ratio"], ["build", "A1c", "lipid ratio"])
    assert scores["recall"] == 1.0
    assert normalise_driver("private pilot") == "aviation"
    assert normalise_driver("on treatment") == "blood pressure treatment"


def test_an_unparseable_answer_scores_the_postpone_equivalent_and_is_flagged():
    golden = {"decision": "accept", "rating_class": "Table 2", "modifiers": [], "drivers": ["build"]}
    scores = score_answer(None, golden, unparseable=True)
    assert scores["ladder_distance"] == 2 and scores["unparseable"] is True
    assert scores["driver"]["recall"] == 0.0


def test_trailing_mean_uses_what_is_available_so_far():
    assert trailing_mean([2.0, 0.0, 1.0], window=5) == [2.0, 1.0, 1.0]
    assert trailing_mean([1, 1, 1, 1, 1, 0], window=5)[-1] == 0.8


def test_modifier_key_is_stable():
    assert modifier_key({"type": "exclusion", "detail": "climbing"}) == "exclusion|climbing"
    assert modifier_key({"type": "flat_extra", "detail": "aviation", "amount_per_1000": 2.5}) == "flat_extra|2.50|aviation"


# --------------------------------------------------------------------------- helpers


def _minimal_case() -> dict:
    return {
        "case_id": "UW-X01", "case_index": 1, "phase": "train", "sex": "M", "age": 40,
        "product": "20-year term", "face_amount": 500_000, "height_in": 70, "weight_lb": 165, "bmi": 23.7,
        "weight_change_lb_12mo": 0, "tobacco_declared": "never", "nicotine_lab": "negative",
        "bp_systolic": 120, "bp_diastolic": 78, "bp_treated": False, "bp_treatment_since": None,
        "total_cholesterol": 190, "hdl": 55, "lipid_ratio": 3.5, "a1c": 5.4, "diabetes_dx_year": None,
        "diabetes_medication": None, "family_history": [], "occupation": "pharmacist", "occupation_class": "A",
        "avocation": {"type": "none"}, "mvr_violations": 0, "dui_year": None, "liver_enzymes": "normal",
        "alcohol_treatment": False, "sleep_apnea": False, "cpap_compliant": False, "annual_income": 150_000,
        "inforce_coverage": 0, "irrelevant_detail": "keeps bees at an allotment",
    }


@pytest.mark.parametrize("rule_id", ALL_RULE_IDS)
def test_every_rule_has_a_numberless_markup_and_a_spoken_statement(rule_id):
    from src.underwriting.markup import forbidden_digits

    rule = RULES_BY_ID[rule_id]
    assert forbidden_digits(rule.markup_sentence) == [], f"{rule_id} markup carries a number"
    assert rule.statement and rule.statement != rule.markup_sentence
    assert rule.oracle_keywords, f"{rule_id} has no oracle keywords"
