"""Evaluator 1.1 (D-19): caveat keywords must not be satisfied by run ids, condition names, paths or citations."""
from __future__ import annotations

from src.evaluator import EVALUATOR_VERSION, _caveat_scope

REPORT = """# T7 — High-cost claim identification

## Summary

Task T7 for run `run_003` / condition `baseline`, attempt 1: status **ok**. See [source: artifacts/tasks/run_003/baseline/T7/attempt_1/metrics.json].

## Artifacts

- `artifacts/tasks/run_003/baseline/T7/attempt_1/model_metrics.json`
"""


def test_version_bumped():
    assert EVALUATOR_VERSION == "1.2"


def test_condition_name_and_paths_are_stripped_without_caveat_section():
    scoped = _caveat_scope(REPORT, ("run_003", "baseline")).lower()
    assert "baseline" not in scoped and "run_003" not in scoped and "artifacts/" not in scoped and "[source:" not in scoped
    assert "status" in scoped  # the rest of the text is still available for genuine phrasing


def test_only_caveat_or_limitation_sections_count_when_present():
    text = REPORT + "\n## Caveats\n\n- These are untuned baseline models; a limitation of a single split.\n\n## Method\n\n- baseline plan\n"
    scoped = _caveat_scope(text, ("run_003", "baseline")).lower()
    assert "limitation" in scoped and "untuned" in scoped
    assert "plan" not in scoped  # the Method section is out of scope
    assert "baseline" not in scoped  # condition name removed even inside the caveat section


def test_other_condition_names_are_stripped_too():
    scoped = _caveat_scope("Condition skill_learning wrote this reflection_only note about foundational_only skills.").lower()
    for name in ("skill_learning", "reflection_only", "foundational_only"):
        assert name not in scoped
