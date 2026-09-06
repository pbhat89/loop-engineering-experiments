"""Graph route tests with injected fakes: per-condition routing, retries, skill lifecycle, manual interrupts, caps."""
from __future__ import annotations

import copy

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from src.claims_graph import build_claims_skill_graph, compiled_edges, designed_topology
from src.graph_nodes import Services, validate_plan
from src.graph_state import initial_state
from src.llm_provider import FixtureProvider, ManualProvider, ProviderSettings

DIMS = ("correctness", "completeness", "reproducibility", "statistical_discipline", "communication")


def task_spec(task_id: str) -> dict:
    return {
        "task_id": task_id,
        "title": f"Task {task_id}",
        "objective": "Describe denial rates with explicit denominators.",
        "tags": ["descriptive", "rates"],
        "input_tables": ["medical_claims"],
        "required_artifacts": ["report.md"],
        "golden_file": f"goldens/{task_id}.json",
        "components": [
            {"id": "load_tables", "default_selected": True, "params": {}},
            {
                "id": "denial_rate",
                "default_selected": False,
                "params": {"denominator": {"options": ["all_claims", "adjudicated_claims"], "default": "all_claims"}},
            },
            {"id": "write_report", "default_selected": True, "params": {}},
        ],
    }


GOLDEN = {"expected_metrics": {"denial_rate": {"value": 0.1, "tolerance": 1e-9}}}


def fake_execute(spec: dict, plan: dict, ctx: dict) -> dict:
    metrics: dict = {}
    steps = {s["component"]: s.get("params", {}) for s in plan["steps"]}
    if "denial_rate" in steps:
        denominator = steps["denial_rate"].get("denominator")
        metrics["denial_rate"] = {"value": 0.1 if denominator == "adjudicated_claims" else 0.08, "denominator_definition": denominator}
    return {
        "status": "ok",
        "task_id": spec["task_id"],
        "attempt": ctx["attempt"],
        "output_dir": ctx["output_dir"],
        "artifacts": [f"{ctx['output_dir']}/report.md"],
        "metrics": metrics,
        "components_executed": list(steps),
        "components_failed": [],
        "errors": [],
        "seed": ctx["seed"],
        "duration_seconds": 0.01,
    }


def fake_evaluate(spec: dict, result: dict, rubric: dict, golden: dict) -> dict:
    metric = (result.get("metrics") or {}).get("denial_rate")
    ok = bool(metric) and abs(metric["value"] - golden["expected_metrics"]["denial_rate"]["value"]) <= 1e-9
    score = 4.0 if ok else 2.0
    feedback = (
        []
        if ok
        else [
            {
                "feedback_id": f"{spec['task_id']}-denial_rate_value",
                "criterion": "correctness",
                "issue_type": "wrong_denominator",
                "severity": "high",
                "remediation": "Use adjudicated claims (Paid, Denied, Adjusted) as the denominator and state it.",
                "related_components": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
                "reusable": True,
                "applicable_task_ids": ["T3", "T4"],
            }
        ]
    )
    return {
        "evaluator_version": "test",
        "rubric_version": "test",
        "scores": {d: score for d in DIMS},
        "score_total": score,
        "passed": ok,
        "checks": [
            {
                "check_id": f"{spec['task_id']}.denial_rate_value",
                "dimension": "correctness",
                "weight": 2,
                "critical": True,
                "passed": ok,
                "observed": metric["value"] if metric else None,
                "expected": 0.1,
                "detail": "",
            }
        ],
        "feedback": feedback,
    }


class FakeLogger:
    def __init__(self):
        self.graph, self.skill, self.feedback, self.experiment = [], [], [], []

    def log_graph_event(self, r):
        self.graph.append(r)

    def log_skill_event(self, r):
        self.skill.append(r)

    def log_feedback_event(self, r):
        self.feedback.append(r)

    def log_experiment_event(self, r):
        self.experiment.append(r)


