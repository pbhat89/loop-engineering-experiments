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
    assert set(doc["llm_decision_nodes"]) == {"plan_task", "revise_plan", "reflect_on_feedback", "propose_skill", "revise_skill_proposal", "self_evaluate"}
    experiment = read_yaml(CONFIG_DIR / "experiment.yaml")
    assert doc["termination"]["max_retries"] == experiment["max_retries"]
    assert doc["termination"]["max_operator_steps_per_condition"] == experiment["max_operator_steps_per_condition"]


# --------------------------------------------------------------------------- experiment 3 (D-21)


def test_self_refine_never_sees_the_evaluator_and_stops_on_its_own_verdict():
    from src.llm_provider import FixtureProvider, ProviderSettings

    logger = FakeLogger()
    services = make_services(FixtureProvider(ProviderSettings(mode="stub")), logger=logger)
    graph = build_claims_skill_graph(services, checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "run_t:self_refine:T2"}}
    out = graph.invoke(make_state("self_refine", max_retries=4), config=cfg)
    # fixture: revise once, then accept - the frozen evaluator scores both attempts but never routes
    assert out["route_history"] == [
        "load_context", "plan_task", "execute_task", "evaluate_output", "self_evaluate", "revise_plan",
        "execute_task", "evaluate_output", "self_evaluate", "finalize_task",
    ]
    assert out["stop_reason"] == "self_accepted" and out["self_evaluation"]["verdict"] == "accept"
    assert len(out["self_evaluation_history"]) == 2 and len(out["evaluation_history"]) == 2
    done = logger.experiment[-1]
    assert done["self_declared_pass"] is True and done["passed"] in (True, False) and done["score_by_attempt"] and done["stop_reason"] == "self_accepted"
    # the self-review feedback was logged with its source; no evaluator feedback was ever issued to this condition
    sources = {e.get("source") for e in logger.feedback if e.get("event") == "feedback_issued"}
    assert sources == {"self"}


def test_self_refine_manual_requests_carry_no_evaluator_information():
    services = make_services(ManualProvider(ProviderSettings(mode="manual")))
    graph = build_claims_skill_graph(services, checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "run_t:self_refine:manual"}}
    paused = graph.invoke(make_state("self_refine", max_retries=4, provider_mode="manual"), config=cfg)
    assert paused["__interrupt__"][0].value["node"] == "plan_task"
    paused = graph.invoke(Command(resume={"steps": [{"component": "load_tables"}, {"component": "write_report"}]}), config=cfg)
    req = paused["__interrupt__"][0].value
    assert req["node"] == "self_evaluate"
    assert "evaluation_summary" not in req["payload"] and "feedback" not in req["payload"]
    assert set(req["payload"]["output"]) == {"report_md", "metrics_json"}
    paused = graph.invoke(
        Command(resume={"verdict": "revise", "findings": [{"issue": "denial rate missing", "severity": "high", "suggested_change": "add denial_rate"}]}),
        config=cfg,
    )
    req = paused["__interrupt__"][0].value
    assert req["node"] == "revise_plan" and "evaluation_summary" not in req["payload"] and "reflection" not in req["payload"]
    assert req["payload"]["feedback"][0]["source"] == "self" and req["payload"]["self_review"]["verdict"] == "revise"


def test_feedback_cap_and_hidden_fixes():
    from src.graph_nodes import evaluation_summary, operator_feedback_view, select_feedback

    items = [
        {"feedback_id": "a", "severity": "low", "weight": 1, "related_components": [{"component": "x", "params": {}}]},
        {"feedback_id": "b", "severity": "high", "weight": 3, "related_components": []},
        {"feedback_id": "c", "severity": "medium", "weight": 2, "related_components": []},
        {"feedback_id": "d", "severity": "high", "weight": 4, "related_components": []},
        {"feedback_id": "e", "severity": "medium", "weight": 2, "related_components": []},
    ]
    assert [f["feedback_id"] for f in select_feedback(items, 3)] == ["b", "c", "d"]  # b, d (high) then c (medium, first in rubric order)
    assert select_feedback(items, None) == items and len(select_feedback(items, 10)) == 5
    hidden = operator_feedback_view(items, reveal_fixes=False)
    assert all("related_components" not in f for f in hidden) and hidden[0]["feedback_id"] == "a"
    assert operator_feedback_view(items, reveal_fixes=True)[0]["related_components"]
    evaluation = {"score_total": 1.0, "scores": {}, "passed": False, "checks": [
        {"check_id": "T2.a", "passed": False}, {"check_id": "T2.b", "passed": False}, {"check_id": "T2.c", "passed": True}]}
    summary = evaluation_summary(evaluation, [{"check_id": "T2.b"}])
    assert [c["check_id"] for c in summary["failed_checks"]] == ["T2.b"]
    assert summary["n_failed_checks_total"] == 2 and summary["n_failed_checks_shown"] == 1 and "note" in summary
    assert len(evaluation_summary(evaluation)["failed_checks"]) == 2


