"""Runner mechanics with fakes: stub run-through, manual pause/response/resume across runner instances, freeze check, status snapshot."""
from __future__ import annotations

import json

import pytest

from src.llm_provider import FixtureProvider, ManualProvider, ProviderSettings
from src.run_experiment import RunConfig, Runner, RunnerPaths
from tests.test_graph_routes import FakeLogger, FakeStore, make_services, task_spec


def make_runner(tmp_path, mode, conditions, provider, run_id="r1"):
    paths = RunnerPaths(
        runs_dir=tmp_path / "runs",
        checkpoint_dir=tmp_path / "ckpt",
        status_path=tmp_path / "status.json",
        manual_root=tmp_path / "manual",
        tasks_root=tmp_path / "tasks",
        render_dashboard=False,
    )
    # three tasks so that T2's lesson (applicable to T3 and T4) satisfies the ">= 2 remaining tasks" rule
    tasks = {"T2": task_spec("T2"), "T3": task_spec("T3"), "T4": task_spec("T4")}
    logger, store = FakeLogger(), FakeStore()
    factory = lambda cfg: make_services(provider, store, logger)  # noqa: E731
    config = RunConfig(run_id=run_id, mode=mode, conditions=conditions, task_order=["T2", "T3", "T4"])
    runner = Runner.init(run_id, conditions, mode, config=config, require_freeze=False, services_factory=factory, tasks=tasks, manifest={}, paths=paths)
    return runner, paths, factory, tasks, logger, store


def test_stub_run_completes_all_tasks_and_writes_status(tmp_path):
    runner, paths, *_ = make_runner(tmp_path, "stub", ["skill_learning", "baseline"], FixtureProvider(ProviderSettings(mode="stub")))
    assert runner.advance("skill_learning")["status"] == "done"
    assert runner.advance("baseline")["status"] == "done"
    snap = json.loads(paths.status_path.read_text(encoding="utf-8"))["runs"]["r1"]
    sl, bl = snap["conditions"]["skill_learning"], snap["conditions"]["baseline"]
    assert sl["tasks_completed"] == 3 and sl["status"] == "done" and sl["skills_created"] == 1
    assert sl["first_attempt_pass"] == {"T2": False, "T3": True, "T4": True}
    assert bl["first_attempt_pass"] == {"T2": False, "T3": False, "T4": False}  # baseline never learns across tasks
    assert sl["operator_steps_used"] > 0 and sl["operator_steps_cap"] == 40
    # stub runs record the repo's freeze hash when config/freeze_manifest.json exists, else "unfrozen"
    assert snap["provider"]["provider_mode"] == "stub" and snap["freeze_sha256"] and isinstance(snap["freeze_sha256"], str)
    assert set(sl["scores"]) == {"T2", "T3", "T4"}
    assert sl["median_seconds_per_task"] is not None and sl["eta_label"].startswith("rough ETA")


