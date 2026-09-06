"""Python equivalent of scripts/bootstrap.sh, run_all.sh and verify.sh.

    uv run python scripts/pipeline.py bootstrap
    uv run python scripts/pipeline.py run-all  [--mode stub|manual] [--run-id ID] [--conditions a,b,c] [--skip-tests]
    uv run python scripts/pipeline.py verify

Every stage prints what it ran and appends its real outcome to docs/verification-log.md.
Nothing here calls a model; manual-mode runs stop at the first operator request per
condition and print the request paths for the operator loop (src/run_experiment.py).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.utils import ARTIFACTS_DIR, CONFIG_DIR, DATA_DIR, DOCS_DIR, GOLDENS_DIR, LOGS_DIR, read_json, read_yaml, rel  # noqa: E402

VERIFICATION_LOG = DOCS_DIR / "verification-log.md"
REQUIRED_FILES = [
    "README.md", "pyproject.toml", ".env.example", "config/experiment.yaml", "config/tasks.yaml", "config/rubric.yaml", "config/graph.yaml",
    "data/README.md", "data/processed/manifest.json", "skills/SKILL_SCHEMA.md", "docs/spec.md", "docs/plan.md", "docs/tasks.md",
    "docs/security-review.md", "docs/decision-log.md", "docs/writeup.md", "artifacts/dashboard/progress.html",
]


class Report:
    def __init__(self, stage: str):
        self.stage = stage
        self.lines: list[str] = []
        self.failures = 0
        self.started = time.monotonic()

    def record(self, label: str, ok: bool, detail: str = "") -> bool:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            self.failures += 1
        line = f"- {mark} — {label}" + (f" — {detail}" if detail else "")
        self.lines.append(line)
        print(line)
        return ok

    def flush(self) -> None:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        block = [f"\n### {stamp} — `scripts/pipeline.py {self.stage}` ({time.monotonic() - self.started:.0f}s, {self.failures} failure(s))", *self.lines, ""]
        VERIFICATION_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(VERIFICATION_LOG, "a", encoding="utf-8") as fh:
            fh.write("\n".join(block))
        print(f"\nappended {len(self.lines)} outcome(s) to {rel(VERIFICATION_LOG)}")


def run(cmd: list[str], timeout: int = 1800) -> tuple[int, str]:
    """Run a command from the repo root and return (exit code, last 40 lines of combined output)."""
    print(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
    tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-40:])
    return proc.returncode, tail


PY = [sys.executable]


# --------------------------------------------------------------------------- stages


def bootstrap(args: argparse.Namespace) -> int:
    rep = Report("bootstrap")
    code, out = run(["uv", "sync", "--extra", "dev"], timeout=900)
    rep.record("uv sync --extra dev", code == 0, out.splitlines()[-1] if out else "")
    code, out = run(PY + ["-m", "src.download_data"])
    rep.record("dataset present/downloaded (pinned revision)", code == 0, out.splitlines()[-1] if out else "")
    code, out = run(PY + ["-m", "src.profile_data"])
    rep.record("data profile + manifest", code == 0, out.splitlines()[-1] if out else "")
    rep.record("manifest.json exists", (DATA_DIR / "processed" / "manifest.json").exists())
    run(PY + ["-m", "src.agent_tracker", "show"])
    rep.flush()
    return 1 if rep.failures else 0


def run_all(args: argparse.Namespace) -> int:
    rep = Report(f"run-all --mode {args.mode}")
    # 1. configuration and runtime mode
    cfg = read_yaml(CONFIG_DIR / "experiment.yaml") if (CONFIG_DIR / "experiment.yaml").exists() else None
    rep.record("config/experiment.yaml loads", cfg is not None)
    from src.llm_provider import ProviderSettings, get_provider

    try:
        provider = get_provider(ProviderSettings(mode=args.mode))
        rep.record("runtime mode valid", True, json.dumps(provider.describe()))
    except Exception as exc:  # noqa: BLE001
        rep.record("runtime mode valid", False, str(exc))
        rep.flush()
        return 1
    # 2./3. dataset and profile
    code, out = run(PY + ["-m", "src.download_data"])
    rep.record("dataset verified", code == 0, out.splitlines()[-1] if out else "")
    if not (DATA_DIR / "processed" / "manifest.json").exists():
        code, out = run(PY + ["-m", "src.profile_data"])
        rep.record("data profiled", code == 0)
    # 4. designed topology
    try:
        from src.charts import render_topology
        from src.claims_graph import designed_topology

        path = render_topology(designed_topology())
        rep.record("LangGraph topology rendered", Path(path).exists(), rel(path))
    except Exception as exc:  # noqa: BLE001
        rep.record("LangGraph topology rendered", False, f"{type(exc).__name__}: {exc}")
    # 5. conditions
    from src.run_experiment import Runner

    conditions = [c.strip() for c in args.conditions.split(",") if c.strip()]
    run_id = args.run_id or (f"stub_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}" if args.mode == "stub" else f"run_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}")
    try:
        runner = Runner(run_id)
        if not runner.run:
            runner = Runner.init(run_id, conditions, args.mode)
        rep.record(f"run {run_id} initialised ({args.mode})", True, f"freeze {runner.config.freeze_sha256[:12]}")
        for condition in conditions:
            summary = runner.advance(condition)
            done = summary["status"] == "done"
            rep.record(f"{condition}: {summary['status']}", done or args.mode == "manual", summary.get("pending_request") or "")
            if summary.get("pending_request"):
                print(f"  OPERATOR NEEDED -> {summary['pending_request']}")
    except SystemExit as exc:
        rep.record("experiment run", False, str(exc))
    # 6. charts + dashboard
    try:
        from src import dashboard
        from src.charts import render_all

        figures = render_all(LOGS_DIR, ARTIFACTS_DIR / "figures")
        rep.record("figures rendered from logs", True, f"{len(figures)} files")
        rep.record("dashboard refreshed", Path(dashboard.render()).exists())
    except Exception as exc:  # noqa: BLE001
        rep.record("figures/dashboard", False, f"{type(exc).__name__}: {exc}")
    # 7. verification
    if not args.skip_tests:
        code, out = run(["uv", "run", "--extra", "dev", "pytest", "-q"], timeout=1800)
        rep.record("pytest -q", code == 0, out.splitlines()[-1] if out else "")
    rep.flush()
    return 1 if rep.failures else 0


def verify(args: argparse.Namespace) -> int:
    rep = Report("verify")
    for f in REQUIRED_FILES:
        rep.record(f"required file {f}", (REPO_ROOT / f).exists())
    found = sorted(p.name for p in (REPO_ROOT / "skills" / "foundational").glob("*.md"))
    rep.record("six foundational skills present", len(found) == 6, ", ".join(found))
    if GOLDENS_DIR.exists() and any(GOLDENS_DIR.iterdir()):
        code, out = run(PY + ["-m", "src.build_goldens", "--check"], timeout=900)
        rep.record("golden pack reproduces from data (build_goldens --check)", code == 0, out.splitlines()[-1] if out else "")
    else:
        rep.record("golden pack present", False, "goldens/ is empty")
    from src.run_experiment import verify_freeze

    sha, drift = verify_freeze()
    rep.record("freeze manifest matches data/goldens/tasks/rubric", not drift, (sha[:12] if sha else "") + ("; " + "; ".join(drift[:3]) if drift else ""))
    try:
        from src.experiment_logger import validate_logs

        problems = validate_logs(LOGS_DIR)
        rep.record("JSONL logs valid", not problems, "; ".join(problems[:3]))
    except ImportError as exc:
        rep.record("JSONL logs valid", False, f"experiment_logger unavailable: {exc}")
    status = read_json(LOGS_DIR / "agent_status.json", default={}) or {}
    rep.record("agent tracker maintained", bool(status.get("agents")), f"{len(status.get('agents', []))} agents, gates passed={status.get('acceptance_gates_passed')}")
    try:
        from src.claims_graph import build_claims_skill_graph, compiled_edges, designed_topology
        from src.graph_nodes import Services
        from src.llm_provider import FixtureProvider, ProviderSettings

        services = Services(provider=FixtureProvider(ProviderSettings(mode="stub")), execute_task=lambda *a: {}, evaluate=lambda *a: {}, skill_store=None,
                            validate_skill=lambda *a: {}, logger=None, rubric={}, load_golden=lambda s: {})
        graph = build_claims_skill_graph(services)
        designed = {(e["source"], e["target"]) for e in designed_topology()["edges"]}
        rep.record("LangGraph compiles and matches designed topology", designed == compiled_edges(graph))
    except Exception as exc:  # noqa: BLE001
        rep.record("LangGraph compiles", False, f"{type(exc).__name__}: {exc}")
    code, out = run(["uv", "run", "--extra", "dev", "pytest", "-q"], timeout=1800)
    rep.record("pytest -q", code == 0, out.splitlines()[-1] if out else "")
    rep.flush()
    return 1 if rep.failures else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("bootstrap")
    ra = sub.add_parser("run-all")
    ra.add_argument("--mode", default="stub", choices=["stub", "manual"])
    ra.add_argument("--run-id", default=None)
    ra.add_argument("--conditions", default="baseline,reflection_only,skill_learning")
    ra.add_argument("--skip-tests", action="store_true")
    sub.add_parser("verify")
    args = p.parse_args(argv)
    return {"bootstrap": bootstrap, "run-all": run_all, "verify": verify}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