class FakeStore:
    def __init__(self):
        self.skills: list[dict] = []
        self.reuse: list[tuple[str, str]] = []

    def list_skills(self):
        return list(self.skills)

    def retrieve(self, spec, current_task_index, k=6):
        out = []
        for s in self.skills:
            if s["kind"] == "evolved" and s["created_after_task_index"] >= current_task_index:
                continue
            out.append({**s, "score": 1.0, "matched_terms": ["rates"]})
        return out[:k]

    def render_for_operator(self, skills):
        return [{k: s[k] for k in ("skill_id", "name", "kind", "version", "tags", "sections")} for s in skills]

    def persist(self, proposal, provenance):
        skill = {
            "skill_id": f"evolved_test_{len(self.skills) + 1:03d}",
            "name": proposal["name"],
            "kind": "evolved",
            "version": 1,
            "tags": proposal.get("tags", []),
            "sections": {k: proposal.get(k) for k in ("trigger", "objective", "procedure", "required_checks")},
            "created_after_task_index": provenance["created_after_task_index"],
            "path": f"skills/evolved/test/{proposal['name']}_v1.md",
        }
        self.skills.append(skill)
        return skill

    def record_reuse(self, skill_id, task_id):
        self.reuse.append((skill_id, task_id))


def fake_validate(proposal, existing, task_id, remaining):
    duplicate = next((e for e in existing if (e.get("name") if isinstance(e, dict) else getattr(e, "name", None)) == proposal["name"]), None)
    decision = "rejected" if duplicate else "accepted"
    return {
        "decision": decision,
        "checks": [{"check_id": "duplicate", "passed": duplicate is None, "detail": ""}],
        "reasons": ["duplicate"] if duplicate else [],
        "duplicate_of": duplicate["skill_id"] if duplicate else None,
        "similarity": 1.0 if duplicate else 0.0,
    }


def make_services(provider, store=None, logger=None) -> Services:
    return Services(
        provider=provider,
        execute_task=fake_execute,
        evaluate=fake_evaluate,
        skill_store=store or FakeStore(),
        validate_skill=fake_validate,
        logger=logger or FakeLogger(),
        rubric={"rubric_version": "test"},
        load_golden=lambda spec: copy.deepcopy(GOLDEN),
        manifest_summary={"tables": {"medical_claims": {"rows": 10, "columns": [{"name": "claim_status", "dtype": "str"}]}}, "relationships": []},
    )


def make_state(condition, task_id="T2", task_index=1, remaining=("T3", "T4"), **over):
    kwargs = dict(
        run_id="run_t",
        condition=condition,
        task_id=task_id,
        task_index=task_index,
        task_spec=task_spec(task_id),
        dataset_manifest={},
        seed=42,
        output_dir=f"artifacts/tasks/run_t/{condition}/{task_id}",
        golden_path=f"goldens/{task_id}.json",
        freeze_sha256="test-freeze",
        max_retries=2,
        pass_threshold=3.5,
        max_operator_steps=40,
        remaining_task_ids=list(remaining),
        provider_mode="stub",
        operator="deterministic-fixture",
        model_identifier="deterministic-fixture-v1",
    )
    kwargs.update(over)
    return initial_state(**kwargs)


def stub() -> FixtureProvider:
    return FixtureProvider(ProviderSettings(mode="stub"))


# --------------------------------------------------------------------------- tests


def test_validate_plan_normalises_and_reports_errors():
    spec = task_spec("T2")
    plan, errors = validate_plan({"steps": [{"component": "denial_rate"}]}, spec)
    assert errors == [] and plan["steps"][0]["params"] == {"denominator": "all_claims"}
    _, errors = validate_plan({"steps": [{"component": "nope"}, {"component": "denial_rate", "params": {"denominator": "x"}}]}, spec)
    assert any("unknown component" in e for e in errors) and any("not in options" in e for e in errors)
    _, errors = validate_plan({"steps": []}, spec)
    assert errors and errors[0].startswith("schema")