def test_capped_feedback_flows_through_reflection_and_revision():
    """With a cap of 1 and fixes hidden, the operator payload itemises one finding and carries no literal fix."""
    services = make_services(ManualProvider(ProviderSettings(mode="manual")))
    services.feedback_max_items = 1
    services.reveal_fixes = False
    graph = build_claims_skill_graph(services, checkpointer=MemorySaver())
    cfg = {"configurable": {"thread_id": "run_t:reflection_only:cap"}}
    paused = graph.invoke(make_state("reflection_only", provider_mode="manual"), config=cfg)
    paused = graph.invoke(Command(resume={"steps": [{"component": "load_tables"}, {"component": "write_report"}]}), config=cfg)
    req = paused["__interrupt__"][0].value
    assert req["node"] == "reflect_on_feedback"
    assert len(req["payload"]["feedback"]) == 1 and "related_components" not in req["payload"]["feedback"][0]
    assert req["payload"]["evaluation_summary"]["n_failed_checks_shown"] == 1


# --------------------------------------------------------------------------- experiment 4 (D-22)


class FakeMemory:
    """Stand-in for src.feedback_memory.FeedbackMemory: one raw, unfiltered log, most recent recalled first."""

    def __init__(self):
        self.records: list[dict] = []

    def append(self, task_id: str, task_title: str, items: list[dict]) -> int:
        for item in items or []:
            source = "self" if item.get("source") == "self" else "checker"
            self.records.append(
                {
                    "task_id": task_id,
                    "task_title": task_title,
                    "attempt": item.get("attempt") or item.get("first_seen_attempt"),
                    "source": source,
                    "severity": item.get("severity"),
                    "criterion": item.get("criterion"),
                    "text": item.get("remediation") if source == "checker" else item.get("issue"),
                    "detail": item.get("detail"),
                    "verdict": item.get("verdict"),
                }
            )
        return len(items or [])

    def recall(self, exclude_task_id: str, limit: int = 30) -> list[dict]:
        return list(reversed([r for r in self.records if r["task_id"] != exclude_task_id]))[:limit]


class FakeMemories:
    """A ``memory_factory``: one log per (run_id, condition), shared across the graphs of a test."""

    def __init__(self):
        self.logs: dict[tuple[str, str], FakeMemory] = {}

    def __call__(self, run_id: str, condition: str) -> FakeMemory:
        return self.logs.setdefault((run_id, condition), FakeMemory())


def memory_services(provider, memories, logger=None) -> Services:
    services = make_services(provider, logger=logger)
    services.memory_factory = memories
    return services


def test_feedback_memory_records_checker_findings_and_shows_them_on_the_next_task():
    memories, logger = FakeMemories(), FakeLogger()
    first = build_claims_skill_graph(memory_services(stub(), memories, logger)).invoke(
        make_state("feedback_memory", task_id="T2", task_index=1, remaining=("T3", "T4"))
    )
    # the arm travels the reflection_only path and nothing was recallable on the first task
    assert first["route_history"][4:6] == ["reflect_on_feedback", "revise_plan"]
    assert first["past_feedback"] == [] and logger.experiment[-1]["past_feedback_count"] == 0
    written = [e for e in logger.skill if e["event"] == "memory_written"]
    assert len(written) == 1 and written[0]["count"] > 0
    assert [e["event"] for e in logger.skill] == ["memory_retrieved", "memory_written"]

    graph = build_claims_skill_graph(
        memory_services(ManualProvider(ProviderSettings(mode="manual")), memories, logger), checkpointer=MemorySaver()
    )
    cfg = {"configurable": {"thread_id": "run_t:feedback_memory:T3"}}
    paused = graph.invoke(
        make_state("feedback_memory", task_id="T3", task_index=2, remaining=("T4",), provider_mode="manual"), config=cfg
    )
    request = paused["__interrupt__"][0].value
    assert request["node"] == "plan_task"
    past = request["payload"]["past_feedback"]
    assert past and {p["source"] for p in past} == {"checker"} and all(p["text"] for p in past)
    assert all(p["task_id"] == "T2" for p in past)  # never a finding from the task being planned
    assert "may or may not apply" in request["payload"]["past_feedback_note"]
    assert [e["count"] for e in logger.skill if e["event"] == "memory_retrieved"][-1] == len(past)