def test_manual_pause_response_resume_across_runner_instances(tmp_path):
    runner, paths, factory, tasks, logger, _ = make_runner(tmp_path, "manual", ["baseline"], ManualProvider(ProviderSettings(mode="manual")))
    first = runner.advance("baseline")
    assert first["status"] == "waiting_operator"
    request_path = tmp_path.parent / first["pending_request"] if not (tmp_path / "manual").exists() else None
    pending = runner.pending()["baseline"]
    assert pending and pending.endswith("T2_a1_plan_task_1.request.json")
    req_file = next((tmp_path / "manual").rglob("T2_a1_plan_task_1.request.json"))
    request = json.loads(req_file.read_text(encoding="utf-8"))
    assert request["node"] == "plan_task" and request["condition"] == "baseline"
    assert [e["event_type"] for e in logger.graph if e["event_type"].startswith("operator")] == ["operator_request"]

    # a second call without a response changes nothing and does not re-log the request
    assert runner.advance("baseline")["status"] == "waiting_operator"
    assert [e["event_type"] for e in logger.graph if e["event_type"].startswith("operator")] == ["operator_request"]

    # answer via a fresh Runner instance (simulates a new process) using the on-disk checkpoint
    response = {"steps": [{"component": "load_tables"}, {"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}]}
    req_file.with_name("T2_a1_plan_task_1.response.json").write_text(json.dumps(response), encoding="utf-8")
    runner2 = Runner("r1", services_factory=factory, tasks=tasks, manifest={}, paths=paths)
    second = runner2.advance("baseline")
    assert second["status"] == "waiting_operator" and second["pending_request"].endswith("T3_a1_plan_task_1.request.json")
    assert runner2.run["conditions"]["baseline"]["task_results"]["T2"]["passed"] is True
    assert runner2.run["conditions"]["baseline"]["operator_steps_used"] == 1

    # resume() copies a response from elsewhere into place and continues; T4 then needs its own answer
    elsewhere = tmp_path / "answer.json"
    elsewhere.write_text(json.dumps(response), encoding="utf-8")
    third = runner2.resume("baseline", elsewhere)
    assert third["status"] == "waiting_operator" and third["pending_request"].endswith("T4_a1_plan_task_1.request.json")
    fourth = runner2.resume("baseline", elsewhere)
    assert fourth["status"] == "done"
    snap = json.loads(paths.status_path.read_text(encoding="utf-8"))["runs"]["r1"]["conditions"]["baseline"]
    assert snap["tasks_completed"] == 3 and snap["pending_request"] is None
    kinds = [e["event_type"] for e in logger.graph if e["event_type"].startswith("operator")]
    assert kinds == ["operator_request", "operator_response"] * 3


def test_manual_init_requires_frozen_pack(tmp_path, monkeypatch):
    import src.run_experiment as re_mod

    monkeypatch.setattr(re_mod, "FREEZE_MANIFEST_PATH", tmp_path / "freeze_manifest.json")
    paths = RunnerPaths(runs_dir=tmp_path / "runs", checkpoint_dir=tmp_path / "ckpt", status_path=tmp_path / "s.json", manual_root=tmp_path / "m", tasks_root=tmp_path / "t", render_dashboard=False)
    config = RunConfig(run_id="r9", mode="manual", conditions=["baseline"], task_order=["T2"])
    with pytest.raises(SystemExit, match="freeze"):
        Runner.init("r9", ["baseline"], "manual", config=config, paths=paths, tasks={}, manifest={})


def test_duplicate_init_is_refused(tmp_path):
    runner, paths, factory, tasks, *_ = make_runner(tmp_path, "stub", ["baseline"], FixtureProvider(ProviderSettings(mode="stub")))
    with pytest.raises(SystemExit, match="already exists"):
        Runner.init("r1", ["baseline"], "stub", config=runner.config, require_freeze=False, services_factory=factory, tasks=tasks, manifest={}, paths=paths)


# --------------------------------------------------------------------------- experiment 5 (D-23)


def test_feedback_memory_seed_redacts_every_number_but_task_ids_and_quantiles(tmp_path):
    from src.feedback_memory import FeedbackMemory, redact_record

    note = {"task_id": "T2", "task_title": "Claims portfolio description", "criterion": "correctness",
            "text": "denial rate 1,286 / 12,339 = 10.42 % on T2, p90", "detail": "outside [0.6, 0.95]: roc_auc = 0.9967"}
    redacted, replaced = redact_record({**note, "source_run": "run_006"})
    assert redacted["text"] == "denial rate [n] / [n] = [n] on T2, p90"
    assert redacted["detail"] == "outside [[n], [n]]: roc_auc = [n]"
    assert replaced == 6  # three numbers in the text, three in the detail
    assert redacted["task_title"] == note["task_title"]  # only text and detail are rewritten

    memory = FeedbackMemory(tmp_path, "run_007", "feedback_memory")
    assert memory.seed([redacted]) == 1
    assert memory.seed([]) == 0
    stored = memory.read_all()
    assert len(stored) == 1 and stored[0]["seeded_from"] == "run_006"
    assert stored[0]["text"] == "denial rate [n] / [n] = [n] on T2, p90"
    # a seeded note is recalled like any other, and its own task is still excluded
    assert [r["task_id"] for r in memory.recall("T9")] == ["T2"]
    assert memory.recall("T2") == []


def test_seed_audit_catches_a_planted_golden_number_and_passes_on_clean_input(tmp_path, monkeypatch):
    import json as _json

    import scripts.seed_audit as audit_mod
    from src.feedback_memory import redact_record

    golden = {"task_id": "T9", "built_at": "2026-09-08T00:00:00+00:00", "data_sha256": {"medical_claims.csv": "9f" * 32},
              "expected_exact": {"denial_code_ranking.codes": [{"code": "CO-15", "n": 241, "share": 0.187402799377916}]},
              "expected_metrics": {"rate": {"value": 0.1101900525677315, "tolerance": 1e-06}},
              "contracts": {"min_group_size": 30}, "metric_ranges": {}, "prohibited_fields": [], "required_caveats": []}
    goldens = tmp_path / "goldens"
    goldens.mkdir()
    (goldens / "T9_denial_hotspots_metrics.json").write_text(_json.dumps(golden), encoding="utf-8")
    logs, memory, skills = tmp_path / "logs", tmp_path / "memory", tmp_path / "skills"
    (logs / "runs").mkdir(parents=True)
    (memory / "run_x").mkdir(parents=True)
    (skills / "evolved" / "run_w").mkdir(parents=True)
    (logs / "runs" / "run_x.json").write_text(_json.dumps({"run_id": "run_x", "config": {"seed_from_run": "run_w"},
                                                           "seeding": {"source_run": "run_w", "skills": {"excluded_skill_ids": []}}}), encoding="utf-8")
    monkeypatch.setattr(audit_mod, "GOLDENS_DIR", goldens)
    monkeypatch.setattr(audit_mod, "LOGS_DIR", logs)
    monkeypatch.setattr(audit_mod, "MEMORY_ROOT", memory)
    monkeypatch.setattr(audit_mod, "SKILLS_DIR", skills)

    def write_notes(*texts):
        lines = []
        for t in texts:
            record, _ = redact_record({"task_id": "T2", "text": t, "detail": None, "source_run": "run_w"})
            lines.append(_json.dumps({**record, "seeded_from": "run_w"}))
        (memory / "run_x" / "feedback_memory.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")

    skill_file = skills / "evolved" / "run_w" / "evolved_run_w_001_v1.md"
    # clean: the note's numbers are redacted and the skill only states a convention
    write_notes("denial rate 1,286 / 12,339 = 10.42 % on T2")
    skill_file.write_text("# skill\n\nUse adjudicated claims as the denominator and record the choice.\n", encoding="utf-8")
    assert audit_mod.audit("run_x", ["T9"]) == 0

    # a golden value planted in a seed skill is caught (skill files are seeded verbatim, never redacted)
    skill_file.write_text("# skill\n\nThe top denial code CO-15 covers 241 of the denials.\n", encoding="utf-8")
    assert audit_mod.audit("run_x", ["T9"]) == 1

    # so is a number that survived the redaction of a seeded note
    skill_file.write_text("# skill\n\nUse adjudicated claims as the denominator.\n", encoding="utf-8")
    (memory / "run_x" / "feedback_memory.jsonl").write_text(
        _json.dumps({"task_id": "T2", "text": "the rate was 0.110190", "seeded_from": "run_w"}) + "\n", encoding="utf-8")
    assert audit_mod.audit("run_x", ["T9"]) == 1

    # a missing holdout golden is a failure, not a silent pass
    assert audit_mod.audit("run_x", ["T5"]) == 1
