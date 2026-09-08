"""Deterministic task executor (A6): ``execute(task_spec, plan, run_context) -> dict``.

The executor interprets a structured plan against the fixed component catalogue
(``src/analyses/catalogue.py``, transcribed from docs/LEAD_CATALOGUE_SKELETON.md),
runs the selected components in canonical order, saves artifacts under
``run_context["output_dir"]`` and returns the §5 execution-result shape.

Guarantees: plan problems never raise (they become structured ``errors``); an
exception inside one component is recorded as ``runtime_error`` and execution
continues; ``metrics.json`` and ``report.md`` are always written; no
``eval``/``exec``/shell/network; writes only inside ``output_dir``.
"""
from __future__ import annotations

import importlib
import json
import time
import traceback
from typing import Any

from src.analyses.catalogue import TASK_CATALOGUE, canonical_order, components_of
from src.analyses.common import SHARED_HANDLERS, Ctx, ExecutorError, to_native, write_report
from src.utils import REPO_ROOT, atomic_write_json, rel, sha256_text, utc_now

TASK_MODULES = {
    "T1": "src.analyses.t1_recon",
    "T2": "src.analyses.t2_portfolio",
    "T3": "src.analyses.t3_providers",
    "T4": "src.analyses.t4_denials",
    "T5": "src.analyses.t5_fraud_exploration",
    "T6": "src.analyses.t6_fraud_model",
    "T7": "src.analyses.t7_high_cost",
    "T8": "src.analyses.t8_brief",
    # experiment 5 (D-23): the held-out transfer tasks reuse the handler modules of the tasks they mirror
    "T9": "src.analyses.t4_denials",
    "T10": "src.analyses.t3_providers",
}
ERROR_TYPES = ("unknown_component", "invalid_param", "missing_column", "missing_dependency", "runtime_error")


def _err(etype: str, component: str | None, message: str) -> dict:
    return {"type": etype, "component": component, "message": str(message)[:500]}


def _match_option(options: list, value: Any) -> tuple[bool, Any]:
    """Option values are compared by string form (``"30"`` matches ``30``; ``"true"`` matches ``True``)."""
    sval = str(value).strip().lower()
    for opt in options:
        if str(opt).strip().lower() == sval:
            return True, opt
    return False, None


def normalise_params(component: dict, raw_params: dict | None) -> tuple[dict, list[str]]:
    """Fill defaults, coerce option values, reject unknown params / options. Returns (params, problems)."""
    declared = component["params"]
    problems: list[str] = []
    params: dict[str, Any] = {}
    raw = raw_params if isinstance(raw_params, dict) else {}
    for name, value in raw.items():
        spec = declared.get(name)
        if spec is None:
            problems.append(f"unknown parameter {name!r}; declared: {sorted(declared)}")
            continue
        if spec["multi"]:
            if isinstance(value, (str, int, float, bool)):
                value = [value]
            if not isinstance(value, list):
                problems.append(f"{name}: expected a list of options")
                continue
            matched, bad = [], []
            for v in value:
                ok, m = _match_option(spec["options"], v)
                (matched if ok else bad).append(m if ok else v)
            if bad:
                problems.append(f"{name}: {bad} not in options {spec['options']}")
                continue
            params[name] = list(dict.fromkeys(matched))
        else:
            ok, m = _match_option(spec["options"], value)
            if not ok:
                problems.append(f"{name}: {value!r} not in options {spec['options']}")
                continue
            params[name] = m
    for name, spec in declared.items():
        if name not in params and name not in raw:
            params[name] = list(spec["default"]) if spec["multi"] else spec["default"]
    return params, problems


def plan_sha256(plan: dict) -> str:
    return sha256_text(json.dumps(to_native(plan), sort_keys=True, ensure_ascii=False))


def _handlers(task_id: str) -> dict:
    module = importlib.import_module(TASK_MODULES[task_id])
    handlers = dict(SHARED_HANDLERS)
    handlers.update(getattr(module, "HANDLERS", {}))
    return handlers


