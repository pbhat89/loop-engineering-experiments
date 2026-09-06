"""Shared execution context, table access, writers, shared components and the report writer.

Everything here is deterministic given the plan, the seed and the data snapshot.
Tables are always loaded through ``src.profile_data.load_table`` (id/code columns as
``str``) and cached per run; artifacts are written only inside the run's output dir.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src.profile_data import RAW_DIR, load_table  # noqa: E402
from src.utils import REPO_ROOT, atomic_write_json, atomic_write_text, ensure_dir, rel  # noqa: E402

# --------------------------------------------------------------------------- #
# Conventions (docs/LEAD_CATALOGUE_SKELETON.md §0)                             #
# --------------------------------------------------------------------------- #
ID_FIELDS = ["claim_id", "member_id", "rendering_npi", "billing_npi", "plan_id", "auth_number", "rx_claim_id", "provider_npi"]
PROTECTED_ATTRIBUTES = ["member_sex", "member_race_ethnicity", "member_age_band", "member_income_band"]
LABEL_DERIVED_FIELDS = ["fraud_pattern_type"]
ADJUDICATED_STATUSES = ("Paid", "Denied", "Adjusted")
PAID_AND_DENIED = ("Paid", "Denied")
DENIED = "Denied"
MISSING_KEY = "(missing)"

DENOMINATOR_DEFINITIONS = {
    "all_claims": "all rows of medical_claims",
    "adjudicated_claims": "claim_status in {Paid, Denied, Adjusted} (Pended excluded)",
    "paid_and_denied": "claim_status in {Paid, Denied}",
}
NUMERATOR_DENIED = 'claim_status == "Denied"'

CAVEAT_SENTENCES = {
    "synthetic_data": "All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.",
    "sample_preview": "The data are a sample preview of the dataset; counts and distributions need not match the full release.",
    "descriptive_only": "The results are descriptive summaries; they estimate no effects and support no inference.",
    "association_not_causation": "Differences between groups are associations only and must not be read as causal effects.",
    "small_groups": "Groups below the minimum group size are flagged; their rates are unstable and should not be compared.",
    "class_imbalance": "The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.",
    "model_limitations": "The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.",
    "no_operational_use": "Nothing in this analysis is suitable for operational decisions about claims, members or providers.",
}


# --------------------------------------------------------------------------- #
# Errors mapped to the structured error types of the execution result         #
# --------------------------------------------------------------------------- #
class ExecutorError(Exception):
    type = "runtime_error"


class MissingColumnError(ExecutorError):
    type = "missing_column"


class InvalidParamError(ExecutorError):
    type = "invalid_param"


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def to_native(obj: Any) -> Any:
    """Recursively convert numpy/pandas scalars to JSON-safe Python values (NaN -> None)."""
    if isinstance(obj, dict):
        return {str(k): to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_native(v) for v in obj]
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer, int)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        f = float(obj)
        return None if (math.isnan(f) or math.isinf(f)) else f
    if obj is pd.NaT or (obj is not None and not isinstance(obj, str) and pd.api.types.is_scalar(obj) and pd.isna(obj)):
        return None
    if isinstance(obj, (pd.Timestamp,)):
        return obj.isoformat()
    if isinstance(obj, np.ndarray):
        return [to_native(v) for v in obj.tolist()]
    return obj


def key_str(value: Any) -> str:
    """Dictionary key for a group value: ``(missing)`` for nulls, plain str otherwise."""
    if value is None or (not isinstance(value, str) and pd.api.types.is_scalar(value) and pd.isna(value)):
        return MISSING_KEY
    return str(value)


def rate(numerator: int, denominator: int) -> float:
    return float(numerator) / float(denominator) if denominator else 0.0


def rate_dict(numerator: int, denominator: int, **extra: Any) -> dict:
    return {"value": rate(numerator, denominator), "numerator": int(numerator), "denominator": int(denominator), **extra}


def status_mask(df: pd.DataFrame, option: str) -> pd.Series:
    """Row mask for the denominator options of the skeleton."""
    if option == "all_claims":
        return pd.Series(True, index=df.index)
    if option == "adjudicated_claims":
        return df["claim_status"].isin(ADJUDICATED_STATUSES)
    if option == "paid_and_denied":
        return df["claim_status"].isin(PAID_AND_DENIED)
    raise InvalidParamError(f"unknown denominator option {option!r}")


def parse_dates(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def month_keys(series: pd.Series) -> tuple[pd.Series, int]:
    """``%Y-%m`` keys of a date column; unparseable rows dropped and counted."""
    parsed = parse_dates(series)
    unparseable = int(parsed.isna().sum())
    keys = parsed.dropna().dt.strftime("%Y-%m")
    return keys, unparseable


def sorted_counts(series: pd.Series) -> list[tuple[str, int]]:
    """(value, n) pairs including nulls, sorted by n desc then value asc - stable across pandas versions."""
    counts = series.value_counts(dropna=False)
    pairs = [(key_str(v), int(n)) for v, n in counts.items()]
    return sorted(pairs, key=lambda p: (-p[1], p[0]))


def split_key(option: str) -> tuple[str, list[str]]:
    """``table.col`` or ``table.col1+col2`` -> (table, [cols])."""
    table, _, cols = option.partition(".")
    if not table or not cols:
        raise InvalidParamError(f"malformed key option {option!r}")
    return table, cols.split("+")


def fmt_num(value: Any) -> str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, np.integer)):
        return f"{int(value)}"
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.6f}"
    return str(value)


# --------------------------------------------------------------------------- #
# Execution context                                                           #
# --------------------------------------------------------------------------- #
class Ctx:
    """State shared by the components of one execution."""

    def __init__(self, task_id: str, title: str, run_context: dict, plan: dict, input_tables: list[str]):
        self.task_id = task_id
        self.title = title
        self.run_context = run_context
        self.plan = plan
        self.input_tables = list(input_tables)
        self.seed = int(run_context.get("seed", 42))
        out = Path(str(run_context["output_dir"]))
        self.output_dir = ensure_dir(out if out.is_absolute() else REPO_ROOT / out)
        data_dir = run_context.get("data_dir")
        if data_dir:
            d = Path(str(data_dir))
            self.data_dir = d if d.is_absolute() else REPO_ROOT / d
        else:
            self.data_dir = RAW_DIR
        self._tables: dict[str, pd.DataFrame] = {}
        self.metrics: dict[str, Any] = {}
        self.artifacts: list[str] = []
        self.results: dict[str, list[dict]] = {}
        self.state: dict[str, Any] = {}  # cross-component objects (splits, matrices, ...)
        self.soft_errors: list[dict] = []  # non-fatal component errors, drained by the runner

    def soft_error(self, component: str, message: str, etype: str = "runtime_error") -> None:
        """Record an error for a component that still produced (partial) results."""
        self.soft_errors.append({"type": etype, "component": component, "message": str(message)[:500]})

    # -- tables -----------------------------------------------------------------
    def table(self, name: str) -> pd.DataFrame:
        if name not in self._tables:
            self._tables[name] = load_table(name, raw_dir=self.data_dir)
        return self._tables[name]

    def loaded_tables(self) -> dict[str, dict]:
        return {n: {"rows": int(len(df)), "columns": int(df.shape[1])} for n, df in sorted(self._tables.items())}

    @staticmethod
    def require_columns(df: pd.DataFrame, columns: list[str], table: str) -> None:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise MissingColumnError(f"{table}: missing column(s) {missing}")

    # -- artifacts --------------------------------------------------------------
    def path(self, name: str) -> Path:
        p = (self.output_dir / name).resolve()
        if self.output_dir.resolve() not in p.parents:
            raise ExecutorError(f"refusing to write outside output_dir: {name}")
        return p

    def artifact_rel(self, name: str) -> str:
        return rel(self.output_dir / name)

    def add_artifact(self, name: str) -> str:
        r = self.artifact_rel(name)
        if r not in self.artifacts:
            self.artifacts.append(r)
        return r

    def write_csv(self, name: str, df: pd.DataFrame) -> str:
        p = self.path(name)
        ensure_dir(p.parent)
        tmp = p.with_name(f".{p.name}.tmp")
        df.to_csv(tmp, index=False, lineterminator="\n")
        tmp.replace(p)
        return self.add_artifact(name)

    def write_json(self, name: str, obj: Any) -> str:
        atomic_write_json(self.path(name), to_native(obj))
        return self.add_artifact(name)

    def write_text(self, name: str, text: str) -> str:
        atomic_write_text(self.path(name), text)
        return self.add_artifact(name)

    def save_fig(self, fig: plt.Figure, name: str) -> str:
        fig.tight_layout()
        fig.savefig(self.path(name), dpi=100)
        plt.close(fig)
        return self.add_artifact(name)

    # -- report bullets ---------------------------------------------------------
    def result(
        self,
        component: str,
        text: str,
        *,
        value: Any = None,
        numerator: int | None = None,
        denominator: int | None = None,
        source: str | None = None,
    ) -> None:
        self.results.setdefault(component, []).append(
            {"text": text, "value": value, "numerator": numerator, "denominator": denominator, "source": source or f"metrics.json#{component}"}
        )


# --------------------------------------------------------------------------- #
# Shared components                                                           #
# --------------------------------------------------------------------------- #
def load_tables(ctx: Ctx, params: dict) -> None:
    tables = {}
    for name in ctx.input_tables:
        df = ctx.table(name)
        tables[name] = {"rows": int(len(df)), "columns": int(df.shape[1])}
    ctx.metrics["tables"] = tables
    for name, info in tables.items():
        ctx.result("load_tables", f"{name}: {info['rows']} rows, {info['columns']} columns", source="metrics.json#tables")


def _cardinality(left_unique: bool, right_unique: bool, matched_rows: int) -> str:
    if matched_rows == 0:
        return "no_match"
    if right_unique and left_unique:
        return "one_to_one"
    if right_unique:
        return "many_to_one"
    return "many_to_many"


def join_check(ctx: Ctx, params: dict) -> None:
    out: dict[str, dict] = {}
    for pair in params.get("pairs", []):
        left_spec, _, right_spec = pair.partition("->")
        lt, lcols = split_key(left_spec)
        rt, rcols = split_key(right_spec)
        left, right = ctx.table(lt), ctx.table(rt)
        ctx.require_columns(left, lcols, lt)
        ctx.require_columns(right, rcols, rt)
        lkey, rkey = left[lcols[0]], right[rcols[0]]
        right_unique = bool(rkey.notna().all() and rkey.is_unique)
        left_unique = bool(lkey.notna().all() and lkey.is_unique)
        matched_mask = lkey.isin(rkey.dropna().unique()) & lkey.notna()
        inner_rows = int(len(left[[lcols[0]]].merge(right[[rcols[0]]], left_on=lcols[0], right_on=rcols[0], how="inner")))
        out[pair] = {
            "cardinality": _cardinality(left_unique, right_unique, int(matched_mask.sum())),
            "rows_left": int(len(left)),
            "rows_after_inner_join": inner_rows,
            "unmatched_left": int((~matched_mask).sum()),
            "unmatched_left_denominator": int(len(left)),
            "right_key_unique": right_unique,
        }
        ctx.result(
            "join_check",
            f"{pair}: {out[pair]['cardinality']}, unmatched left rows",
            value=rate(out[pair]["unmatched_left"], out[pair]["rows_left"]),
            numerator=out[pair]["unmatched_left"],
            denominator=out[pair]["rows_left"],
            source="metrics.json#join_check",
        )
    ctx.metrics["join_check"] = out


# --------------------------------------------------------------------------- #
# Report writer                                                               #
# --------------------------------------------------------------------------- #
def render_bullet(b: dict, show_denominators: bool, cite_artifacts: bool) -> str:
    text = b["text"]
    if b.get("numerator") is not None and b.get("denominator") is not None and b.get("value") is not None:
        if show_denominators:
            text = f"{text}: {int(b['numerator'])} / {int(b['denominator'])} = {fmt_num(b['value'])}"
        else:
            text = f"{text}: {fmt_num(b['value'])}"
    elif b.get("value") is not None:
        text = f"{text}: {fmt_num(b['value'])}"
    if cite_artifacts:
        text = f"{text} [source: {b['source']}]"
    return f"- {text}"


def write_report(
    ctx: Ctx,
    params: dict | None,
    executed: list[str],
    failed: list[str],
    errors: list[dict],
    status: str,
) -> dict:
    """Write ``report.md`` in the fixed structure and return the ``report`` metric (params may be None
    when ``write_report`` was not selected: the file is still written with default formatting)."""
    p = params or {}
    caveats = [c for c in p.get("caveats", []) if c in CAVEAT_SENTENCES]
    show_den = bool(p.get("show_denominators", False))
    cite = bool(p.get("cite_artifacts", False))
    sections = ["Summary", "Results", "Artifacts"] + (["Caveats"] if caveats else []) + ["Method"]

    lines: list[str] = [f"# {ctx.task_id} — {ctx.title}", ""]
    lines += ["## Summary", ""]
    lines.append(
        f"Task {ctx.task_id} ({ctx.title}) for run `{ctx.run_context.get('run_id')}` / condition "
        f"`{ctx.run_context.get('condition')}`, attempt {ctx.run_context.get('attempt')}: status **{status}**; "
        f"{len(executed)} component(s) executed, {len(failed)} failed, {len(errors)} error(s) recorded."
    )
    if ctx.metrics.get("tables"):
        parts = [f"{n} ({v['rows']} rows)" for n, v in ctx.metrics["tables"].items()]
        lines.append(f"Tables: {', '.join(parts)}.")
    lines.append("")
    lines += ["## Results", ""]
    body_components = [c for c in executed if c != "write_report"]
    if not body_components:
        lines += ["No component produced results.", ""]
    for comp in body_components:
        lines.append(f"### {comp}")
        lines.append("")
        bullets = ctx.results.get(comp) or [{"text": "completed (no scalar results)", "value": None, "numerator": None, "denominator": None, "source": f"metrics.json#{comp}"}]
        lines += [render_bullet(b, show_den, cite) for b in bullets]
        lines.append("")
    if failed:
        lines.append("### Not executed")
        lines.append("")
        for e in errors:
            lines.append(f"- {e.get('component')}: {e.get('type')} — {e.get('message')}")
        lines.append("")
    lines += ["## Artifacts", ""]
    all_artifacts = list(ctx.artifacts) + [ctx.artifact_rel("metrics.json"), ctx.artifact_rel("report.md")]
    for a in dict.fromkeys(all_artifacts):
        lines.append(f"- `{a}`")
    lines.append("")
    if caveats:
        lines += ["## Caveats", ""]
        for c in caveats:
            lines.append(f"- **{c}**: {CAVEAT_SENTENCES[c]}")
        lines.append("")
    lines += ["## Method", ""]
    lines.append(f"- Seed: {ctx.seed}; plan sha256: `{ctx.metrics.get('plan_sha256', '')}`.")
    lines.append(f"- Components (canonical order): {', '.join(executed) if executed else 'none'}.")
    for step in ctx.plan.get("steps", []):
        lines.append(f"- `{step.get('component')}` params: `{to_native(step.get('params') or {})}`")
    lines.append(f"- Report options: show_denominators={show_den}, cite_artifacts={cite}, caveats={caveats}.")
    lines.append("")
    ctx.write_text("report.md", "\n".join(lines))
    return {"caveats": caveats, "show_denominators": show_den, "cite_artifacts": cite, "sections": sections}


SHARED_HANDLERS = {"load_tables": load_tables, "join_check": join_check}
