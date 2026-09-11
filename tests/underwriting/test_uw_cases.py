"""Experiment 7: the seeded case pack, the derived schedule and the freeze."""
from __future__ import annotations

from src.underwriting.cases import (
    HELDOUT_CASES,
    TRAINING_CASES,
    TRAINING_CLEAN_COUNT,
    TRAINING_COMPOUND_TARGETS,
    TRAINING_JUDGEMENT_TARGETS,
    WINDOW,
    WINDOW_CLEAN,
    WINDOW_COMPOUND,
    WINDOW_JUDGEMENT,
    CASE_FIELDS,
    build_dataset,
    operator_fields,
    render_case,
    sanity,
)
from src.underwriting.data import (
    build_freeze_manifest,
    load_cases,
    load_goldens,
    load_house_rules,
    load_manual,
    verify_freeze,
    verify_regeneration,
)
from src.underwriting.house_rules import HELDOUT_ONLY_RULE_IDS, TRAINING_RULE_IDS
from src.underwriting.manual import build_manual

TRAINING_RULES = list(TRAINING_RULE_IDS)


def _dataset():
    return build_dataset()


def test_the_generator_is_deterministic():
    first_cases, first_goldens = build_dataset()
    second_cases, second_goldens = build_dataset()
    assert first_cases == second_cases
    assert first_goldens == second_goldens


def test_the_schedule_holds():
    cases, goldens = _dataset()
    assert sanity(cases, goldens) == []


def test_case_counts_and_tier_counts():
    _, goldens = _dataset()
    train = [g for g in goldens if g["phase"] == "train"]
    held = [g for g in goldens if g["phase"] == "holdout"]
    assert len(train) == TRAINING_CASES and len(held) == HELDOUT_CASES
    tiers = [g["tier"] for g in train]
    assert tiers.count("clean") == TRAINING_CLEAN_COUNT
    assert tiers.count("judgement") == len(TRAINING_JUDGEMENT_TARGETS)
    assert tiers.count("compound") == len(TRAINING_COMPOUND_TARGETS)
    assert tiers[0] != "clean", "case 1 must not be clean"


def test_the_mix_is_constant_across_every_window_of_ten():
    _, goldens = _dataset()
    tiers = [g["tier"] for g in goldens if g["phase"] == "train"]
    for start in range(0, len(tiers) - WINDOW + 1):
        window = tiers[start : start + WINDOW]
        assert WINDOW_CLEAN[0] <= window.count("clean") <= WINDOW_CLEAN[1], start
        assert WINDOW_JUDGEMENT[0] <= window.count("judgement") <= WINDOW_JUDGEMENT[1], start
        assert WINDOW_COMPOUND[0] <= window.count("compound") <= WINDOW_COMPOUND[1], start


def test_every_training_rule_fires_at_least_three_times_in_at_least_two_shapes():
    _, goldens = _dataset()
    train = [g for g in goldens if g["phase"] == "train"]
    shapes: dict[str, list[frozenset]] = {}
    for g in train:
        fired = set(g["fired_rule_ids"])
        for rule_id in fired:
            shapes.setdefault(rule_id, []).append(frozenset(fired - {rule_id}))
    for rule_id in TRAINING_RULES:
        assert len(shapes.get(rule_id, [])) >= 3, f"{rule_id} fires in fewer than three training cases"
        assert len(set(shapes[rule_id])) >= 2, f"{rule_id} fires in fewer than two shapes"


def test_the_held_out_rules_never_fire_in_training_and_fire_twice_in_the_held_out_set():
    _, goldens = _dataset()
    train_fired = {r for g in goldens if g["phase"] == "train" for r in g["fired_rule_ids"]}
    assert not (train_fired & set(HELDOUT_ONLY_RULE_IDS))
    held = [g for g in goldens if g["phase"] == "holdout"]
    novel = [g for g in held if set(g["fired_rule_ids"]) & set(HELDOUT_ONLY_RULE_IDS)]
    assert len(novel) == 2
    assert {r for g in novel for r in g["fired_rule_ids"]} == set(HELDOUT_ONLY_RULE_IDS)


def test_held_out_tier_counts():
    _, goldens = _dataset()
    tiers = [g["tier"] for g in goldens if g["phase"] == "holdout"]
    assert tiers.count("clean") == 2
    assert tiers.count("judgement") == 4
    assert tiers.count("compound") == 2


def test_every_case_renders_without_a_golden_field_and_carries_an_irrelevant_detail():
    cases, goldens = _dataset()
    by_id = {g["case_id"]: g for g in goldens}
    for case in cases:
        text = render_case(case)
        assert text.isascii()
        assert 70 <= len(text.split()) <= 200
        assert case["irrelevant_detail"] in text
        golden = by_id[case["case_id"]]
        assert golden["tier"] not in text
        for rule_id in golden["fired_rule_ids"]:
            assert rule_id not in text
        assert set(operator_fields(case)) <= set(CASE_FIELDS)
        assert "tier" not in operator_fields(case)


def test_the_frozen_files_match_the_code_that_generated_them():
    assert verify_regeneration() == []


def test_the_freeze_manifest_matches_what_is_on_disk():
    digest, drift = verify_freeze()
    assert drift == []
    assert digest == build_freeze_manifest(write=False)["freeze_sha256"]


def test_the_data_pack_loads():
    assert load_manual() == build_manual()
    assert len(load_house_rules()) == len(TRAINING_RULES) + len(HELDOUT_ONLY_RULE_IDS)
    assert len(load_cases("train")) == TRAINING_CASES
    assert len(load_cases("holdout")) == HELDOUT_CASES
    assert len(load_goldens()) == TRAINING_CASES + HELDOUT_CASES


def test_goldens_never_reach_the_case_file():
    cases = load_cases()
    for case in cases:
        assert "tier" not in case
        assert "fired_rule_ids" not in case
        assert "decision" not in case
        assert "rating_class" not in case
