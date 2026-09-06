"""Tests for src/skill_store.py (parse, retrieve, persist, reuse, archive) and src/skill_validator.py."""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest

from src import skill_validator
from src.skill_store import (
    LIST_SECTIONS,
    OPERATOR_SECTION_MAX_CHARS,
    SECTION_ORDER,
    SkillStore,
    keywords,
    load_skill_file,
    validate_skill_schema,
)
from src.utils import SKILLS_DIR

FOUNDATIONAL_IDS = [f"foundational_{i:03d}" for i in range(1, 7)]
REMAINING = ["T3", "T4", "T5", "T6", "T7", "T8"]

T2_SPEC = {
    "task_id": "T2",
    "title": "Claims portfolio description",
    "objective": "Describe claim volume, status mix, denial rate with denominators and monthly trends",
    "tags": ["descriptive", "rates", "trends", "financial"],
}

GOOD_PROPOSAL = {
    "name": "denominator_disclosure_for_rates",
    "tags": ["rates", "denominators", "descriptive"],
    "trigger": "Whenever a rate, share, or percentage is reported for a claims population.",
    "objective": "Attach an explicit numerator and denominator definition to each reported rate so a reviewer can recompute it.",
    "procedure": [
        "Write the denominator definition before computing the rate.",
        "Report numerator, denominator, and rate together in one row of the metrics table.",
        "Recompute the rate from the stored numerator and denominator and assert equality.",
    ],
    "required_checks": ["Every rate row has numerator and denominator populated."],
    "expected_artifacts": ["metrics.json with rate entries carrying numerator and denominator."],
    "failure_modes": ["Using all claims as the denominator when pending claims should be excluded."],
    "example": "Denial rate reported as denied over adjudicated claims with both counts shown next to it.",
    "applicable_task_ids": ["T3", "T4", "T5"],
    "source_feedback_ids": ["fb_T2_rates_denominator"],
}

