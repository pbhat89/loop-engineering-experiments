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
    assert snap["provider"]["provider_mode"] == "stub" and snap["freeze_sha256"] == "unfrozen"
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
