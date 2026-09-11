"""Move everything one run left behind into ``archive/<folder>/`` (logs, checkpoints, task artifacts, transcripts, skills).

    uv run python scripts/archive_run.py --run-id run_004 --folder experiment-2_run_004 [--note "..."]

What moves (only for the given run id; other runs' records stay where they are):
  logs/{experiment,skill,graph,feedback}_events.jsonl   lines with run_id == <run_id> are cut out into the archive copy
  logs/runs/<run_id>.json, logs/checkpoints/<run_id>.sqlite
  artifacts/tasks/<run_id>/, artifacts/manual/<run_id>/, artifacts/memory/<run_id>/, skills/evolved/<run_id>/
  skills/index.json                                     entries whose run_id == <run_id> are cut out into the archive copy
The archive folder gets a README.md stub naming the run, the date and the note. Nothing is deleted; ``git mv`` is up to the caller.

Experiment 7 (the underwriting apprentice) keeps everything one run leaves behind under a
single directory, so it archives with ``--uw-run-id`` instead::

    python scripts/archive_run.py --uw-run-id uw_stub_smoke --folder experiment-7_stub_smoke
    python scripts/archive_run.py --uw-run-id uw_stub_full  --folder experiment-7_stub_smoke --logs-only

``artifacts/uw/<run_id>/`` moves wholesale. ``checkpoints/`` is never archived - it is a
LangGraph SQLite database the runner rebuilds, and it dwarfs everything else. ``--logs-only``
additionally leaves the request/response transcript behind, for a supporting run whose
per-case logs are the point.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.utils import ARTIFACTS_DIR, LOGS_DIR, SKILLS_DIR, atomic_write_json, ensure_dir, read_json, utc_now  # noqa: E402

JSONL = ("experiment_events", "skill_events", "graph_events", "feedback_events")


def split_jsonl(path: Path, run_id: str, out: Path) -> tuple[int, int]:
    """Write lines belonging to ``run_id`` to ``out`` and the rest back to ``path``. Returns (moved, kept)."""
    if not path.exists():
        return 0, 0
    keep, move = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rid = json.loads(line).get("run_id")
        except json.JSONDecodeError:
            rid = None
        (move if rid == run_id else keep).append(line)
    if move:
        ensure_dir(out.parent)
        out.write_text("\n".join(move) + "\n", encoding="utf-8")
    path.write_text(("\n".join(keep) + "\n") if keep else "", encoding="utf-8")
    return len(move), len(keep)


def move(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    ensure_dir(dst.parent)
    shutil.move(str(src), str(dst))
    return True


UW_SKIP_ALWAYS = ("checkpoints",)          # rebuilt by the runner; tens of megabytes of SQLite
UW_SKIP_LOGS_ONLY = ("requests", "responses")


def archive_uw_run(run_id: str, dest: Path, logs_only: bool = False) -> list[str]:
    """Move ``artifacts/uw/<run_id>/`` into the archive, minus the rebuildable checkpoints."""
    source = ARTIFACTS_DIR / "uw" / run_id
    if not source.is_dir():
        return [f"artifacts/uw/{run_id}: absent"]
    skip = set(UW_SKIP_ALWAYS) | (set(UW_SKIP_LOGS_ONLY) if logs_only else set())
    target = dest / run_id
    ensure_dir(target)
    report: list[str] = []
    for child in sorted(source.iterdir()):
        if child.name in skip:
            report.append(f"artifacts/uw/{run_id}/{child.name}: skipped")
            continue
        report.append(f"artifacts/uw/{run_id}/{child.name}: {'moved' if move(child, target / child.name) else 'absent'}")
    remaining = [p.name for p in source.iterdir()] if source.is_dir() else []
    if remaining:
        report.append(f"artifacts/uw/{run_id}: left in place -> {', '.join(sorted(remaining))}")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", default=None, help="a claims run id (experiments 1-6)")
    ap.add_argument("--uw-run-id", default=None, help="an underwriting run id (experiment 7)")
    ap.add_argument("--folder", required=True, help="name under archive/")
    ap.add_argument("--note", default="")
    ap.add_argument("--logs-only", action="store_true", help="experiment 7: leave the request/response transcript behind")
    args = ap.parse_args(argv)
    dest = REPO_ROOT / "archive" / args.folder
    ensure_dir(dest)

    if args.uw_run_id:
        report = archive_uw_run(args.uw_run_id, dest, logs_only=args.logs_only)
        readme = dest / "README.md"
        if not readme.exists():
            readme.write_text(
                f"# Archive - `{args.uw_run_id}` ({utc_now()[:10]})\n\n"
                f"{args.note or 'Moved here unchanged by scripts/archive_run.py --uw-run-id.'}\n\n"
                "## What moved\n\n" + "\n".join(f"- {line}" for line in report) + "\n",
                encoding="utf-8",
            )
        print("\n".join(report))
        print(f"archived {args.uw_run_id} -> {dest.relative_to(REPO_ROOT)}")
        return 0

    if not args.run_id:
        ap.error("one of --run-id or --uw-run-id is required")
    run_id = args.run_id
    report: list[str] = []
    for name in JSONL:
        moved, kept = split_jsonl(LOGS_DIR / f"{name}.jsonl", run_id, dest / "logs" / f"{name}.jsonl")
        report.append(f"logs/{name}.jsonl: moved {moved} lines, kept {kept}")
    for src, rel_dst in (
        (LOGS_DIR / "runs" / f"{run_id}.json", Path("logs/runs") / f"{run_id}.json"),
        (LOGS_DIR / "checkpoints" / f"{run_id}.sqlite", Path("logs/checkpoints") / f"{run_id}.sqlite"),
        (ARTIFACTS_DIR / "tasks" / run_id, Path("artifacts/tasks") / run_id),
        (ARTIFACTS_DIR / "manual" / run_id, Path("artifacts/manual") / run_id),
        (ARTIFACTS_DIR / "memory" / run_id, Path("artifacts/memory") / run_id),
        (SKILLS_DIR / "evolved" / run_id, Path("skills/evolved") / run_id),
    ):
        report.append(f"{rel_dst}: {'moved' if move(src, dest / rel_dst) else 'absent'}")
    index = read_json(SKILLS_DIR / "index.json", default={}) or {}
    mine = {k: v for k, v in index.items() if isinstance(v, dict) and v.get("run_id") == run_id}
    if mine:
        atomic_write_json(dest / "skills" / "index.json", mine)
        atomic_write_json(SKILLS_DIR / "index.json", {k: v for k, v in index.items() if k not in mine})
    report.append(f"skills/index.json: moved {len(mine)} entries, kept {len(index) - len(mine)}")
    readme = dest / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# Archive - `{run_id}` ({utc_now()[:10]})\n\n{args.note or 'Moved here unchanged by scripts/archive_run.py.'}\n\n"
            "## What moved\n\n" + "\n".join(f"- {line}" for line in report) + "\n",
            encoding="utf-8",
        )
    print("\n".join(report))
    print(f"archived {run_id} -> {dest.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
