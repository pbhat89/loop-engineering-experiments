"""Experiment 7: the graph routes, the stub end-to-end run, the runner protocol and the leakage audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.underwriting.audit import audit_run, hidden_point_values, statement_fragments
from src.underwriting.data import goldens_by_case_id, load_cases, load_manual
from src.underwriting.graph import (
    NODES,
    build_underwriting_graph,
    compiled_edges,
    designed_topology,
    route_after_load,
    route_after_markup,
)
from src.underwriting.house_rules import ALL_RULE_IDS, RULES_BY_ID
from src.underwriting.nodes import Services
from src.underwriting.state import CONDITIONS, UwRequest, initial_state, validate_response
from src.underwriting.stub import build_stub_provider

REPO_ROOT = Path(__file__).resolve().parents[2]
SMOKE_ARCHIVE = REPO_ROOT / "archive" / "experiment-7_stub_smoke"


# --------------------------------------------------------------------------- helpers


def run_arm(root: Path, condition: str, phase: str, n_cases: int, style: str = "learner") -> list[dict]:
    records: list[dict] = []
    services = Services(
        provider=build_stub_provider(style, transcript_root=root),
        manual=load_manual(),
        goldens=goldens_by_case_id(),
        run_root=root,
        log=lambda condition_, record: records.append(record),
    )
    graph = build_underwriting_graph(services)
    for case in load_cases(phase)[:n_cases]:
        graph.invoke(
            initial_state(
                run_id="uw_test",
                condition=condition,
                phase=phase,
                case=case,
                manual=services.manual,
                memory_root=str(root),
                mode="stub",
                operator_name="stub",
                model_identifier="deterministic-learner-v1",
            )
        )
    return records


# --------------------------------------------------------------------------- routing


def test_the_compiled_graph_matches_the_designed_topology():
    services = Services(provider=build_stub_provider(), manual="", goldens={}, run_root=Path("."))
    graph = build_underwriting_graph(services)
    designed = {(e["source"], e["target"]) for e in designed_topology()["edges"]}
    assert compiled_edges(graph) == designed
    assert set(designed_topology()["nodes"]) == set(NODES)


@pytest.mark.parametrize("condition", CONDITIONS)
def test_only_the_asking_arm_visits_ask_senior(condition):
    assert route_after_load({"condition": condition}) == ("ask_senior" if condition == "ask_senior" else "decide")


@pytest.mark.parametrize("condition", CONDITIONS)
def test_only_written_rules_reflects_and_only_while_training(condition):
    train = route_after_markup({"condition": condition, "phase": "train"})
    holdout = route_after_markup({"condition": condition, "phase": "holdout"})
    assert train == ("reflect" if condition == "written_rules" else "update_memory")
    assert holdout == "update_memory"


@pytest.mark.parametrize("condition", CONDITIONS)
def test_each_arm_walks_its_designed_path(tmp_path, condition):
    root = tmp_path / condition
    services = Services(
        provider=build_stub_provider("learner", transcript_root=root),
        manual=load_manual(),
        goldens=goldens_by_case_id(),
        run_root=root,
    )
    graph = build_underwriting_graph(services)
    case = load_cases("train")[0]
    result = graph.invoke(
        initial_state(
            run_id="uw_test", condition=condition, phase="train", case=case, manual=services.manual,
            memory_root=str(root), mode="stub", operator_name="stub", model_identifier="stub",
        )
    )
    assert result["route_history"] == designed_topology()["per_condition"][condition]
    assert result["status"] == "done"


# --------------------------------------------------------------------------- end to end


@pytest.mark.parametrize("condition", CONDITIONS)
def test_stub_end_to_end_train_then_holdout(tmp_path, condition):
    root = tmp_path / condition
    train = run_arm(root, condition, "train", 6)
    held = run_arm(root, condition, "holdout", 2)
    assert len(train) == 6 and len(held) == 2
    for record in train + held:
        assert record["ladder_distance"] is not None
        assert record["unparseable"] is False
        assert "tier" not in record, "the tier is joined in at analysis time, never logged"
    if condition == "ask_senior":
        assert sum(r["questions_asked"] for r in train) > 0
    else:
        assert sum(r["questions_asked"] for r in train) == 0


def test_the_held_out_phase_writes_nothing_to_memory(tmp_path):
    root = tmp_path / "notebook"
    run_arm(root, "notebook", "train", 4)
    before = (root / "notebook" / "markups.jsonl").read_text(encoding="utf-8")
    run_arm(root, "notebook", "holdout", 3)
    after = (root / "notebook" / "markups.jsonl").read_text(encoding="utf-8")
    assert before == after
    assert len(before.strip().splitlines()) == 4


def test_the_held_out_phase_shows_no_markup(tmp_path):
    root = tmp_path / "new_joiner"
    run_arm(root, "new_joiner", "holdout", 3)
    for path in (root / "requests").rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "markup" not in text


def test_the_naive_stub_never_learns_and_the_learner_does(tmp_path):
    naive = run_arm(tmp_path / "naive", "notebook", "train", 30, style="naive")
    learner = run_arm(tmp_path / "learner", "notebook", "train", 30, style="learner")
    naive_mean = sum(r["ladder_distance"] for r in naive) / len(naive)
    learner_mean = sum(r["ladder_distance"] for r in learner) / len(learner)
    assert learner_mean < naive_mean
    assert sum(r["ladder_distance"] for r in learner[-5:]) <= sum(r["ladder_distance"] for r in naive[-5:])


def test_the_written_rules_arm_rewrites_its_book_each_training_case(tmp_path):
    root = tmp_path / "written_rules"
    run_arm(root, "written_rules", "train", 6)
    history = sorted((root / "written_rules" / "history").glob("v*.md"))
    assert len(history) == 6
    assert (root / "written_rules" / "rulebook.md").read_text(encoding="utf-8").strip()


def test_the_precedent_arm_files_every_training_case_and_logs_the_nearest_distance(tmp_path):
    root = tmp_path / "precedent"
    records = run_arm(root, "precedent", "train", 6)
    filed = (root / "precedent" / "filed_cases.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(filed) == 6
    assert records[0]["nearest_distance"] is None
    assert records[-1]["nearest_distance"] is not None


# --------------------------------------------------------------------------- the leakage audit


@pytest.mark.parametrize("condition", CONDITIONS)
def test_no_request_file_the_stub_smoke_writes_leaks_anything(tmp_path, condition):
    root = tmp_path / condition
    run_arm(root, condition, "train", 6)
    run_arm(root, condition, "holdout", 2)
    markups = {}
    notebook = root / "notebook" / "markups.jsonl"
    if notebook.exists():
        for line in notebook.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                markups[record["case_id"]] = record["markup"]
    problems = audit_run(root, goldens_by_case_id(), markups)
    assert problems == [], problems
    assert len(list((root / "requests").rglob("*.json"))) > 0


def test_every_archived_smoke_request_is_clean():
    if not SMOKE_ARCHIVE.exists():  # pragma: no cover - the archive is committed with phase (b)
        pytest.skip("stub smoke archive not present")
    run_dirs = [p.parent for p in SMOKE_ARCHIVE.rglob("requests") if p.is_dir()]
    assert run_dirs, "the archived smoke has no requests/ directory"
    for root in run_dirs:
        markups = {}
        notebook = root / "notebook" / "markups.jsonl"
        if notebook.exists():
            for line in notebook.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    record = json.loads(line)
                    markups[record["case_id"]] = record["markup"]
        assert audit_run(root, goldens_by_case_id(), markups) == []


def test_the_audit_catches_a_planted_leak(tmp_path):
    from src.underwriting.audit import audit_payload

    base = {"run_id": "r", "condition": "notebook", "phase": "train", "case_index": 1, "case_id": "UW-T01",
            "step": "decide", "payload": {"case": {"rendered": "x"}, "manual": "m"}}
    assert audit_payload(base) == []
    assert audit_payload({**base, "payload": {**base["payload"], "tier": "compound"}})
    assert audit_payload({**base, "payload": {**base["payload"], "note": "see HR-04"}})
    assert audit_payload({**base, "payload": {**base["payload"], "note": RULES_BY_ID["HR-04"].statement}})
    assert audit_payload({**base, "payload": {**base["payload"], "note": "judgement"}})
    assert audit_payload({**base, "payload": {**base["payload"], "fired_rule_ids": []}})


def test_hidden_point_values_are_numbers_the_manual_never_prints():
    hidden = hidden_point_values()
    assert hidden, "no hidden-only numbers found; the audit would be toothless"
    manual = load_manual()
    for token in hidden:
        assert token not in manual


def test_every_rule_statement_has_a_fragment_the_markup_does_not_share():
    fragments = statement_fragments()
    assert set(fragments) == set(ALL_RULE_IDS)
    for rule_id, fragment in fragments.items():
        assert fragment.lower() not in RULES_BY_ID[rule_id].markup_sentence.lower(), rule_id
        assert fragment.lower() in RULES_BY_ID[rule_id].statement.lower()


# --------------------------------------------------------------------------- response validation


def test_a_valid_decide_response_passes():
    parsed, errors = validate_response(
        "decide",
        {"decision": "accept with modification", "rating_class": "Table 4",
         "modifiers": [{"type": "flat_extra", "detail": "aviation", "amount_per_1000": 2.5}],
         "drivers": ["build"], "rationale": "short"},
    )
    assert errors == [] and parsed["rating_class"] == "Table 4"


@pytest.mark.parametrize(
    "body",
    [
        {"decision": "maybe", "rating_class": "Table 4"},
        {"decision": "accept"},
        {"decision": "accept", "rating_class": "Table 3"},
        {"decision": "accept", "rating_class": "Standard", "rationale": " ".join(["word"] * 81)},
        {"decision": "accept", "rating_class": "Standard", "modifiers": [{"type": "flat_extra", "detail": "aviation"}]},
    ],
)
def test_bad_decide_responses_are_rejected(body):
    parsed, errors = validate_response("decide", body)
    assert parsed is None and errors


def test_a_postpone_needs_no_rating_class():
    parsed, errors = validate_response("decide", {"decision": "postpone", "rating_class": None})
    assert errors == [] and parsed["rating_class"] is None


def test_ask_and_reflect_responses():
    assert validate_response("ask", {"questions": ["a", "b"]})[1] == []
    assert validate_response("ask", {"questions": ["a"] * 5})[0] is None
    assert validate_response("reflect", {"rulebook_markdown": "# Book"})[1] == []
    assert validate_response("reflect", {"rulebook_markdown": ""})[0] is None


def test_request_file_names_follow_the_protocol():
    request = UwRequest.build(
        run_id="uw_001", condition="notebook", phase="train", case_index=7, case_id="UW-T07",
        step="decide", attempt=1, payload={},
    )
    assert request.request_path("root").as_posix().endswith("root/requests/notebook/train_case07_decide.json")
    assert request.response_path("root").as_posix().endswith("root/responses/notebook/train_case07_decide.json")
    retry = UwRequest.build(
        run_id="uw_001", condition="notebook", phase="holdout", case_index=2, case_id="UW-H02",
        step="decide", attempt=3, payload={},
    )
    assert retry.file_stem() == "holdout_case02_decide_r3"