def test_baseline_retries_without_reflection_and_stops_when_passed():
    logger = FakeLogger()
    graph = build_claims_skill_graph(make_services(stub(), logger=logger))
    out = graph.invoke(make_state("baseline"))
    assert out["route_history"] == [
        "load_context", "plan_task", "execute_task", "evaluate_output", "revise_plan", "execute_task", "evaluate_output", "finalize_task",
    ]
    assert out["status"] == "done" and out["stop_reason"] == "passed" and out["retry_count"] == 1
    assert out["evaluation"]["passed"] and out["execution_attempts"] == 2
    assert [e["status"] for e in logger.experiment] == ["attempt", "attempt", "done"]
    assert logger.experiment[-1]["first_attempt_passed"] is False and logger.experiment[-1]["skills_created"] == []
    assert logger.skill == []
    assert any(e["event"] == "feedback_incorporated" for e in logger.feedback)


def test_reflection_only_reflects_before_revising_and_persists_nothing():
    logger = FakeLogger()
    store = FakeStore()
    out = build_claims_skill_graph(make_services(stub(), store, logger)).invoke(make_state("reflection_only"))
    assert out["route_history"][4:6] == ["reflect_on_feedback", "revise_plan"]
    assert "propose_skill" not in out["route_history"] and store.skills == []
    assert out["reflection"]["reusable_lessons"]


def test_retry_budget_exhausted_finalizes_with_reason():
    services = make_services(stub())
    services.evaluate = lambda spec, result, rubric, golden: {**fake_evaluate(spec, result, rubric, {"expected_metrics": {"denial_rate": {"value": 0.99}}}), "feedback": []}
    out = build_claims_skill_graph(services).invoke(make_state("baseline"))
    assert out["stop_reason"] == "retry_budget_exhausted" and out["retry_count"] == 2 and out["execution_attempts"] == 3


def test_skill_learning_creates_then_reuses_a_skill():
    store, logger = FakeStore(), FakeLogger()
    graph = build_claims_skill_graph(make_services(stub(), store, logger))

    first = graph.invoke(make_state("skill_learning", task_id="T2", task_index=1, remaining=("T3", "T4")))
    assert first["route_history"] == [
        "load_context", "retrieve_skills", "plan_task", "execute_task", "evaluate_output", "reflect_on_feedback", "revise_plan",
        "execute_task", "evaluate_output", "reflect_on_feedback", "propose_skill", "validate_skill", "persist_skill", "finalize_task",
    ]
    assert first["skills_created"] == ["evolved_test_001"] and len(store.skills) == 1
    events = [e["event"] for e in logger.skill]
    assert events == ["skill_proposed", "skill_validated", "skill_persisted"]

    second = graph.invoke(make_state("skill_learning", task_id="T3", task_index=2, remaining=("T4",)))
    assert second["retrieved_skills"][0]["skill_id"] == "evolved_test_001"
    assert second["execution_attempts"] == 1 and second["evaluation"]["passed"]
    assert second["route_history"][-4:] == ["propose_skill", "validate_skill", "finalize_task"][-3:] or second["route_history"][-1] == "finalize_task"
    final = logger.experiment[-1]
    assert final["first_attempt_passed"] is True and final["skills_reused"] == ["evolved_test_001"]
    assert store.reuse == [("evolved_test_001", "T3")]
    assert any(e["event"] == "skill_reused" for e in logger.skill)
    assert any(e["event"] == "skill_proposal_skipped" for e in logger.skill)


def test_foundational_only_uses_curated_skills_but_never_learns():
    store, logger = FakeStore(), FakeLogger()
    store.skills.append(
        {
            "skill_id": "foundational_003",
            "name": "descriptive_summary",
            "kind": "foundational",
            "version": 1,
            "tags": ["rates"],
            "sections": {"required_checks": ["denial_rate.denominator=adjudicated_claims and state it"]},
            "created_after_task_index": -1,
            "path": "skills/foundational/03_descriptive_summary.md",
        }
    )
    graph = build_claims_skill_graph(make_services(stub(), store, logger))
    out = graph.invoke(make_state("foundational_only"))
    assert out["route_history"] == ["load_context", "retrieve_skills", "plan_task", "execute_task", "evaluate_output", "finalize_task"]
    assert out["evaluation"]["passed"] and out["skills_created"] == []
    assert logger.experiment[-1]["skills_reused"] == ["foundational_003"]
    # evolved skills are invisible to the control even when the store has them
    store.persist({"name": "evolved_thing", "tags": []}, {"created_after_task_index": 0})
    again = graph.invoke(make_state("foundational_only", task_id="T3", task_index=2, remaining=("T4",)))
    assert [s["skill_id"] for s in again["retrieved_skills"]] == ["foundational_003"]