def execute(task_spec: dict, plan: dict, run_context: dict) -> dict:
    """Run one task plan deterministically. Never raises for plan problems or component failures."""
    t0 = time.perf_counter()
    task_id = str(run_context.get("task_id") or (task_spec or {}).get("task_id") or "")
    attempt = int(run_context.get("attempt", 1))
    seed = int(run_context.get("seed", 42))
    output_dir = str(run_context.get("output_dir") or f"artifacts/tasks/{run_context.get('run_id', 'run')}/{run_context.get('condition', 'cond')}/{task_id}/attempt_{attempt}")
    run_context = {**run_context, "task_id": task_id, "attempt": attempt, "seed": seed, "output_dir": output_dir}
    plan = plan if isinstance(plan, dict) else {}
    errors: list[dict] = []
    executed: list[str] = []
    failed: list[str] = []

    if task_id not in TASK_CATALOGUE:
        errors.append(_err("runtime_error", None, f"unknown task_id {task_id!r}; known: {sorted(TASK_CATALOGUE)}"))
        return _finish(None, task_id, attempt, seed, output_dir, plan, executed, failed, errors, t0)

    spec = TASK_CATALOGUE[task_id]
    catalogue = components_of(task_id)
    declared_ids = {c.get("id") for c in (task_spec or {}).get("components", []) if isinstance(c, dict)}
    ctx = Ctx(task_id, spec["title"], run_context, plan, spec["input_tables"])
    ctx.metrics["plan_sha256"] = plan_sha256(plan)

    # ---- plan validation (never raises) -------------------------------------------
    selected: dict[str, dict] = {}
    for step in plan.get("steps") or []:
        cid = step.get("component") if isinstance(step, dict) else None
        if cid not in catalogue:
            hint = " (declared in task_spec but not in the executor catalogue)" if cid in declared_ids else ""
            errors.append(_err("unknown_component", cid, f"unknown component {cid!r}{hint}; valid ids: {canonical_order(task_id)}"))
            continue
        if cid in selected:
            errors.append(_err("invalid_param", cid, f"duplicate component {cid!r}; the first occurrence is kept"))
            continue
        params, problems = normalise_params(catalogue[cid], step.get("params"))
        if problems:
            errors.append(_err("invalid_param", cid, "; ".join(problems)))
            failed.append(cid)
            continue
        selected[cid] = params

    # ---- execution in canonical order ---------------------------------------------
    handlers = _handlers(task_id)
    for cid in canonical_order(task_id):
        if cid not in selected or cid == "write_report":
            continue
        missing = [d for d in catalogue[cid]["requires"] if d not in selected or d in failed]
        if missing:
            errors.append(_err("missing_dependency", cid, f"requires {missing} (not selected or failed)"))
            failed.append(cid)
            continue
        handler = handlers.get(cid)
        if handler is None:
            errors.append(_err("runtime_error", cid, "no handler implemented"))
            failed.append(cid)
            continue
        try:
            handler(ctx, selected[cid])
            executed.append(cid)
            errors.extend(ctx.soft_errors)  # partial failures inside an executed component
            ctx.soft_errors.clear()
        except ExecutorError as exc:
            errors.append(_err(exc.type, cid, f"{type(exc).__name__}: {exc}"))
            failed.append(cid)
        except Exception as exc:  # noqa: BLE001 - component bugs become recorded errors
            tb = traceback.format_exc().strip().splitlines()[-1]
            errors.append(_err("runtime_error", cid, f"{type(exc).__name__}: {exc} ({tb})"))
            failed.append(cid)

    # ---- metrics.json + report.md (always) ------------------------------------------
    status = "error" if not executed and "write_report" not in selected else ("partial" if failed or errors else "ok")
    if "tables" not in ctx.metrics:
        ctx.metrics["tables"] = ctx.loaded_tables()
    if "write_report" in selected:
        try:
            ctx.metrics["report"] = write_report(ctx, selected["write_report"], executed + ["write_report"], failed, errors, status)
            executed.append("write_report")
        except Exception as exc:  # noqa: BLE001
            errors.append(_err("runtime_error", "write_report", f"{type(exc).__name__}: {exc}"))
            failed.append("write_report")
            status = "partial" if executed else "error"
    else:
        try:
            write_report(ctx, None, executed, failed, errors, status)
        except Exception as exc:  # noqa: BLE001
            errors.append(_err("runtime_error", "report.md", f"{type(exc).__name__}: {exc}"))
    if not executed:
        status = "error"
    elif failed or errors:
        status = "partial"
    return _finish(ctx, task_id, attempt, seed, output_dir, plan, executed, failed, errors, t0, status)


def _finish(
    ctx: Ctx | None,
    task_id: str,
    attempt: int,
    seed: int,
    output_dir: str,
    plan: dict,
    executed: list[str],
    failed: list[str],
    errors: list[dict],
    t0: float,
    status: str = "error",
) -> dict:
    if ctx is None:  # unknown task: still honour "metrics.json and report.md are always written"
        from pathlib import Path

        from src.utils import atomic_write_text, ensure_dir

        out = Path(output_dir)
        out = out if out.is_absolute() else REPO_ROOT / out
        ensure_dir(out)
        metrics_path, report_path = out / "metrics.json", out / "report.md"
        metrics = {"task_id": task_id, "attempt": attempt, "seed": seed, "generated_at": utc_now(), "plan_sha256": plan_sha256(plan), "plan": to_native(plan), "tables": {}}
        atomic_write_json(metrics_path, metrics)
        atomic_write_text(report_path, f"# {task_id}\n\n## Summary\n\nExecution failed: {errors[0]['message'] if errors else 'unknown error'}\n")
        artifacts = [rel(metrics_path), rel(report_path)]
        rc: dict = {}
    else:
        rc = ctx.run_context
        metrics_path, report_path = ctx.path("metrics.json"), ctx.path("report.md")
        head = {
            "task_id": task_id,
            "run_id": rc.get("run_id"),
            "condition": rc.get("condition"),
            "attempt": attempt,
            "seed": seed,
            "generated_at": utc_now(),
            "plan_sha256": ctx.metrics.get("plan_sha256"),
            "plan": to_native(plan),
            "tables": ctx.metrics.get("tables", {}),
        }
        body = {k: v for k, v in ctx.metrics.items() if k not in head}
        metrics = to_native({**head, **body})
        atomic_write_json(metrics_path, metrics)
        artifacts = list(dict.fromkeys(ctx.artifacts + [rel(metrics_path), rel(report_path)]))
    return {
        "status": status,
        "task_id": task_id,
        "attempt": attempt,
        "output_dir": output_dir,
        "artifacts": artifacts,
        "metrics_path": rel(metrics_path),
        "report_path": rel(report_path),
        "metrics": metrics,
        "components_executed": executed,
        "components_failed": failed,
        "errors": errors,
        "seed": seed,
        "duration_seconds": round(time.perf_counter() - t0, 3),
    }
