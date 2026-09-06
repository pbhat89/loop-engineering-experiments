"""Provider adapter tests: mode selection, fail-closed API mode, fixture rules, manual file protocol."""
from __future__ import annotations

import json

import pytest

from src.graph_state import PlanResponse, ReflectionResponse, SkillProposalResponse
from src.llm_provider import (
    API_KEY_ENV,
    MODE_ENV,
    AnthropicAPIProvider,
    FixtureProvider,
    ManualProvider,
    OperatorRequest,
    ProviderConfigurationError,
    ProviderSettings,
    get_provider,
    pending_requests,
    read_response_file,
)

CATALOGUE = [
    {"id": "load_tables", "default_selected": True, "params": {}},
    {
        "id": "denial_rate",
        "default_selected": False,
        "params": {"denominator": {"options": ["all_claims", "adjudicated_claims"], "default": "all_claims"}},
    },
    {"id": "write_report", "default_selected": True, "params": {"caveats": {"options": [[], ["synthetic_data"]], "default": []}}},
]


def _request(node="plan_task", payload=None, **kw):
    base = dict(run_id="run_t", condition="baseline", task_id="T2", attempt=1, node=node, seq=1, instructions="x")
    base.update(kw)
    return OperatorRequest.build(payload=payload or {"component_catalogue": CATALOGUE, "remaining_task_ids": ["T3", "T4"]}, **base)


def test_default_mode_is_manual(monkeypatch):
    monkeypatch.delenv(MODE_ENV, raising=False)
    settings = ProviderSettings.from_env()
    assert settings.mode == "manual"
    provider = get_provider(settings)
    assert isinstance(provider, ManualProvider)
    assert provider.describe() == {
        "provider_mode": "manual",
        "operator": "claude-code-subagent",
        "model_identifier": "claude-fable-5-1",
    }


def test_env_selects_stub_and_rejects_unknown(monkeypatch):
    monkeypatch.setenv(MODE_ENV, "stub")
    assert isinstance(get_provider(ProviderSettings.from_env()), FixtureProvider)
    monkeypatch.setenv(MODE_ENV, "magic")
    with pytest.raises(ProviderConfigurationError):
        ProviderSettings.from_env()


def test_anthropic_api_fails_closed_without_key(monkeypatch):
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    with pytest.raises(ProviderConfigurationError, match="ANTHROPIC_API_KEY"):
        AnthropicAPIProvider(ProviderSettings(mode="anthropic_api"))
    with pytest.raises(ProviderConfigurationError):
        get_provider(ProviderSettings(mode="anthropic_api"))


def test_fixture_plan_uses_defaults_then_skills_then_feedback():
    provider = FixtureProvider(ProviderSettings(mode="stub"))
    plan = PlanResponse(**provider.decide(_request()))
    assert [s.component for s in plan.steps] == ["load_tables", "write_report"]
    assert plan.skills_applied == []

    skill = {
        "skill_id": "foundational_003",
        "name": "rates",
        "tags": ["rates"],
        "sections": {"required_checks": ["compute denial_rate with denial_rate.denominator=adjudicated_claims"]},
    }
    with_skill = PlanResponse(**provider.decide(_request(payload={"component_catalogue": CATALOGUE, "retrieved_skills": [skill]})))
    by_id = {s.component: s.params for s in with_skill.steps}
    assert by_id["denial_rate"] == {"denominator": "adjudicated_claims"}
    assert with_skill.skills_applied == ["foundational_003"]

    feedback = [
        {
            "feedback_id": "T2-x",
            "remediation": "use adjudicated",
            "related_components": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
            "reusable": True,
            "applicable_task_ids": ["T3", "T4"],
        }
    ]
    revised = PlanResponse(
        **provider.decide(
            _request(node="revise_plan", payload={"component_catalogue": CATALOGUE, "feedback": feedback, "prior_plan": plan.model_dump()})
        )
    )
    assert {s.component: s.params for s in revised.steps}["denial_rate"]["denominator"] == "adjudicated_claims"
    assert "T2-x" in (revised.changes_summary or "")


def test_fixture_reflection_and_proposal_rules():
    provider = FixtureProvider(ProviderSettings(mode="stub"))
    feedback = [
        {
            "feedback_id": "T2-a",
            "criterion": "correctness",
            "issue_type": "wrong_denominator",
            "remediation": "use adjudicated",
            "related_components": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
            "reusable": True,
            "applicable_task_ids": ["T3", "T4"],
        },
        {"feedback_id": "T2-b", "remediation": "one-off fix", "related_components": [], "reusable": False, "applicable_task_ids": []},
    ]
    reflection = ReflectionResponse(**provider.decide(_request(node="reflect_on_feedback", payload={"feedback": feedback})))
    assert len(reflection.reusable_lessons) == 1 and len(reflection.current_task_corrections) == 2

    payload = {
        "feedback": feedback,
        "reflection": reflection.model_dump(),
        "remaining_task_ids": ["T3", "T4"],
        "task_spec": {"tags": ["rates"], "required_artifacts": ["a.png"]},
        "task_id": "T2",
    }
    proposal = SkillProposalResponse(**provider.decide(_request(node="propose_skill", payload=payload)))
    assert proposal.proposal is not None
    assert "denial_rate.denominator=adjudicated_claims" in " ".join(proposal.proposal.procedure)
    assert proposal.proposal.applicable_task_ids == ["T3", "T4"]

    payload["remaining_task_ids"] = ["T4"]
    none = SkillProposalResponse(**provider.decide(_request(node="propose_skill", payload=payload)))
    assert none.proposal is None and none.reason_if_null


def test_manual_file_protocol_roundtrip(tmp_path):
    request = _request()
    assert request.request_id == "run_t:baseline:T2:a1:plan_task:1"
    path = request.write_request_file(tmp_path)
    assert path == tmp_path / "run_t" / "baseline" / "T2_a1_plan_task_1.request.json"
    assert json.loads(path.read_text(encoding="utf-8"))["response_schema"]["properties"]["steps"]
    assert pending_requests("run_t", "baseline", tmp_path) == [path]

    response_path = request.response_path(tmp_path)
    response_path.write_text(json.dumps({"steps": [{"component": "load_tables"}]}), encoding="utf-8")
    data, digest = read_response_file(response_path)
    assert data["steps"][0]["component"] == "load_tables" and len(digest) == 64
    assert pending_requests("run_t", "baseline", tmp_path) == []


def test_request_rejects_non_decision_nodes():
    with pytest.raises(ValueError):
        OperatorRequest.build(run_id="r", condition="baseline", task_id="T1", attempt=1, node="execute_task", seq=1, instructions="x", payload={})