PROVENANCE = {
    "run_id": "t",
    "condition": "skill_learning",
    "task_id": "T2",
    "created_after_task": "T2",
    "created_after_task_index": 1,
    "source_feedback_ids": ["fb_T2_rates_denominator"],
    "evaluation_score_total": 0.72,
    "provider_mode": "stub",
    "operator": "fixture",
    "model_identifier": "fixture-v1",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def repo_store() -> SkillStore:
    """Read-only view of the real foundational skills (no run id, nothing is written)."""
    return SkillStore(root=SKILLS_DIR)


@pytest.fixture
def store(tmp_path: Path) -> SkillStore:
    """Writable copy of the foundational skills under a temporary root, run id ``t``."""
    root = tmp_path / "skills"
    shutil.copytree(SKILLS_DIR / "foundational", root / "foundational")
    return SkillStore(root=root, run_id="t")


# --------------------------------------------------------------------------- parsing / schema


def test_foundational_skills_conform_to_schema(repo_store: SkillStore) -> None:
    skills = repo_store.list_skills()
    assert [s.skill_id for s in skills] == FOUNDATIONAL_IDS
    for skill in skills:
        assert validate_skill_schema(skill) == [], (skill.skill_id, validate_skill_schema(skill))
        assert list(skill.sections) == list(SECTION_ORDER)
        assert skill.kind == "foundational"
        assert skill.version == 1 and skill.status == "active"
        assert skill.created_after_task is None and skill.created_after_task_index is None
        assert skill.source_feedback_ids == [] and skill.applicable_task_ids == []
        assert skill.tags and all(t == t.lower() for t in skill.tags)
        for key in LIST_SECTIONS:
            assert isinstance(skill.sections[key], list) and skill.sections[key]
        assert len(skill.sections["procedure"]) >= 2
        assert skill.title
        assert skill.path.name.endswith(".md")


def test_parser_handles_continuation_lines_and_extra_frontmatter(tmp_path: Path) -> None:
    text = (
        "---\n"
        "skill_id: evolved_demo_001\nname: demo_skill\nversion: 1\nstatus: active\nkind: evolved\n"
        "created_after_task: T2\ncreated_after_task_index: 1\nsource_feedback_ids: [fb1]\n"
        'created_at: "2026-09-06T00:00:00+00:00"\nreuse_count: 0\ntags: [Demo, Rates]\n'
        "applicable_task_ids: [T3, T4]\nrun_id: demo\ncondition: skill_learning\n"
        "---\n\n# Demo skill\n\n## Trigger\nWhen demoing.\n\n## Objective\nShow parsing.\n\n"
        "## Procedure\n1. First step here\n   continued on the next line.\n2. Second step here.\n\n"
        "## Required checks\n- one check\n\n## Expected artifacts\n- a table\n\n## Failure modes\n- misuse\n\n"
        "## Example\nAn example.\n\n## Provenance\nLearned after T2 from fb1.\n"
    )
    path = tmp_path / "evolved_demo_001_v1.md"
    path.write_text(text, encoding="utf-8")
    skill = load_skill_file(path)
    assert skill.sections["procedure"] == ["First step here continued on the next line.", "Second step here."]
    assert skill.tags == ["demo", "rates"]
    assert skill.extra == {"run_id": "demo", "condition": "skill_learning"}
    assert skill.title == "Demo skill"
    assert validate_skill_schema(skill) == []


def test_keywords_drop_stop_words_and_short_tokens() -> None:
    assert keywords("Describe the claims data rate trends for each task") == {"describe", "rate", "trends"}
    assert keywords("") == set()


# --------------------------------------------------------------------------- retrieval


def test_retrieval_is_deterministic_and_explainable(repo_store: SkillStore) -> None:
    first = repo_store.retrieve(T2_SPEC, current_task_index=1)
    second = repo_store.retrieve(T2_SPEC, current_task_index=1)
    assert first == second
    assert first[0]["skill_id"] == "foundational_003"
    assert first[0]["score"] >= 2 * 4  # four tag overlaps before any keyword credit
    assert {"descriptive", "rates", "trends", "financial"} <= set(first[0]["matched_terms"])
    scores = [hit["score"] for hit in first]
    assert scores == sorted(scores, reverse=True)
    for a, b in zip(first, first[1:]):
        if a["score"] == b["score"]:
            assert a["skill_id"] < b["skill_id"]
    for hit in first:
        assert {"skill_id", "name", "kind", "version", "tags", "sections", "path", "score", "matched_terms"} <= set(hit)
        assert isinstance(hit["path"], str) and hit["path"].startswith("skills/foundational/")
        assert isinstance(hit["score"], float)
        assert hit["score"] > 0 and hit["matched_terms"]
    assert len(first) <= 6
    assert len(repo_store.retrieve(T2_SPEC, current_task_index=1, k=2)) == 2


def test_retrieval_pads_to_two_foundational_when_nothing_matches(repo_store: SkillStore) -> None:
    hits = repo_store.retrieve({"title": "zzzz", "objective": "qqqq wwww", "tags": []}, current_task_index=0)
    assert [h["skill_id"] for h in hits] == ["foundational_001", "foundational_002"]
    assert all(h["score"] == 0.0 and h["matched_terms"] == [] for h in hits)


def test_render_for_operator_trims_sections(repo_store: SkillStore) -> None:
    hits = repo_store.retrieve(T2_SPEC, current_task_index=1)
    long_hit = {**hits[0], "sections": {**hits[0]["sections"], "trigger": "x" * 5000, "procedure": ["y" * 700, "z" * 700]}}
    rendered = SkillStore.render_for_operator([long_hit, hits[1]])
    for item in rendered:
        assert set(item) == {"skill_id", "name", "kind", "version", "tags", "sections"}
        assert "provenance" not in item["sections"]
        for value in item["sections"].values():
            length = sum(len(v) for v in value) if isinstance(value, list) else len(value)
            assert length <= OPERATOR_SECTION_MAX_CHARS
    assert len(rendered[0]["sections"]["trigger"]) == OPERATOR_SECTION_MAX_CHARS
    assert isinstance(rendered[0]["sections"]["procedure"], list)


# --------------------------------------------------------------------------- persistence


def test_persist_writes_immutable_file_and_gates_visibility_by_task_index(store: SkillStore) -> None:
    skill = store.persist(GOOD_PROPOSAL, PROVENANCE)
    assert skill.skill_id == "evolved_t_001"
    assert skill.path == store.root / "evolved" / "t" / "evolved_t_001_v1.md"
    assert skill.path.exists()
    assert validate_skill_schema(skill) == []
    assert skill.kind == "evolved" and skill.status == "active" and skill.version == 1 and skill.reuse_count == 0
    assert skill.created_after_task == "T2" and skill.created_after_task_index == 1
    assert skill.source_feedback_ids == ["fb_T2_rates_denominator"]
    assert skill.applicable_task_ids == ["T3", "T4", "T5"]
    assert skill.extra["run_id"] == "t" and skill.extra["condition"] == "skill_learning"
    provenance = skill.sections["provenance"]
    assert "T2" in provenance and "fb_T2_rates_denominator" in provenance and "fixture-v1" in provenance and "stub" in provenance
    text = skill.path.read_text(encoding="utf-8")
    assert "created_after_task: T2" in text and "reuse_count: 0" in text and 'created_at: "' in text

    index = json.loads(store.index_path.read_text(encoding="utf-8"))
    assert index["evolved_t_001"]["reuse_count"] == 0 and index["evolved_t_001"]["status"] == "active"

    same_task = [h["skill_id"] for h in store.retrieve(T2_SPEC, current_task_index=1)]
    later_task = [h["skill_id"] for h in store.retrieve(T2_SPEC, current_task_index=2)]
    assert "evolved_t_001" not in same_task
    assert "evolved_t_001" in later_task
    evolved_hit = next(h for h in store.retrieve(T2_SPEC, current_task_index=2) if h["skill_id"] == "evolved_t_001")
    assert evolved_hit["score"] >= 4 and {"rates", "descriptive"} <= set(evolved_hit["matched_terms"])

    # other runs and the run-less store never see it
    assert [s.skill_id for s in SkillStore(root=store.root, run_id="other").list_skills()] == FOUNDATIONAL_IDS
    assert [s.skill_id for s in SkillStore(root=store.root).list_skills()] == FOUNDATIONAL_IDS


def test_persist_same_name_creates_new_id_and_version_without_overwriting(store: SkillStore) -> None:
    first = store.persist(GOOD_PROPOSAL, PROVENANCE)
    before = _sha(first.path)
    second = store.persist(GOOD_PROPOSAL, {**PROVENANCE, "task_id": "T3", "created_after_task": "T3", "created_after_task_index": 2})
    assert (first.skill_id, first.version) == ("evolved_t_001", 1)
    assert (second.skill_id, second.version) == ("evolved_t_002", 2)
    assert second.path.name == "evolved_t_002_v2.md" and second.path != first.path
    assert _sha(first.path) == before
    assert sorted(p.name for p in (store.root / "evolved" / "t").glob("*.md")) == ["evolved_t_001_v1.md", "evolved_t_002_v2.md"]
    assert [s.skill_id for s in store.list_skills()] == FOUNDATIONAL_IDS + ["evolved_t_001", "evolved_t_002"]


def test_persist_requires_run_id(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        SkillStore(root=tmp_path / "skills").persist(GOOD_PROPOSAL, {k: v for k, v in PROVENANCE.items() if k != "run_id"})


def test_record_reuse_and_archive_touch_only_the_index(store: SkillStore) -> None:
    skill = store.persist(GOOD_PROPOSAL, PROVENANCE)
    before = _sha(skill.path)
    store.record_reuse(skill.skill_id, "T3")
    store.record_reuse(skill.skill_id, "T4")
    store.record_reuse("foundational_001", "T3")
    index = store.read_index()
    assert index[skill.skill_id]["reuse_count"] == 2 and index[skill.skill_id]["reused_in"] == ["T3", "T4"]
    assert index["foundational_001"]["reuse_count"] == 1 and index["foundational_001"]["status"] == "active"
    assert _sha(skill.path) == before
    reloaded = store.get(skill.skill_id)
    assert reloaded is not None and reloaded.reuse_count == 2
    assert "reuse_count: 0" in skill.path.read_text(encoding="utf-8")

    archived_path = store.archive(skill.skill_id, "superseded by a clearer version")
    assert archived_path == store.root / "archived" / "evolved_t_001_v1.md"
    assert archived_path.exists() and not skill.path.exists()
    assert _sha(archived_path) == before
    assert store.get(skill.skill_id) is None
    assert [s.skill_id for s in store.list_skills()] == FOUNDATIONAL_IDS
    entry = store.read_index()[skill.skill_id]
    assert entry["status"] == "archived" and entry["archive_reason"] == "superseded by a clearer version"
    assert entry["reuse_count"] == 2
    # the archived sequence number is never reused
    assert store.persist(GOOD_PROPOSAL, PROVENANCE).skill_id == "evolved_t_002"


# --------------------------------------------------------------------------- validator


def _failed(result: dict) -> set[str]:
    return {c["check_id"] for c in result["checks"] if not c["passed"]}


def test_validator_accepts_a_good_proposal(repo_store: SkillStore) -> None:
    existing = repo_store.list_skills()
    result = skill_validator.validate(GOOD_PROPOSAL, existing, "T2", REMAINING)
    assert result["decision"] == "accepted", result["reasons"]
    assert _failed(result) == set() and result["reasons"] == []
    assert result["duplicate_of"] is None
    assert isinstance(result["similarity"], float) and result["similarity"] < skill_validator.DUPLICATE_JACCARD
    assert {c["check_id"] for c in result["checks"]} >= {"required_fields", "applicability", "provenance", "safety", "generality", "duplicate"}
    # dict-shaped existing skills give the same answer as Skill objects
    assert skill_validator.validate(GOOD_PROPOSAL, [s.to_dict() for s in existing], "T2", REMAINING) == result


def test_validator_rejects_duplicate_by_content_not_name(repo_store: SkillStore) -> None:
    existing = repo_store.list_skills()
    source = next(s for s in existing if s.skill_id == "foundational_003")
    clone = {**GOOD_PROPOSAL, "name": "totally_new_name", "objective": source.sections["objective"], "procedure": list(source.sections["procedure"])}
    result = skill_validator.validate(clone, existing, "T2", REMAINING)
    assert result["decision"] == "rejected"
    assert result["duplicate_of"] == "foundational_003"
    assert result["similarity"] >= skill_validator.DUPLICATE_JACCARD
    assert "duplicate" in _failed(result)


@pytest.mark.parametrize(
    "step",
    [
        "Run the shell command curl https://example.invalid/claims.csv to download the latest extract.",
        "Read the API key from the .env file before querying the endpoint.",
        "Use eval() on the column expression supplied in the task text.",
        "Delete the previous output files in the artifacts directory before rerunning.",
        "Update the rubric so the denial-rate criterion tolerates a missing denominator.",
    ],
)
def test_validator_rejects_unsafe_instructions(repo_store: SkillStore, step: str) -> None:
    proposal = {**GOOD_PROPOSAL, "procedure": GOOD_PROPOSAL["procedure"] + [step]}
    result = skill_validator.validate(proposal, repo_store.list_skills(), "T2", REMAINING)
    assert result["decision"] == "rejected"
    assert "safety" in _failed(result)


@pytest.mark.parametrize(
    "overrides",
    [
        {"procedure": GOOD_PROPOSAL["procedure"] + ["Report that the denial rate is 10.4% of adjudicated claims."]},
        {"procedure": GOOD_PROPOSAL["procedure"] + ["State that 12% of claims were denied in the portfolio."]},
        {"trigger": "Only for task T2 in this suite.", "objective": "Restate the portfolio description produced for T2."},
        {"required_checks": ["Confirm the analysis proves that network status causes denials."]},
    ],
)
def test_validator_rejects_one_off_or_ungrounded_proposals(repo_store: SkillStore, overrides: dict) -> None:
    result = skill_validator.validate({**GOOD_PROPOSAL, **overrides}, repo_store.list_skills(), "T2", REMAINING)
    assert result["decision"] == "rejected"
    assert "generality" in _failed(result)


def test_validator_allows_thresholds_in_procedures(repo_store: SkillStore) -> None:
    proposal = {**GOOD_PROPOSAL, "procedure": GOOD_PROPOSAL["procedure"] + ["Flag any group with n < 30 and report a 95% interval for its rate."]}
    result = skill_validator.validate(proposal, repo_store.list_skills(), "T2", REMAINING)
    assert "generality" not in _failed(result)
    assert result["decision"] == "accepted"


def test_validator_rejects_fewer_than_two_future_tasks(repo_store: SkillStore) -> None:
    existing = repo_store.list_skills()
    result = skill_validator.validate({**GOOD_PROPOSAL, "applicable_task_ids": ["T3", "T9"]}, existing, "T2", REMAINING)
    assert result["decision"] == "rejected" and _failed(result) == {"applicability"}
    # the current task never counts as a future task
    result = skill_validator.validate({**GOOD_PROPOSAL, "applicable_task_ids": ["T2", "T3"]}, existing, "T2", ["T2"] + REMAINING)
    assert result["decision"] == "rejected" and "applicability" in _failed(result)


def test_validator_rejects_missing_provenance(repo_store: SkillStore) -> None:
    result = skill_validator.validate({**GOOD_PROPOSAL, "source_feedback_ids": []}, repo_store.list_skills(), "T2", REMAINING)
    assert result["decision"] == "rejected" and _failed(result) == {"provenance"}


def test_validator_requests_revision_for_structural_gaps(repo_store: SkillStore) -> None:
    proposal = {**GOOD_PROPOSAL, "required_checks": [], "expected_artifacts": [], "failure_modes": [], "example": "short"}
    result = skill_validator.validate(proposal, repo_store.list_skills(), "T2", REMAINING)
    assert result["decision"] == "retry_revision"
    assert _failed(result) == {"optional_sections", "example_present"}
    assert result["duplicate_of"] is None
    thin = {**GOOD_PROPOSAL, "procedure": ["Do it.", "Check."]}
    result = skill_validator.validate(thin, repo_store.list_skills(), "T2", REMAINING)
    assert result["decision"] == "retry_revision" and "procedure_concrete" in _failed(result)


def test_validator_hard_failures_outrank_structural_gaps(repo_store: SkillStore) -> None:
    proposal = {**GOOD_PROPOSAL, "example": "", "source_feedback_ids": []}
    result = skill_validator.validate(proposal, repo_store.list_skills(), "T2", REMAINING)
    assert result["decision"] == "rejected" and {"provenance", "example_present"} <= _failed(result)
