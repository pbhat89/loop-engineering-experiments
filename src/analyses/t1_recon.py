"""T1 — Dataset reconnaissance: schema, missingness, duplicates, date ranges (join_check is shared)."""
from __future__ import annotations

import pandas as pd

from src.analyses.common import Ctx, parse_dates, split_key


def schema_summary(ctx: Ctx, params: dict) -> None:
    schema, contract = {}, {}
    for name in ctx.input_tables:
        df = ctx.table(name)
        dtypes = [str(df[c].dtype) for c in df.columns]
        counts: dict[str, int] = {}
        for d in dtypes:
            counts[d] = counts.get(d, 0) + 1
        schema[name] = {"rows": int(len(df)), "n_columns": int(df.shape[1]), "dtypes": dict(sorted(counts.items()))}
        contract[name] = {"rows": int(len(df)), "columns": [{"name": c, "dtype": d} for c, d in zip(df.columns, dtypes)]}
        ctx.result("schema_summary", f"{name}: {len(df)} rows, {df.shape[1]} columns, dtypes {schema[name]['dtypes']}", source="metrics.json#schema")
    ctx.metrics["schema"] = schema
    ctx.write_json("data_contract.json", contract)


def missingness(ctx: Ctx, params: dict) -> None:
    scope = params["scope"]
    per_table, all_null, rows = {}, {}, []
    for name in ctx.input_tables:
        df = ctx.table(name)
        nulls = {c: int(df[c].isna().sum()) for c in df.columns}
        cols = list(df.columns)
        if scope == "top_10":
            cols = sorted(cols, key=lambda c: -nulls[c])[:10]  # stable: ties keep column order
        per_table[name] = {c: nulls[c] for c in cols}
        all_null[name] = [c for c in cols if len(df) > 0 and nulls[c] == len(df)]
        for c in cols:
            rows.append({"table": name, "column": c, "null_count": nulls[c], "null_share": nulls[c] / len(df) if len(df) else 0.0})
        total_null = sum(nulls.values())
        cells = int(len(df) * df.shape[1])
        ctx.result(
            "missingness",
            f"{name}: null cells share (all columns); all-null columns: {all_null[name] or 'none'}",
            value=total_null / cells if cells else 0.0,
            numerator=total_null,
            denominator=cells,
            source="metrics.json#missingness",
        )
    ctx.metrics["missingness"] = {"scope": scope, "per_table": per_table, "all_null_columns": all_null}
    ctx.write_csv("missingness.csv", pd.DataFrame(rows, columns=["table", "column", "null_count", "null_share"]))


def duplicate_check(ctx: Ctx, params: dict) -> None:
    out = {}
    for key in params["keys"]:
        table, cols = split_key(key)
        df = ctx.table(table)
        ctx.require_columns(df, cols, table)
        n_rows = int(len(df))
        n_unique = int(len(df[cols].drop_duplicates()))
        null_keys = int(df[cols].isna().any(axis=1).sum())
        dup = n_rows - n_unique
        out[key] = {"n_rows": n_rows, "n_unique": n_unique, "duplicate_rows": dup, "is_candidate_key": bool(dup == 0 and null_keys == 0)}
        ctx.result(
            "duplicate_check",
            f"{key}: duplicate rows (candidate key: {out[key]['is_candidate_key']})",
            value=dup / n_rows if n_rows else 0.0,
            numerator=dup,
            denominator=n_rows,
            source="metrics.json#duplicates",
        )
    ctx.metrics["duplicates"] = out


def date_ranges(ctx: Ctx, params: dict) -> None:
    out = {}
    for opt in params["columns"]:
        table, cols = split_key(opt)
        df = ctx.table(table)
        ctx.require_columns(df, cols, table)
        parsed = parse_dates(df[cols[0]])
        valid = parsed.dropna()
        out[opt] = {
            "min": valid.min().strftime("%Y-%m-%d") if len(valid) else None,
            "max": valid.max().strftime("%Y-%m-%d") if len(valid) else None,
            "unparseable": int(parsed.isna().sum()),
        }
        ctx.result("date_ranges", f"{opt}: {out[opt]['min']} … {out[opt]['max']}, unparseable rows", value=out[opt]["unparseable"], source="metrics.json#date_ranges")
    ctx.metrics["date_ranges"] = out
    if params["consistency_checks"]:
        mc = ctx.table("medical_claims")
        ctx.require_columns(mc, ["service_date_from", "service_date_to", "adjudication_date"], "medical_claims")
        sfrom, sto, adj = parse_dates(mc["service_date_from"]), parse_dates(mc["service_date_to"]), parse_dates(mc["adjudication_date"])
        cons = {
            "adjudication_before_service_end": int((adj < sto).sum()),
            "service_end_before_start": int((sto < sfrom).sum()),
        }
        ctx.metrics["date_consistency"] = cons
        for k, v in cons.items():
            ctx.result("date_ranges", f"medical_claims consistency — {k}", value=v, source="metrics.json#date_consistency")


HANDLERS = {
    "schema_summary": schema_summary,
    "missingness": missingness,
    "duplicate_check": duplicate_check,
    "date_ranges": date_ranges,
}
