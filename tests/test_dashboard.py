"""Dashboard and chart tests (A5): empty-logs rendering, populated rendering with a pending operator request and the
score grid, ``render_all`` on realistic generated logs, and the designed-topology renderer. Synthetic data only;
matplotlib runs with the Agg backend."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from src import dashboard
from src.charts import CONDITION_COLORS, CONDITION_ORDER, FIGURE_CATALOGUE, LIFECYCLE_FILE, MANIFEST_FILE, TOPOLOGY_FILE, render_all, render_topology
from src.claims_graph import designed_topology
from src.experiment_logger import read_status, summarize_runs
from tests.test_logging import CONDITIONS, PENDING_REQUEST, RUN_ID, WAITING_CONDITION, build_realistic_logs


@pytest.fixture(scope="module")
def generated_logs(tmp_path_factory) -> Path:
    logs_dir = tmp_path_factory.mktemp("exp_logs")
    build_realistic_logs(logs_dir)
    return logs_dir


def _render(tmp_path: Path, logs_dir: Path, figures_dir: Path) -> str:
    out = dashboard.render(out_path=tmp_path / "dashboard" / "progress.html", logs_dir=logs_dir, figures_dir=figures_dir)
    assert out.exists()
    return out.read_text(encoding="utf-8")


def _assert_self_contained(text: str) -> None:
    assert text.startswith("<!DOCTYPE html>")
    assert 'http-equiv="refresh"' in text
    assert "<script" not in text and "http://" not in text and "https://" not in text
    assert "manual_or_stub" not in text


# --------------------------------------------------------------------------- empty


def test_render_with_empty_logs_says_no_runs_yet(tmp_path):
    text = _render(tmp_path, tmp_path / "logs", tmp_path / "figures")
    _assert_self_contained(text)
    assert dashboard.NO_RUNS_TEXT in text
    assert "No agents registered yet" in text and "No figures rendered yet" in text
    assert "not yet passed" in text and "100% is reserved" in text
    assert "Log validation: no problems" in text


def test_render_never_claims_completion_before_gates(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "agent_status.json").write_text(
        json.dumps(
            {
                "updated_at": "2026-09-06T00:00:00+00:00",
                "acceptance_gates_passed": False,
                "agents": [{"agent_id": "A5", "role": "observability", "status": "review", "current_task": "x", "total_work_units": 8, "completed_work_units": 8, "percent_complete": 100.0}],
                "overall": {"total_work_units": 8, "completed_work_units": 8, "percent_complete": 99.5, "eta_label": "rough ETA ≈ 1 min"},
            }
        ),
        encoding="utf-8",
    )
    text = _render(tmp_path, logs, tmp_path / "figures")
    assert "99.5%" in text and "not yet passed" in text and "100% is reserved until they pass" in text
    assert "◆ review" in text  # glyph + word


# --------------------------------------------------------------------------- populated


def test_render_with_generated_logs_shows_pending_request_and_score_grid(generated_logs, tmp_path):
    text = _render(tmp_path, generated_logs, tmp_path / "figures")
    _assert_self_contained(text)
    assert dashboard.NO_RUNS_TEXT not in text
    assert RUN_ID in text
    # run header: the runner's provider dict is unpacked, never printed as a Python repr
    assert "mode <code>stub</code>" in text and "provider <code>stub</code>" in text
    assert "model <code>deterministic-fixture-v1</code>" in text and "operator <code>deterministic-fixture</code>" in text
    assert "{&#x27;" not in text and "provider_mode&#x27;" not in text
    for condition in CONDITIONS:
        assert condition in text
    status = read_status(generated_logs)
    waiting = status["runs"][RUN_ID]["conditions"][WAITING_CONDITION]
    assert PENDING_REQUEST in text
    assert waiting["waiting_since"] in text
    assert re.search(r"waiting for 7m \d\ds", text), "waited-for duration must be computed from waiting_since"
    assert "◆ waiting_operator" in text and "● done" in text
    assert "T4_a2_revise_plan_1.request.json" in text and "revise_plan" in text and "attempt 2" in text
    # score grid: final scores from the logs, first-attempt glyph, and the waiting cell
    summary = summarize_runs(generated_logs)["runs"][RUN_ID]["conditions"]
    for condition, cond in summary.items():
        for task_id, task in cond["tasks"].items():
            score = task["final"]["evaluator_score_total"]
            cell = f"{score:.2f}" + (f" {dashboard.FIRST_ATTEMPT_GLYPH}" if task["final"]["first_attempt_passed"] else "")
            assert f">{cell}</td>" in text, f"score cell for {condition}/{task_id} missing"
    assert f"{dashboard.FIRST_ATTEMPT_GLYPH} = passed on the first attempt" in text
    assert "◆ waiting</td>" in text
    assert "<th class='task'>T1</th>" in text and "<th class='task'>T8</th>" in text  # configured task order as columns
    # counts
    assert "Operator steps used / cap" in text and "/40" in text
    assert "1 condition(s) are waiting on an operator step" in text
    assert "Log validation: no problems" in text
    for colour in CONDITION_COLORS.values():
        assert colour in text  # swatches carry the fixed chart colours


# --------------------------------------------------------------------------- charts on the generated logs


def test_render_all_produces_every_figure_and_manifest(generated_logs, tmp_path):
    figures_dir = tmp_path / "figures"
    paths = render_all(generated_logs, figures_dir)
    expected = [file_name for file_name, _, _ in FIGURE_CATALOGUE.values()]
    assert [p.name for p in paths] == expected
    for p in paths:
        assert p.exists() and p.stat().st_size > 5_000, p
    assert (tmp_path / "graphs" / LIFECYCLE_FILE).exists()
    assert not [p for p in figures_dir.iterdir() if p.name.startswith(".")], "no temp files left behind"

    manifest = json.loads((figures_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    assert manifest["run_ids"] == [RUN_ID]
    assert manifest["condition_colors"] == CONDITION_COLORS
    assert [f["name"] for f in manifest["figures"]] == list(FIGURE_CATALOGUE)
    by_name = {f["name"]: f for f in manifest["figures"]}
    for name in FIGURE_CATALOGUE:
        assert by_name[name]["observations"] is True, name
        assert by_name[name]["sources"], name
    # baseline / reflection_only never touch skills: the accumulation figure must say so rather than draw a line for them
    assert any("no skill events" in n and "baseline" in n for n in by_name["skill_accumulation"]["notes"])
    rows = manifest["skill_utility_rows"]
    assert [r["skill_id"] for r in rows] == ["evolved_test_001"] and rows[0]["condition"] == "skill_learning" and rows[0]["reuse_count"] >= 1
    assert by_name["skill_lifecycle_graph"]["nodes"] >= 3

    # once rendered, the dashboard embeds them by relative path
    text = _render(tmp_path, generated_logs, figures_dir)
    for file_name in expected:
        assert f'src="../figures/{file_name}"' in text
    assert "No figures rendered yet" not in text
    assert "no skill events" in text  # manifest notes surface in the captions


def test_render_all_with_no_logs_draws_missing_as_missing(tmp_path):
    figures_dir = tmp_path / "figures"
    paths = render_all(tmp_path / "empty_logs", figures_dir)
    assert len(paths) == len(FIGURE_CATALOGUE) and all(p.exists() for p in paths)
    manifest = json.loads((figures_dir / MANIFEST_FILE).read_text(encoding="utf-8"))
    assert manifest["run_ids"] == []
    for fig in manifest["figures"]:
        assert fig["observations"] is False
        assert any("no observations" in n for n in fig["notes"]), fig["name"]


def test_render_topology_into_tmp_path(tmp_path):
    topology = designed_topology()
    assert list(topology["per_condition"]) == list(CONDITION_ORDER)
    out = render_topology(topology, out_path=tmp_path / "graphs" / TOPOLOGY_FILE)
    assert out == tmp_path / "graphs" / TOPOLOGY_FILE and out.exists() and out.stat().st_size > 20_000
    assert not [p for p in out.parent.iterdir() if p.name.startswith(".")]
