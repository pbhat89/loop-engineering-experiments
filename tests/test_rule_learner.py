"""Rule learner (experiment 2): token grammar, plan rules by parameter concept, reflection, proposal, validator fit, graph transfer."""
from __future__ import annotations

from src.claims_graph import build_claims_skill_graph
from src.graph_state import PlanResponse, ReflectionResponse, SkillProposalResponse
from src.llm_provider import OperatorRequest, ProviderSettings, get_provider
from src.rule_learner import RuleLearnerProvider, describe_rule, parse_rules, rule_token
from src.skill_validator import validate as real_validate
from tests.test_graph_routes import FakeLogger, FakeStore, make_services, make_state, task_spec

CATALOGUE = [
    {"id": "load_tables", "default_selected": True, "params": {}},
    {"id": "denial_rate", "default_selected": True, "params": {"denominator": {"options": ["all_claims", "adjudicated_claims"], "default": "all_claims"}}},
    {"id": "group_comparison", "default_selected": True, "params": {
        "denominator": {"options": ["all_claims", "adjudicated_claims"], "default": "all_claims"},
        "min_group_size": {"options": [0, 30, 50], "default": 0},
        "group_by": {"multi": True, "options": ["provider_specialty", "network_status"], "default": ["provider_specialty"]}}},
    {"id": "join_check", "default_selected": False, "params": {"pairs": {"multi": True, "options": ["a->b", "c->d"], "default": []}}},
    {"id": "write_report", "default_selected": True, "params": {
        "caveats": {"multi": True, "options": ["synthetic_data", "small_groups"], "default": []},
        "show_denominators": {"options": [True, False], "default": False}}},
]
SKILL = {
    "skill_id": "evolved_r_001", "name": "house_conventions_t2", "kind": "evolved", "version": 1, "tags": ["rates"],
    "sections": {"required_checks": ["param:denominator=adjudicated_claims", "param:min_group_size=30", "list:caveats+=synthetic_data",
                                     "param:show_denominators=true", "component:join_check", "list:pairs+=a->b", "list:group_by-=provider_specialty"]},
}


def learner() -> RuleLearnerProvider:
    return RuleLearnerProvider(ProviderSettings(mode="rule_learner"))


def request(node="plan_task", payload=None, **kw):
    base = dict(run_id="r", condition="skill_learning", task_id="T3", attempt=1, node=node, seq=1, instructions="x")
    base.update(kw)
    return OperatorRequest.build(payload=payload or {}, **base)


def test_mode_registered_and_labelled():
    p = get_provider(ProviderSettings(mode="rule_learner"))
    assert isinstance(p, RuleLearnerProvider)
    assert p.describe() == {"provider_mode": "rule_learner", "operator": "deterministic-rule-learner", "model_identifier": "rule-learner-v1"}


def test_token_grammar_roundtrip():
    text = "Notes: param:denominator=adjudicated_claims, param:monthly_trend.date_column=service_date_from. list:caveats+=synthetic_data; list:features-=claim_id component:join_check param:test_size=0.25"
    rules = parse_rules(text)
    tokens = {rule_token(r) for r in rules}
    assert tokens == {"param:denominator=adjudicated_claims", "param:monthly_trend.date_column=service_date_from", "list:caveats+=synthetic_data",
                      "list:features-=claim_id", "component:join_check", "param:test_size=0.25"}
    assert describe_rule(("param", None, "denominator", "adjudicated_claims")).startswith("`denominator` = `adjudicated_claims`")
    assert describe_rule(("list", "features", "-=", "claim_id")) == "Remove `claim_id` from any `features` list."


def test_plan_defaults_then_conventions_by_parameter_name():
    naive = PlanResponse(**learner().decide(request(payload={"component_catalogue": CATALOGUE, "retrieved_skills": []})))
    by_id = {s.component: s.params for s in naive.steps}
    assert set(by_id) == {"load_tables", "denial_rate", "group_comparison", "write_report"}
    assert by_id["denial_rate"] == {"denominator": "all_claims"} and by_id["group_comparison"]["min_group_size"] == 0
    assert naive.skills_applied == []

    learned = PlanResponse(**learner().decide(request(payload={"component_catalogue": CATALOGUE, "retrieved_skills": [SKILL]})))
    by_id = {s.component: s.params for s in learned.steps}
    assert by_id["denial_rate"]["denominator"] == "adjudicated_claims"           # generalised across components
    assert by_id["group_comparison"]["denominator"] == "adjudicated_claims"
    assert by_id["group_comparison"]["min_group_size"] == 30                     # typed option matched by string form
    assert by_id["group_comparison"]["group_by"] == []                           # list removal
    assert by_id["write_report"] == {"caveats": ["synthetic_data"], "show_denominators": True}
    assert by_id["join_check"] == {"pairs": ["a->b"]}                            # component added, then list add
    assert learned.skills_applied == ["evolved_r_001"]


