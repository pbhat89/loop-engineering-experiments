"""Experiment 7: the summariser's published measures, the figure script's output
directory and stub watermark, and the configuration keys the code actually reads.

These cover the behaviours a code review found broken:

* the figure script defaulted its output to the article's committed assets folder, so
  following the reproduction guide silently replaced the published charts;
* stub figures were only watermarked when the run id began ``uw_stub``, while the docs
  tell people to run stubs as ``uw_demo``;
* the summariser could not reproduce the decision-correct column the article publishes
  (it is computed over all 38 files, not the 30 training ones) nor the held-out
  files-rated-exactly-right count;
* ``max_questions`` and ``trailing_window`` sat in the config unread while being copied
  into ``run.json``, so editing them made the log claim a value nothing used.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from src.underwriting import run as runner
from src.utils import CONFIG_DIR, read_yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from summarize_uw_run import default_window, summarize  # noqa: E402

ASSETS = REPO_ROOT / "articles" / "underwriting-apprentice" / "assets"
UW_001 = REPO_ROOT / "artifacts" / "uw"
ARM_FIELDS = {
    "modifier_f1": 1.0, "driver_recall": 1.0, "memory_size": 0,
    "nearest_distance": None, "questions_asked": 0, "rerequests": 0,
    "unparseable": False, "model_identifier": "stub",
}


def _load_make_figures():
    """Import the figure script by path; it is not an importable package module."""
    path = ASSETS / "make_figures.py"
    spec = importlib.util.spec_from_file_location("uw_make_figures", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_run(root: Path, run_id: str, arm: str, train: list[tuple], held: list[tuple], mode: str) -> None:
    """A minimal run on disk: run.json plus one arm's cases.jsonl.

    Each tuple is ``(ladder_distance, decision_match)``; case ids are real ones so the
    tier/rule join in ``load_run`` behaves as it does for a real run.
    """
    run_root = root / run_id
    run_root.mkdir(parents=True, exist_ok=True)
    (run_root / "run.json").write_text(json.dumps({"run_id": run_id, "mode": mode}), encoding="utf-8")
    lines = []
    for phase, rows in (("train", train), ("holdout", held)):
        for i, (distance, decision_match) in enumerate(rows, start=1):
            lines.append(json.dumps({
                "case_id": f"UW-{'T' if phase == 'train' else 'H'}{i:02d}",
                "case_index": i, "phase": phase,
                "ladder_distance": distance, "decision_match": decision_match,
                **ARM_FIELDS,
            }))
    arm_dir = run_root / arm
    arm_dir.mkdir(parents=True, exist_ok=True)
    (arm_dir / "cases.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------- the summariser's new measures


def test_decision_accuracy_is_reported_over_every_file_not_only_training(tmp_path):
    # 3 of 4 training decisions right, 1 of 2 held-out: 0.75 training, 4/6 overall.
    _write_run(tmp_path, "uw_x", "notebook",
               train=[(0, True), (1, True), (0, True), (2, False)],
               held=[(0, True), (1, False)], mode="stub")
    arm = summarize("uw_x", tmp_path)["arms"]["notebook"]
    assert arm["decision_accuracy_train"] == 0.75
    assert arm["decision_accuracy_all"] == round(4 / 6, 4)
    assert arm["decision_accuracy_holdout"] == 0.5


def test_held_out_files_rated_exactly_right_are_counted(tmp_path):
    _write_run(tmp_path, "uw_x", "notebook",
               train=[(0, True)],
               held=[(0, True), (0, True), (1, True), (2, False)], mode="stub")
    arm = summarize("uw_x", tmp_path)["arms"]["notebook"]
    assert arm["holdout_exact_match"] == 2
    assert arm["holdout_cases"] == 4


def test_the_existing_summary_keys_all_survive(tmp_path):
    """New measures were added alongside the old ones, never by renaming them."""
    _write_run(tmp_path, "uw_x", "notebook", train=[(0, True)], held=[(1, False)], mode="stub")
    arm = summarize("uw_x", tmp_path)["arms"]["notebook"]
    for key in ("train_cases", "holdout_cases", "mean_distance_train", "mean_distance_first5",
                "mean_distance_last5", "mean_distance_holdout", "mean_distance_holdout_novel",
                "decision_accuracy_train", "modifier_f1_train", "driver_recall_train",
                "questions_asked", "rerequests", "unparseable", "memory_size_final",
                "nearest_distance_holdout", "trailing_mean", "per_case_distance", "by_tier",
                "model_identifier"):
        assert key in arm, key


@pytest.mark.parametrize(
    "arm,decision_all,exact",
    [("new_joiner", 0.7105, 2), ("notebook", 0.8947, 6), ("written_rules", 0.8947, 6), ("precedent", 0.8421, 5)],
)
def test_the_summariser_reproduces_the_numbers_the_article_publishes(arm, decision_all, exact):
    """uw_001 is the run the write-up quotes: 71/89/89/84 percent decision-correct over
    all 38 files, and 2/6/6/5 of the 8 held-out files rated exactly right."""
    if not (UW_001 / "uw_001").exists():  # pragma: no cover - the run is committed
        pytest.skip("artifacts/uw/uw_001 not present")
    summary = summarize("uw_001", UW_001)["arms"][arm]
    assert summary["decision_accuracy_all"] == decision_all
    assert summary["holdout_exact_match"] == exact
    assert summary["holdout_cases"] == 8


# --------------------------------------------------------- the figure script


def test_figures_default_into_the_runs_own_folder_and_never_the_article_assets(tmp_path, capsys):
    """The reproduction guide says to run this with your own run id. Doing so must not
    touch the three PNGs the article publishes."""
    module = _load_make_figures()
    before = {p.name: p.read_bytes() for p in ASSETS.glob("*.png")}
    assert before, "the article's committed figures are missing"

    _write_run(tmp_path, "uw_demo", "notebook", train=[(2, False), (1, True), (0, True)],
               held=[(0, True), (1, False)], mode="stub")
    assert module.main(["--run-id", "uw_demo", "--root", str(tmp_path)]) == 0

    out = tmp_path / "uw_demo" / "figures"
    for name in ("learning_curve.png", "holdout.png", "what_each_gets.png"):
        assert (out / name).exists(), name
    assert {p.name: p.read_bytes() for p in ASSETS.glob("*.png")} == before
    # and the destination is stated on stdout, so it is never a guess
    assert str(out) in capsys.readouterr().out


def test_an_explicit_out_is_still_honoured(tmp_path):
    module = _load_make_figures()
    _write_run(tmp_path, "uw_demo", "notebook", train=[(1, True)], held=[(0, True)], mode="stub")
    chosen = tmp_path / "somewhere-else"
    assert module.main(["--run-id", "uw_demo", "--root", str(tmp_path), "--out", str(chosen)]) == 0
    assert (chosen / "learning_curve.png").exists()
    assert not (tmp_path / "uw_demo" / "figures").exists()


@pytest.mark.parametrize(
    "run_id,mode,expected",
    [
        ("uw_demo", "stub", True),      # the id the docs actually tell people to use
        ("uw_001", "stub", True),       # any name at all, if the run was a stub
        ("uw_stub_smoke", None, True),  # the old prefix trigger is kept as a fallback
        ("uw_001", "manual", False),    # a real run is never watermarked
        ("uw_demo", None, False),
    ],
)
def test_a_stub_run_is_watermarked_whatever_it_is_called(run_id, mode, expected):
    assert _load_make_figures().is_stub_run(run_id, mode) is expected


def test_the_watermark_actually_reaches_the_image(tmp_path):
    """Rendering the same figure as a stub and as a real run must not produce the same file."""
    module = _load_make_figures()
    stub_dir, real_dir = tmp_path / "stub", tmp_path / "real"
    stub_dir.mkdir()
    real_dir.mkdir()
    module.fig_what_each_gets("uw_demo", stub_dir, "stub")
    module.fig_what_each_gets("uw_demo", real_dir, "manual")
    assert (stub_dir / "what_each_gets.png").read_bytes() != (real_dir / "what_each_gets.png").read_bytes()


# --------------------------------------------------------- the configuration keys


def test_trailing_window_is_read_from_the_config_file():
    configured = int(read_yaml(CONFIG_DIR / "underwriting.yaml")["trailing_window"])
    assert default_window() == configured


def test_max_questions_is_read_from_the_config_file(tmp_path):
    config = {"artifacts_root": str(tmp_path), "mode": "stub", "max_questions": 1}
    services, _ = runner.build_services("uw_q", config, "stub", "learner", "freeze")
    assert services.max_questions == 1
    services, _ = runner.build_services("uw_q", {"artifacts_root": str(tmp_path), "mode": "stub"},
                                        "stub", "learner", "freeze")
    assert services.max_questions == 4  # the state.py default when the config is silent


def test_the_question_cap_changes_what_the_senior_is_asked(tmp_path):
    """Not just carried: the cap reaches the oracle and bounds the logged questions."""
    def asked(limit: int | None) -> list[int]:
        root = tmp_path / f"cap{limit}"
        config = {"artifacts_root": str(root), "mode": "stub", "poll_interval_seconds": 0.01}
        if limit is not None:
            config["max_questions"] = limit
        runner.advance("uw_q", "ask_senior", "train", mode="stub", config=config, max_cases=6, quiet=True)
        path = root / "uw_q" / "ask_senior" / "cases.jsonl"
        return [json.loads(line)["questions_asked"] for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert max(asked(None)) > 1, "the stub never asks more than one question; the cap proves nothing"
    assert max(asked(1)) == 1


def test_the_config_advertises_no_key_the_code_ignores():
    """Keys that nothing read used to sit here, two of them copied into run.json so the
    log claimed values the code never used. Each of these now has a reader."""
    config = read_yaml(CONFIG_DIR / "underwriting.yaml")
    for gone in ("experiment", "seed", "conditions", "phases", "data_dir"):
        assert gone not in config, f"{gone} is back in the config but nothing reads it"
    for kept in ("max_questions", "trailing_window", "max_rerequests", "precedent_k",
                 "mode", "operator", "model_identifier", "stub_operator", "artifacts_root",
                 "poll_interval_seconds", "poll_timeout_seconds"):
        assert kept in config, kept
