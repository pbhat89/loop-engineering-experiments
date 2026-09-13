"""Summarise one experiment-7 run strictly from its logs (the write-up's source of numbers).

    python scripts/summarize_uw_run.py --run-id uw_001 [--json out.json]

Reads ``artifacts/uw/<run_id>/<arm>/cases.jsonl`` and joins the tier in from
``data/underwriting/goldens.json`` at analysis time - the tier is never written into a
run log, so nothing downstream can accidentally condition on it.

Prints, per arm: cases done, mean rating distance in ladder steps (whole run, first five,
last five, held-out), held-out files rated exactly right, decision accuracy (training and
over all 38 files), modifier F1, driver recall, questions asked, re-requests, unparseable
answers - then the trailing-five series, the per-tier means, and the three validation
checks the design registered in advance:

1. cases 1-3 must be a dead heat across the four non-asking arms;
2. the clean tier must stay flat for everyone;
3. the two held-out cases firing a rule that never appeared in training should be missed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.underwriting.data import goldens_by_case_id  # noqa: E402
from src.underwriting.run import load_config  # noqa: E402
from src.underwriting.scorer import DEFAULT_TRAILING_WINDOW, trailing_mean  # noqa: E402
from src.underwriting.state import ASKING_CONDITIONS, CONDITIONS  # noqa: E402
from src.utils import read_json, read_jsonl  # noqa: E402

NOVEL_RULES = ("HR-13", "HR-14")
DEAD_HEAT_CASES = 3


def default_window() -> int:
    """The trailing-mean window: ``trailing_window`` from config/underwriting.yaml.

    The config key used to be dead - it was copied into run.json but nothing read it, so
    editing it made the log claim a window the analysis never used. This is what reads it.
    The config file is loaded by the runner's own ``load_config`` rather than by a second
    copy of it here, so the summariser and the runner can never read different files.
    """
    try:
        return int((load_config() or {}).get("trailing_window", DEFAULT_TRAILING_WINDOW))
    except (TypeError, ValueError):
        return DEFAULT_TRAILING_WINDOW


def _mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def load_run(run_id: str, root: Path) -> dict:
    run_root = root / run_id
    goldens = goldens_by_case_id()
    out: dict = {
        "run_id": run_id,
        "run": read_json(run_root / "run.json", default={}) or {},
        "arms": {},
    }
    for condition in CONDITIONS:
        path = run_root / condition / "cases.jsonl"
        if not path.exists():
            continue
        records = read_jsonl(path)
        for r in records:
            r["tier"] = (goldens.get(r["case_id"]) or {}).get("tier")
            r["fired_rule_ids"] = (goldens.get(r["case_id"]) or {}).get("fired_rule_ids") or []
        out["arms"][condition] = records
    return out


def summarize(run_id: str, root: Path, window: int = DEFAULT_TRAILING_WINDOW) -> dict:
    data = load_run(run_id, root)
    summary: dict = {"run_id": run_id, "provider": (data["run"] or {}).get("provider"),
                     "mode": (data["run"] or {}).get("mode"),
                     "freeze_sha256": (data["run"] or {}).get("freeze_sha256"), "arms": {}}
    for condition, records in data["arms"].items():
        train = sorted([r for r in records if r["phase"] == "train"], key=lambda r: r["case_index"])
        held = sorted([r for r in records if r["phase"] == "holdout"], key=lambda r: r["case_index"])
        series = [float(r["ladder_distance"]) for r in train]
        by_tier = {}
        for tier in ("clean", "judgement", "compound"):
            by_tier[tier] = _mean([float(r["ladder_distance"]) for r in train if r["tier"] == tier])
        novel = [r for r in held if set(r["fired_rule_ids"]) & set(NOVEL_RULES)]
        # Every scored file, training then held-out. The write-up quotes the decision-correct
        # rate over all 38 files, not over the 30 training ones, so it has to be derivable here.
        every = train + held
        summary["arms"][condition] = {
            "train_cases": len(train),
            "holdout_cases": len(held),
            "mean_distance_train": _mean(series),
            "mean_distance_first5": _mean(series[:5]),
            "mean_distance_last5": _mean(series[-5:]),
            "mean_distance_holdout": _mean([float(r["ladder_distance"]) for r in held]),
            "mean_distance_holdout_novel": _mean([float(r["ladder_distance"]) for r in novel]),
            "decision_accuracy_train": _mean([1.0 if r["decision_match"] else 0.0 for r in train]),
            # over all 38 files (training + held-out) - the decision-correct figure the article publishes
            "decision_accuracy_all": _mean([1.0 if r["decision_match"] else 0.0 for r in every]),
            "decision_accuracy_holdout": _mean([1.0 if r["decision_match"] else 0.0 for r in held]),
            # held-out files whose rating matched exactly (ladder distance 0), out of holdout_cases
            "holdout_exact_match": sum(1 for r in held if float(r["ladder_distance"]) == 0.0),
            "modifier_f1_train": _mean([float(r["modifier_f1"] or 0.0) for r in train]),
            "driver_recall_train": _mean([float(r["driver_recall"] or 0.0) for r in train]),
            "questions_asked": sum(int(r.get("questions_asked") or 0) for r in records),
            "rerequests": sum(int(r.get("rerequests") or 0) for r in records),
            "unparseable": sum(1 for r in records if r.get("unparseable")),
            "memory_size_final": train[-1]["memory_size"] if train else 0,
            "nearest_distance_holdout": [r.get("nearest_distance") for r in held],
            "trailing_mean": trailing_mean(series, window),
            "per_case_distance": series,
            "by_tier": by_tier,
            "model_identifier": train[0]["model_identifier"] if train else None,
        }
    summary["validation"] = validation_checks(summary)
    return summary


def validation_checks(summary: dict) -> dict:
    arms = summary["arms"]
    non_asking = [c for c in arms if c not in ASKING_CONDITIONS]
    heads = {c: arms[c]["per_case_distance"][:DEAD_HEAT_CASES] for c in non_asking}
    dead_heat = len({tuple(v) for v in heads.values()}) <= 1 if heads else False
    clean = {c: arms[c]["by_tier"].get("clean") for c in arms}
    clean_values = [v for v in clean.values() if v is not None]
    clean_flat = (max(clean_values) - min(clean_values)) < 1e-9 if clean_values else False
    novel = {c: arms[c]["mean_distance_holdout_novel"] for c in arms}
    return {
        "dead_heat_first_3_non_asking": {"passed": dead_heat, "per_arm": heads},
        "clean_tier_flat": {"passed": clean_flat, "per_arm": clean},
        "novel_rule_holdout": {"per_arm": novel},
    }


def print_tables(summary: dict) -> None:
    print(f"\n=== run {summary['run_id']} | mode {summary['mode']} | freeze {(summary.get('freeze_sha256') or '')[:12]}")
    print(f"    provider {summary.get('provider')}")
    header = (
        f"{'arm':<15}{'train':>6}{'mean':>7}{'first5':>8}{'last5':>7}{'hold':>7}{'hxact':>7}{'novel':>7}"
        f"{'dec':>7}{'decAll':>8}{'modF1':>7}{'drvR':>7}{'quest':>7}{'rereq':>7}{'bad':>5}"
    )
    print(header)
    for condition, s in summary["arms"].items():
        fmt = lambda v: "-" if v is None else f"{v:.3f}"  # noqa: E731
        print(
            f"{condition:<15}{s['train_cases']:>6}{fmt(s['mean_distance_train']):>7}"
            f"{fmt(s['mean_distance_first5']):>8}{fmt(s['mean_distance_last5']):>7}"
            f"{fmt(s['mean_distance_holdout']):>7}"
            f"{str(s['holdout_exact_match']) + '/' + str(s['holdout_cases']):>7}"
            f"{fmt(s['mean_distance_holdout_novel']):>7}"
            f"{fmt(s['decision_accuracy_train']):>7}{fmt(s['decision_accuracy_all']):>8}"
            f"{fmt(s['modifier_f1_train']):>7}"
            f"{fmt(s['driver_recall_train']):>7}{s['questions_asked']:>7}{s['rerequests']:>7}{s['unparseable']:>5}"
        )
    print("  hxact = held-out files rated exactly right out of the 8; dec = decision correct over the 30 training"
          " files; decAll = decision correct over all 38 files")
    print("\nmean rating distance by tier (training)")
    print(f"{'arm':<15}{'clean':>8}{'judge':>8}{'compnd':>8}")
    for condition, s in summary["arms"].items():
        fmt = lambda v: "-" if v is None else f"{v:.3f}"  # noqa: E731
        t = s["by_tier"]
        print(f"{condition:<15}{fmt(t.get('clean')):>8}{fmt(t.get('judgement')):>8}{fmt(t.get('compound')):>8}")

    print("\ntrailing-5 mean rating distance, cases 1..n")
    for condition, s in summary["arms"].items():
        print(f"{condition:<15}" + " ".join(f"{v:.2f}" for v in s["trailing_mean"]))

    v = summary["validation"]
    print("\nvalidation checks")
    print(f"  cases 1-{DEAD_HEAT_CASES} dead heat across the non-asking arms: "
          f"{'PASS' if v['dead_heat_first_3_non_asking']['passed'] else 'FAIL'} "
          f"{v['dead_heat_first_3_non_asking']['per_arm']}")
    print(f"  clean tier flat for everyone: {'PASS' if v['clean_tier_flat']['passed'] else 'FAIL'} "
          f"{v['clean_tier_flat']['per_arm']}")
    print(f"  held-out novel-rule cases (everyone should miss these): {v['novel_rule_holdout']['per_arm']}")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--root", default=None, help="defaults to artifacts/uw")
    ap.add_argument("--window", type=int, default=None,
                    help="trailing-mean window; defaults to trailing_window in config/underwriting.yaml")
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    root = Path(args.root) if args.root else REPO_ROOT / "artifacts" / "uw"
    window = args.window if args.window is not None else default_window()
    summary = summarize(args.run_id, root, window)
    print_tables(summary)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