def test_skill_not_retrievable_in_same_task_index():
    store = FakeStore()
    store.persist({"name": "x", "tags": []}, {"created_after_task_index": 1})
    assert store.retrieve(task_spec("T2"), 1) == []
    assert store.retrieve(task_spec("T3"), 2)


def test_manual_mode_interrupts_validates_and_resumes():
    logger = FakeLogger()
    services = make_services(ManualProvider(ProviderSettings(mode="manual")), logger=logger)
    graph = build_claims_skill_graph(services, checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "run_t:baseline:T2"}}
    state = make_state("baseline", provider_mode="manual", operator="claude-code-subagent", model_identifier="claude-fable-5-1")

    paused = graph.invoke(state, config=cfg)
    request = paused["__interrupt__"][0].value
    assert request["node"] == "plan_task" and request["seq"] == 1
    assert request["payload"]["component_catalogue"][1]["id"] == "denial_rate"
    assert "retrieved_skills" not in request["payload"]  # baseline never sees skills
    assert request["response_schema"]["properties"]["steps"]

    again = graph.invoke(Command(resume={"steps": [{"component": "bogus"}]}), config=cfg)
    retry = again["__interrupt__"][0].value
    assert retry["seq"] == 2 and retry["payload"]["validation_errors"][0].startswith("unknown component")

    done = graph.invoke(
        Command(resume={"steps": [{"component": "load_tables"}, {"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}], "rationale": "ok"}),
        config=cfg,
    )
    assert "__interrupt__" not in done and done["status"] == "done" and done["evaluation"]["passed"]
    assert done["operator_steps_used"] == 2  # one invalid + one valid answer
    assert graph.get_state(cfg).next == ()


def test_operator_cap_uses_defaults_without_interrupting():
    services = make_services(ManualProvider(ProviderSettings(mode="manual")))
    graph = build_claims_skill_graph(services, checkpointer=MemorySaver())
    out = graph.invoke(make_state("skill_learning", max_operator_steps=0), config={"configurable": {"thread_id": "cap"}})
    assert "__interrupt__" not in out and out["status"] == "done"
    assert out["stop_reason"] == "operator_cap" and out["retry_count"] == 0
    assert out["analysis_plan"]["rationale"] == "catalogue defaults"


def test_designed_topology_matches_compiled_graph():
    graph = build_claims_skill_graph(make_services(stub()))
    designed = {(e["source"], e["target"]) for e in designed_topology()["edges"]}
    assert designed == compiled_edges(graph)


def test_graph_yaml_mirrors_designed_topology_and_experiment_config():
    from src.utils import CONFIG_DIR, read_yaml

    doc = read_yaml(CONFIG_DIR / "graph.yaml")
    designed = designed_topology()
    assert doc["nodes"] == designed["nodes"]
    assert {(e["source"], e["target"], e["label"]) for e in doc["edges"]} == {(e["source"], e["target"], e["label"]) for e in designed["edges"]}
    assert doc["per_condition"] == designed["per_condition"]
    assert set(doc["llm_decision_nodes"]) == {"plan_task", "revise_plan", "reflect_on_feedback", "propose_skill", "revise_skill_proposal"}
    experiment = read_yaml(CONFIG_DIR / "experiment.yaml")
    assert doc["termination"]["max_retries"] == experiment["max_retries"]
    assert doc["termination"]["max_operator_steps_per_condition"] == experiment["max_operator_steps_per_condition"]