def test_reflection_only_requests_never_carry_past_feedback():
    memories = FakeMemories()
    memories("run_t", "reflection_only").append("T2", "Task T2", [{"remediation": "state the denominator", "severity": "high"}])
    graph = build_claims_skill_graph(
        memory_services(ManualProvider(ProviderSettings(mode="manual")), memories), checkpointer=MemorySaver()
    )
    cfg = {"configurable": {"thread_id": "run_t:reflection_only:T3"}}
    paused = graph.invoke(
        make_state("reflection_only", task_id="T3", task_index=2, remaining=("T4",), provider_mode="manual"), config=cfg
    )
    payload = paused["__interrupt__"][0].value["payload"]
    assert "past_feedback" not in payload and "past_feedback_note" not in payload


def test_self_refine_memory_carries_its_own_findings_and_never_the_evaluator():
    memories, logger = FakeMemories(), FakeLogger()
    first = build_claims_skill_graph(memory_services(stub(), memories, logger)).invoke(
        make_state("self_refine_memory", task_id="T2", task_index=1, remaining=("T3", "T4"), max_retries=4)
    )
    assert first["route_history"] == [
        "load_context", "plan_task", "execute_task", "evaluate_output", "self_evaluate", "revise_plan",
        "execute_task", "evaluate_output", "self_evaluate", "finalize_task",
    ]
    assert first["stop_reason"] == "self_accepted" and logger.experiment[-1]["self_declared_pass"] is True
    assert [e["count"] for e in logger.skill if e["event"] == "memory_written"] == [1]  # the one finding it raised itself
    assert {e.get("source") for e in logger.feedback if e.get("event") == "feedback_issued"} == {"self"}

    graph = build_claims_skill_graph(
        memory_services(ManualProvider(ProviderSettings(mode="manual")), memories, logger), checkpointer=MemorySaver()
    )
    cfg = {"configurable": {"thread_id": "run_t:self_refine_memory:T3"}}
    paused = graph.invoke(
        make_state("self_refine_memory", task_id="T3", task_index=2, remaining=("T4",), max_retries=4, provider_mode="manual"),
        config=cfg,
    )
    payloads = [paused["__interrupt__"][0].value["payload"]]
    past = payloads[0]["past_feedback"]
    assert [p["source"] for p in past] == ["self"] and past[0]["task_id"] == "T2" and past[0]["verdict"] == "revise"

    paused = graph.invoke(Command(resume={"steps": [{"component": "load_tables"}, {"component": "write_report"}]}), config=cfg)
    assert paused["__interrupt__"][0].value["node"] == "self_evaluate"
    payloads.append(paused["__interrupt__"][0].value["payload"])
    paused = graph.invoke(
        Command(
            resume={
                "verdict": "revise",
                "findings": [{"issue": "denial rate missing", "severity": "high", "suggested_change": "add denial_rate"}],
            }
        ),
        config=cfg,
    )
    assert paused["__interrupt__"][0].value["node"] == "revise_plan"
    payloads.append(paused["__interrupt__"][0].value["payload"])
    for payload in payloads:  # nothing the frozen checker produced ever reaches this arm
        assert "evaluation_summary" not in payload and "reflection" not in payload
        assert all(f.get("source") == "self" for f in payload.get("feedback") or [])
        assert all(p["source"] == "self" for p in payload.get("past_feedback") or [])


def test_memory_arms_reuse_the_existing_paths_and_graph_yaml_mirrors_them():
    from src.utils import CONFIG_DIR, read_yaml

    per_condition = designed_topology()["per_condition"]
    assert per_condition["feedback_memory"] == per_condition["reflection_only"]
    assert per_condition["self_refine_memory"] == per_condition["self_refine"]
    doc = read_yaml(CONFIG_DIR / "graph.yaml")
    assert doc["per_condition"] == per_condition and doc["graph_version"] == "4"
    assert set(doc["memory"]["arms"]) == {"feedback_memory", "self_refine_memory"}
    assert doc["memory"]["file"] == "artifacts/memory/<run_id>/<condition>.jsonl"


