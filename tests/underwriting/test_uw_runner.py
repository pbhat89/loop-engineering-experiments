"""Experiment 7: the manual-mode request/response file protocol and the runner's book-keeping."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.underwriting import run as runner
from src.underwriting.data import goldens_by_case_id
from src.utils import read_jsonl

VALID = {
    "decision": "accept",
    "rating_class": "Standard",
    "modifiers": [],
    "drivers": ["build"],
    "rationale": "Rated from the manual.",
}


def _config(tmp_path: Path) -> dict:
    return {
        "artifacts_root": str(tmp_path),
        "mode": "manual",
        "operator": "claude-code-subagent",
        "model_identifier": "claude-fable-5-1",
        "max_rerequests": 2,
        "precedent_k": 3,
        "poll_interval_seconds": 0.01,
        "poll_timeout_seconds": 1,
    }


def _write(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body), encoding="utf-8")


def test_manual_mode_pauses_with_a_request_file_and_resumes_from_the_response(tmp_path):
    config = _config(tmp_path)
    root = tmp_path / "uw_t"

    result = runner.advance("uw_t", "new_joiner", "train", config=config, quiet=True)
    assert result["status"] == "waiting_operator"
    request_path = root / "requests" / "new_joiner" / "train_case01_decide.json"
    assert request_path.exists()
    assert not (root / "responses" / "new_joiner" / "train_case01_decide.json").exists()
    assert runner.load_run_state(root)["arms"]["new_joiner"]["train"]["cases_done"] == 0

    _write(root / "responses" / "new_joiner" / "train_case01_decide.json", VALID)
    result = runner.advance("uw_t", "new_joiner", "train", config=config, max_cases=1, quiet=True)
    assert runner.load_run_state(root)["arms"]["new_joiner"]["train"]["cases_done"] == 1
    records = read_jsonl(root / "new_joiner" / "cases.jsonl")
    assert len(records) == 1 and records[0]["case_id"] == "UW-T01"
    assert records[0]["unparseable"] is False

    # the next case asks for its own request file
    runner.advance("uw_t", "new_joiner", "train", config=config, quiet=True)
    assert (root / "requests" / "new_joiner" / "train_case02_decide.json").exists()


def test_an_invalid_response_is_re_requested_with_the_errors_attached(tmp_path):
    config = _config(tmp_path)
    root = tmp_path / "uw_t"
    runner.advance("uw_t", "notebook", "train", config=config, quiet=True)
    _write(root / "responses" / "notebook" / "train_case01_decide.json", {"decision": "maybe"})
    runner.advance("uw_t", "notebook", "train", config=config, quiet=True)

    retry = root / "requests" / "notebook" / "train_case01_decide_r2.json"
    assert retry.exists()
    payload = json.loads(retry.read_text(encoding="utf-8"))["payload"]
    assert payload["validation_errors"], "the re-request must tell the operator what was wrong"
    assert read_jsonl(root / "notebook" / "cases.jsonl") == []


def test_three_invalid_responses_score_the_case_as_unparseable_and_flag_it(tmp_path):
    config = _config(tmp_path)
    root = tmp_path / "uw_t"
    for stem in ("train_case01_decide", "train_case01_decide_r2", "train_case01_decide_r3"):
        runner.advance("uw_t", "new_joiner", "train", config=config, max_cases=1, quiet=True)
        _write(root / "responses" / "new_joiner" / f"{stem}.json", {"decision": "maybe"})
    runner.advance("uw_t", "new_joiner", "train", config=config, max_cases=1, quiet=True)

    records = read_jsonl(root / "new_joiner" / "cases.jsonl")
    assert len(records) == 1
    assert records[0]["unparseable"] is True
    assert records[0]["ladder_distance"] == 2
    assert records[0]["rerequests"] == 2


def test_the_ask_arm_asks_before_it_decides(tmp_path):
    config = _config(tmp_path)
    root = tmp_path / "uw_t"
    runner.advance("uw_t", "ask_senior", "train", config=config, quiet=True)
    ask_request = root / "requests" / "ask_senior" / "train_case01_ask.json"
    assert ask_request.exists()
    assert "senior_answers" not in json.loads(ask_request.read_text(encoding="utf-8"))["payload"]

    _write(root / "responses" / "ask_senior" / "train_case01_ask.json",
           {"questions": ["How is private aviation rated?"]})
    runner.advance("uw_t", "ask_senior", "train", config=config, quiet=True)
    decide_request = root / "requests" / "ask_senior" / "train_case01_decide.json"
    payload = json.loads(decide_request.read_text(encoding="utf-8"))["payload"]
    assert isinstance(payload["senior_answers"], list)
    assert all(set(entry) == {"question", "answer"} for entry in payload["senior_answers"])


def test_a_stub_run_records_the_freeze_and_the_provider(tmp_path):
    config = {**_config(tmp_path), "mode": "stub"}
    runner.advance("uw_s", "new_joiner", "train", mode="stub", config=config, max_cases=2, quiet=True)
    state = runner.load_run_state(tmp_path / "uw_s")
    assert state["provider"]["provider_mode"] == "stub"
    assert len(state["freeze_sha256"]) == 64
    records = read_jsonl(tmp_path / "uw_s" / "new_joiner" / "cases.jsonl")
    assert all(r["freeze_sha256"] == state["freeze_sha256"] for r in records)


def test_the_arms_are_independent_within_one_run(tmp_path):
    config = {**_config(tmp_path), "mode": "stub"}
    for condition in ("new_joiner", "notebook"):
        runner.advance("uw_s", condition, "train", mode="stub", config=config, max_cases=3, quiet=True)
    state = runner.load_run_state(tmp_path / "uw_s")
    assert set(state["arms"]) == {"new_joiner", "notebook"}
    assert all(state["arms"][c]["train"]["cases_done"] == 3 for c in state["arms"])
    assert (tmp_path / "uw_s" / "checkpoints" / "new_joiner_train.sqlite").exists()
    assert (tmp_path / "uw_s" / "checkpoints" / "notebook_train.sqlite").exists()


def test_the_runner_audit_reads_every_request_file(tmp_path):
    config = {**_config(tmp_path), "mode": "stub"}
    runner.advance("uw_s", "notebook", "train", mode="stub", config=config, max_cases=4, quiet=True)
    assert runner.audit("uw_s", config) == []


def test_unknown_arms_and_phases_are_refused(tmp_path):
    config = _config(tmp_path)
    with pytest.raises(SystemExit):
        runner.advance("uw_t", "no_such_arm", "train", config=config, quiet=True)
    with pytest.raises(SystemExit):
        runner.advance("uw_t", "new_joiner", "no_such_phase", config=config, quiet=True)


def test_the_goldens_are_only_read_after_the_answer(tmp_path):
    """No request payload ever carries a golden; the audit over a live manual run proves it."""
    config = _config(tmp_path)
    root = tmp_path / "uw_t"
    runner.advance("uw_t", "precedent", "train", config=config, quiet=True)
    request = json.loads((root / "requests" / "precedent" / "train_case01_decide.json").read_text(encoding="utf-8"))
    golden = goldens_by_case_id()[request["case_id"]]
    text = json.dumps(request)
    assert golden["tier"] not in text
    for rule_id in golden["fired_rule_ids"]:
        assert rule_id not in text
