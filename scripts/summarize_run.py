"""Summarise one or more runs strictly from the logs (the write-up's source of numbers).

    uv run python scripts/summarize_run.py --run-id run_001 [--run-id stub_001] [--json out.json]

Reads logs/experiment_events.jsonl, logs/skill_events.jsonl, logs/graph_events.jsonl and
logs/runs/<run_id>.json. Prints, per run and condition: tasks done, first-attempt passes,
mean final score, mean first-attempt score, retries, execution errors, operator steps,
stop reasons, skills retrieved / proposed / persisted / rejected / reused, and the
provider metadata recorded on the events. Nothing is computed from anything but the logs.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.utils import LOGS_DIR, read_json, read_jsonl  # noqa: E402

CONDITION_ORDER = [
    "baseline", "reflection_only", "skill_learning", "foundational_only", "self_refine", "feedback_memory", "self_refine_memory",
]


def summarize(run_id: str) -> dict:
    events = [r for r in read_jsonl(LOGS_DIR / "experiment_events.jsonl") if r.get("run_id") == run_id]
    skills = [r for r in read_jsonl(LOGS_DIR / "skill_events.jsonl") if r.get("run_id") == run_id]
    graph = [r for r in read_jsonl(LOGS_DIR / "graph_events.jsonl") if r.get("run_id") == run_id]
    run_manifest = read_json(LOGS_DIR / "runs" / f"{run_id}.json", default={}) or {}
    task_order = list((run_manifest.get("config") or {}).get("task_order") or [])
    out: dict = {"run_id": run_id, "mode": (run_manifest.get("config") or {}).get("mode"), "provider": run_manifest.get("provider"),
                 "freeze_sha256": (run_manifest.get("config") or {}).get("freeze_sha256"), "task_order": task_order, "conditions": {}}
    by_condition: dict[str, list[dict]] = defaultdict(list)
    for r in events:
        by_condition[r["condition"]].append(r)
    for condition in sorted(by_condition, key=lambda c: CONDITION_ORDER.index(c) if c in CONDITION_ORDER else 99):
        recs = by_condition[condition]
        done = {r["task_id"]: r for r in recs if r.get("status") == "done"}
        first = {r["task_id"]: r for r in recs if r.get("status") == "attempt" and r.get("attempt") == 1}
        tasks = [t for t in task_order if t in done] or sorted(done)
        final_scores = [done[t]["evaluator_score_total"] for t in tasks if done[t].get("evaluator_score_total") is not None]
        first_scores = [first[t]["evaluator_score_total"] for t in tasks if t in first and first[t].get("evaluator_score_total") is not None]
        sk = [r for r in skills if r.get("condition") == condition]
        skill_counts = Counter(r["event"] for r in sk)
        rejections = [
            {"task_id": r["task_id"], "proposal": r.get("proposal_name"), "failed_checks": [c["check_id"] for c in (r.get("checks") or []) if not c.get("passed")]}
            for r in sk if r["event"] == "skill_rejected"
        ]
        operator_requests = [r for r in graph if r.get("condition") == condition and r.get("event_type") == "operator_request"]
        validation_errors = [r for r in graph if r.get("condition") == condition and r.get("event_type") == "operator_validation_error"]
        providers = Counter((r.get("provider_mode"), r.get("operator"), r.get("model_identifier")) for r in recs)
        out["conditions"][condition] = {
            "tasks_done": len(done),
            "tasks": tasks,
            "final_scores": {t: done[t].get("evaluator_score_total") for t in tasks},
            "first_attempt_scores": {t: first[t].get("evaluator_score_total") for t in tasks if t in first},
            "first_attempt_passed": {t: bool(done[t].get("first_attempt_passed")) for t in tasks},
            "first_attempt_pass_rate": (sum(bool(done[t].get("first_attempt_passed")) for t in tasks) / len(tasks)) if tasks else None,
            "mean_final_score": round(sum(final_scores) / len(final_scores), 3) if final_scores else None,
            "mean_first_attempt_score": round(sum(first_scores) / len(first_scores), 3) if first_scores else None,
            "retries_total": sum(int(done[t].get("retry_count") or 0) for t in tasks),
            "execution_attempts_total": sum(int(done[t].get("execution_attempts") or 0) for t in tasks),
            "execution_errors_total": sum(int(done[t].get("execution_errors") or 0) for t in tasks),
            "operator_steps_used": max((int(done[t].get("operator_steps_used") or 0) for t in tasks), default=0),
            "operator_requests_logged": len(operator_requests),
            "operator_validation_errors": len(validation_errors),
            "stop_reasons": dict(Counter(done[t].get("stop_reason") for t in tasks)),
            "skills_retrieved_total": sum(len(done[t].get("skills_retrieved") or []) for t in tasks),
            "skills_reused_total": sum(len(done[t].get("skills_reused") or []) for t in tasks),
            "skills_created": [s for t in tasks for s in (done[t].get("skills_created") or [])],
            "skill_events": dict(skill_counts),
            "skill_rejections": rejections,
            "provider_metadata_on_events": [{"provider_mode": p[0], "operator": p[1], "model_identifier": p[2], "records": n} for p, n in providers.items()],
        }
    return out


def print_table(summary: dict) -> None:
    print(f"\n=== run {summary['run_id']} | mode {summary['mode']} | freeze {(summary.get('freeze_sha256') or '')[:12]} | provider {summary.get('provider')}")
    header = f"{'condition':<17}{'done':>5}{'1st-pass':>9}{'mean final':>11}{'mean 1st':>9}{'retries':>8}{'errors':>7}{'steps':>6}{'valid.err':>10}{'retrieved':>10}{'reused':>7}{'created':>8}"
    print(header)
    for c, s in summary["conditions"].items():
        fp = f"{s['first_attempt_pass_rate']:.0%}" if s["first_attempt_pass_rate"] is not None else "-"
        print(f"{c:<17}{s['tasks_done']:>5}{fp:>9}{str(s['mean_final_score']):>11}{str(s['mean_first_attempt_score']):>9}{s['retries_total']:>8}"
              f"{s['execution_errors_total']:>7}{s['operator_steps_used']:>6}{s['operator_validation_errors']:>10}{s['skills_retrieved_total']:>10}{s['skills_reused_total']:>7}{len(s['skills_created']):>8}")
    for c, s in summary["conditions"].items():
        if s["skill_events"]:
            print(f"  {c} skill events: {s['skill_events']}")
        for rej in s["skill_rejections"]:
            print(f"    rejected @{rej['task_id']}: {rej['proposal']} -> {rej['failed_checks']}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-id", action="append", required=True)
    p.add_argument("--json", default=None, help="write the full summary to this JSON file")
    args = p.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    summaries = [summarize(r) for r in args.run_id]
    for s in summaries:
        print_table(s)
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