def test_feedback_memory_store_appends_verbatim_and_recalls_newest_first(tmp_path):
    from src.feedback_memory import FeedbackMemory

    memory = FeedbackMemory(tmp_path, "run_t", "feedback_memory")
    assert memory.recall("T2") == []
    checker = {"remediation": "state the denominator", "severity": "high", "criterion": "correctness",
               "detail": "x" * 400, "first_seen_attempt": 1}
    assert memory.append("T2", "Task T2", [checker]) == 1
    assert memory.append("T3", "Task T3", [{"source": "self", "issue": "no caveats", "severity": "low", "verdict": "revise"}]) == 1
    assert memory.path == tmp_path / "run_t" / "feedback_memory.jsonl"
    recalled = memory.recall("T4")
    assert [r["task_id"] for r in recalled] == ["T3", "T2"]  # most recent first
    assert recalled[0]["source"] == "self" and recalled[0]["text"] == "no caveats" and recalled[0]["verdict"] == "revise"
    assert recalled[1]["source"] == "checker" and recalled[1]["text"] == "state the denominator"
    assert len(recalled[1]["detail"]) == 240  # only the detail is truncated
    assert [r["task_id"] for r in memory.recall("T3")] == ["T2"]
    assert len(memory.recall("T4", limit=1)) == 1
    assert memory.append("T4", "Task T4", []) == 0


# --------------------------------------------------------------------------- frozen memory (D-24)
def read_only_services(provider, memories, store=None, logger=None) -> Services:
    """A run whose carried-over memory is frozen: recall and retrieval work, nothing is ever written."""
    services = make_services(provider, store=store, logger=logger)
    services.memory_factory = memories
    services.memory_read_only = True
    return services


def test_memory_read_only_recalls_the_seeded_log_but_never_appends():
    memories, logger = FakeMemories(), FakeLogger()
    seeded = memories("run_t", "feedback_memory")
    seeded.records.append(
        {"task_id": "T2", "task_title": "Task T2", "attempt": 1, "source": "checker", "severity": "high",
         "criterion": "statistical_discipline", "text": "state the denominator", "detail": None, "verdict": None,
         "seeded_from": "run_006"}
    )
    graph = build_claims_skill_graph(read_only_services(stub(), memories, logger=logger))
    out = graph.invoke(make_state("feedback_memory", task_id="T3", task_index=2, remaining=("T4",)))

    # the seeded note was recalled and planned with ...
    assert [r["text"] for r in out["past_feedback"]] == ["state the denominator"]
    assert logger.experiment[-1]["past_feedback_count"] == 1
    # ... and nothing was written back: the log still holds exactly the one seeded record
    assert len(seeded.records) == 1 and seeded.records[0]["seeded_from"] == "run_006"
    events = [e for e in logger.skill if e["event"].startswith("memory_")]
    assert [e["event"] for e in events] == ["memory_retrieved", "memory_write_skipped"]
    skipped = events[-1]
    assert skipped["reason"] == "read_only" and skipped["count"] == 0 and skipped["withheld"] > 0
    assert not any(e["event"] == "memory_written" for e in logger.skill)
    assert logger.experiment[-1]["memory_read_only"] is True


def test_memory_read_only_skill_learning_retrieves_but_never_proposes():
    store, logger, memories = FakeStore(), FakeLogger(), FakeMemories()
    store.skills.append(
        {
            "skill_id": "evolved_run_006_001",
            "name": "state_the_denominator",
            "kind": "evolved",
            "version": 1,
            "tags": ["rates"],
            "sections": {"required_checks": ["denial_rate.denominator=adjudicated_claims and state it"]},
            "created_after_task_index": 0,
            "path": "skills/evolved/run_006/state_the_denominator_v1.md",
        }
    )
    graph = build_claims_skill_graph(read_only_services(stub(), memories, store=store, logger=logger))
    out = graph.invoke(make_state("skill_learning", task_id="T3", task_index=6, remaining=("T4",)))

    # the seeded skill is still retrieved and offered to the planner ...
    assert [s["skill_id"] for s in out["retrieved_skills"]] == ["evolved_run_006_001"]
    # ... but the learn path is closed: no reflect-for-learning, no proposal, no new skill
    assert out["route_history"][-1] == "finalize_task"
    assert "propose_skill" not in out["route_history"] and "validate_skill" not in out["route_history"]
    assert out["skills_created"] == [] and len(store.skills) == 1
    assert not any(e["event"].startswith("skill_pro") or e["event"] == "skill_persisted" for e in logger.skill)
    assert logger.experiment[-1]["memory_read_only"] is True
    # skill_learning carries no raw memory log, so no memory event is recorded either way
    assert not any(e["event"].startswith("memory_") for e in logger.skill)


def test_run_config_reads_memory_read_only_from_experiment_yaml():
    from src.run_experiment import RunConfig
    from src.utils import CONFIG_DIR

    cfg = RunConfig.from_experiment_yaml("run_x", "manual", ["reflection_only"], path=CONFIG_DIR / "experiment.yaml")
    assert cfg.memory_read_only is True and cfg.seed_from_run == "run_006" and cfg.task_index_offset == 6
    assert cfg.task_order == ["T11", "T12", "T13"]
    assert "memory_read_only" in cfg.to_dict()  # so it lands in logs/runs/<run_id>.json