def test_reflection_generalises_feedback_into_tokens():
    prior = {"steps": [{"component": "denial_rate", "params": {"denominator": "all_claims"}},
                       {"component": "write_report", "params": {"caveats": [], "show_denominators": False}}]}
    feedback = [
        {"feedback_id": "T2-denominator", "remediation": "use adjudicated", "reusable": True, "applicable_task_ids": ["T3", "T4"],
         "related_components": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}]},
        {"feedback_id": "T2-caveats", "remediation": "add caveats", "reusable": True, "applicable_task_ids": ["T3"],
         "related_components": [{"component": "write_report", "params": {"caveats": ["synthetic_data"], "show_denominators": True}}]},
        {"feedback_id": "T2-join", "remediation": "check joins", "reusable": True, "applicable_task_ids": ["T3"],
         "related_components": [{"component": "join_check", "params": {"pairs": ["a->b"]}}]},
    ]
    refl = ReflectionResponse(**learner().decide(request(node="reflect_on_feedback", payload={"feedback": feedback, "plan": prior, "remaining_task_ids": ["T3", "T4"]})))
    lessons = {l.source_feedback_ids[0]: l.lesson for l in refl.reusable_lessons}
    assert "param:denominator=adjudicated_claims" in lessons["T2-denominator"] and "component:denial_rate" in lessons["T2-denominator"]
    assert "list:caveats+=synthetic_data" in lessons["T2-caveats"] and "param:show_denominators=true" in lessons["T2-caveats"]
    assert "component:join_check" in lessons["T2-join"] and "list:pairs+=a->b" in lessons["T2-join"]
    assert len(refl.current_task_corrections) == 3

    # list removals are learned only from exclusion-type feedback
    prior_feat = {"steps": [{"component": "feature_set", "params": {"features": ["claim_type", "fraud_pattern_type", "claim_id"]}}]}
    exclusion = [{"feedback_id": "T6-no_leakage_features", "issue_type": "leakage", "remediation": "drop leaks", "reusable": True,
                  "applicable_task_ids": ["T7"], "related_components": [{"component": "feature_set", "params": {"features": ["claim_type"]}}]}]
    coverage = [{"feedback_id": "T3-caveat_coverage", "issue_type": "missing_caveat", "remediation": "add caveats", "reusable": True,
                 "applicable_task_ids": ["T4"], "related_components": [{"component": "write_report", "params": {"caveats": ["small_groups"]}}]}]
    prior_cav = {"steps": [{"component": "write_report", "params": {"caveats": ["synthetic_data"]}}]}
    r1 = ReflectionResponse(**learner().decide(request(node="reflect_on_feedback", payload={"feedback": exclusion, "plan": prior_feat, "remaining_task_ids": ["T7", "T8"]})))
    assert "list:features-=fraud_pattern_type" in r1.reusable_lessons[0].lesson and "list:features-=claim_id" in r1.reusable_lessons[0].lesson
    r2 = ReflectionResponse(**learner().decide(request(node="reflect_on_feedback", payload={"feedback": coverage, "plan": prior_cav, "remaining_task_ids": ["T4", "T5"]})))
    assert "list:caveats+=small_groups" in r2.reusable_lessons[0].lesson and "-=" not in r2.reusable_lessons[0].lesson


def test_proposal_excludes_known_tokens_and_passes_real_validator():
    reflection = {"reusable_lessons": [
        {"lesson": "House convention from T2-a: param:denominator=adjudicated_claims list:caveats+=synthetic_data", "applicable_task_ids": ["T3", "T4"], "source_feedback_ids": ["T2-a"]},
        {"lesson": "House convention from T2-b: param:min_group_size=30", "applicable_task_ids": ["T3", "T4"], "source_feedback_ids": ["T2-b"]},
    ]}
    payload = {"reflection": reflection, "remaining_task_ids": ["T3", "T4"], "task_id": "T2",
               "task_spec": {"tags": ["descriptive", "rates"], "required_artifacts": ["report.md"]},
               "existing_skills": [{"skill_id": "x", "required_checks": ["param:denominator=adjudicated_claims"]}]}
    resp = SkillProposalResponse(**learner().decide(request(node="propose_skill", task_id="T2", payload=payload)))
    assert resp.proposal is not None
    assert resp.proposal.required_checks == ["list:caveats+=synthetic_data", "param:min_group_size=30"]  # the known token is skipped
    assert set(resp.proposal.source_feedback_ids) == {"T2-a", "T2-b"} and "rates" in resp.proposal.tags
    verdict = real_validate(resp.proposal.model_dump(), [], "T2", ["T3", "T4"])
    assert verdict["decision"] == "accepted", verdict

    payload["existing_skills"].append({"skill_id": "y", "required_checks": resp.proposal.required_checks})
    none = SkillProposalResponse(**learner().decide(request(node="propose_skill", task_id="T2", payload=payload)))
    assert none.proposal is None and "already captured" in (none.reason_if_null or "")


def test_graph_transfer_second_task_passes_first_attempt():
    store, logger = FakeStore(), FakeLogger()
    graph = build_claims_skill_graph(make_services(learner(), store, logger))
    kw = dict(provider_mode="rule_learner", operator="deterministic-rule-learner", model_identifier="rule-learner-v1")
    first = graph.invoke(make_state("skill_learning", task_id="T2", task_index=1, remaining=("T3", "T4"), **kw))
    assert first["execution_attempts"] == 2 and first["skills_created"] == ["evolved_test_001"]
    assert "param:denominator=adjudicated_claims" in " ".join(store.skills[0]["sections"]["required_checks"])
    second = graph.invoke(make_state("skill_learning", task_id="T3", task_index=2, remaining=("T4",), **kw))
    assert second["execution_attempts"] == 1 and second["evaluation"]["passed"]
    assert logger.experiment[-1]["skills_reused"] == ["evolved_test_001"]
    baseline = graph.invoke(make_state("baseline", task_id="T3", task_index=2, remaining=("T4",), **kw))
    assert baseline["execution_attempts"] == 2  # no memory: the same mistake again


def test_task_spec_catalogue_is_unchanged_by_learner():
    spec = task_spec("T2")
    before = [dict(c) for c in spec["components"]]
    learner().decide(request(payload={"component_catalogue": spec["components"], "retrieved_skills": [SKILL]}))
    assert spec["components"] == before
