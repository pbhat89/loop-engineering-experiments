"""T2 — Claims portfolio description: volumes, denial rate, fraud prevalence, financials, monthly trend."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.analyses.common import (
    DENIED,
    DENOMINATOR_DEFINITIONS,
    NUMERATOR_DENIED,
    Ctx,
    month_keys,
    rate,
    sorted_counts,
    status_mask,
)


def claim_volume(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, params["by"], "medical_claims")
    total = int(len(mc))
    by: dict[str, dict] = {}
    for col in params["by"]:
        pairs = sorted_counts(mc[col])
        by[col] = {v: {"n": n, "share": rate(n, total)} for v, n in pairs}
        if params["figure"]:
            name = "claims_status_distribution.png" if col == "claim_status" else f"claim_volume_by_{col}.png"
            fig, ax = plt.subplots(figsize=(8, 4.5))
            ax.bar([v for v, _ in pairs], [n for _, n in pairs], color="#4C72B0")
            ax.set_title(f"Claim volume by {col} (n={total})")
            ax.set_ylabel("claims")
            ax.tick_params(axis="x", rotation=45 if len(pairs) > 6 else 0)
            for lbl in ax.get_xticklabels():
                lbl.set_horizontalalignment("right" if len(pairs) > 6 else "center")
            ctx.save_fig(fig, name)
    ctx.metrics["claim_volume"] = {"total_claims": total, "by": by}
    ctx.result("claim_volume", "Total claims", value=total, source="metrics.json#claim_volume.total_claims")
    for col, values in by.items():
        for v, info in values.items():
            ctx.result("claim_volume", f"{col} = {v}: share of claims", value=info["share"], numerator=info["n"], denominator=total, source=f"metrics.json#claim_volume.by.{col}")


def denial_rate(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, ["claim_status"], "medical_claims")
    opt = params["denominator"]
    den_mask = status_mask(mc, opt)
    num = int(((mc["claim_status"] == DENIED) & den_mask).sum())
    den = int(den_mask.sum())
    ctx.metrics["denial_rate"] = {
        "value": rate(num, den),
        "numerator": num,
        "denominator": den,
        "numerator_definition": NUMERATOR_DENIED,
        "denominator_definition": DENOMINATOR_DEFINITIONS[opt],
        "denominator_option": opt,
    }
    ctx.result("denial_rate", f"Denial rate (denominator: {opt})", value=rate(num, den), numerator=num, denominator=den, source="metrics.json#denial_rate")


def fraud_prevalence(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, ["claim_status", "fraud_label"], "medical_claims")
    opt = params["denominator"]
    den_mask = status_mask(mc, opt)
    num = int(((mc["fraud_label"] == 1) & den_mask).sum())
    den = int(den_mask.sum())
    ctx.metrics["fraud_prevalence"] = {"value": rate(num, den), "numerator": num, "denominator": den, "denominator_option": opt}
    ctx.result("fraud_prevalence", f"Fraud prevalence (denominator: {opt})", value=rate(num, den), numerator=num, denominator=den, source="metrics.json#fraud_prevalence")


def financial_summary(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    cols = params["amount_columns"]
    ctx.require_columns(mc, cols, "medical_claims")
    quantiles = params["statistics"] == "sum_mean_quantiles"
    out, rows = {}, []
    for col in cols:
        s = pd.to_numeric(mc[col], errors="coerce").dropna()
        info = {"n": int(len(s)), "sum": float(s.sum()), "mean": float(s.mean()) if len(s) else 0.0}
        if quantiles:
            info.update(
                {
                    "median": float(np.percentile(s.to_numpy(), 50)) if len(s) else 0.0,
                    "p90": float(np.percentile(s.to_numpy(), 90)) if len(s) else 0.0,
                    "p99": float(np.percentile(s.to_numpy(), 99)) if len(s) else 0.0,
                }
            )
        out[col] = info
        rows.append({"column": col, **info})
        ctx.result("financial_summary", f"{col}: sum", value=info["sum"], source="metrics.json#financial_summary")
        ctx.result("financial_summary", f"{col}: mean", value=info["mean"], source="metrics.json#financial_summary")
        if quantiles:
            ctx.result("financial_summary", f"{col}: median / p90 / p99 = {info['median']:.2f} / {info['p90']:.2f} / {info['p99']:.2f}", source=ctx.artifact_rel("financial_summary.csv"))
    ctx.metrics["financial_summary"] = out
    ctx.write_csv("financial_summary.csv", pd.DataFrame(rows))


def monthly_trend(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    date_col = params["date_column"]
    metrics = params["metrics"]
    ctx.require_columns(mc, [date_col] + (["paid_amount"] if "paid_amount_sum" in metrics else []), "medical_claims")
    keys, unparseable = month_keys(mc[date_col])
    months = sorted(keys.unique().tolist())
    series: dict[str, dict] = {}
    frame = pd.DataFrame({"month": months})
    if "claim_count" in metrics:
        counts = keys.value_counts()
        series["claim_count"] = {m: int(counts.get(m, 0)) for m in months}
        frame["claim_count"] = [series["claim_count"][m] for m in months]
    if "paid_amount_sum" in metrics:
        paid = pd.to_numeric(mc.loc[keys.index, "paid_amount"], errors="coerce").fillna(0.0)
        sums = paid.groupby(keys).sum()
        series["paid_amount_sum"] = {m: float(sums.get(m, 0.0)) for m in months}
        frame["paid_amount_sum"] = [series["paid_amount_sum"][m] for m in months]
    ctx.metrics["monthly_trend"] = {
        "date_column": date_col,
        "n_months": int(len(months)),
        "first_month": months[0] if months else None,
        "last_month": months[-1] if months else None,
        "unparseable_dates": int(unparseable),
        "series": series,
    }
    ctx.write_csv("monthly_trend.csv", frame)
    plot_metric = "claim_count" if "claim_count" in series else (metrics[0] if metrics else None)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    if plot_metric and months:
        ax.plot(range(len(months)), [series[plot_metric][m] for m in months], marker="o", color="#4C72B0")
        step = max(1, len(months) // 12)
        ax.set_xticks(range(0, len(months), step))
        ax.set_xticklabels(months[::step], rotation=45, ha="right")
    ax.set_title(f"Monthly {plot_metric or 'volume'} by {date_col}")
    ax.set_ylabel(plot_metric or "")
    ctx.save_fig(fig, "monthly_claim_volume.png")
    ctx.result("monthly_trend", f"Date column {date_col}: months covered", value=len(months), source="metrics.json#monthly_trend")
    ctx.result("monthly_trend", f"Range {months[0] if months else '-'} … {months[-1] if months else '-'}; unparseable dates", value=unparseable, source="metrics.json#monthly_trend.unparseable_dates")
    for m_name, vals in series.items():
        ctx.result("monthly_trend", f"{m_name}: mean per month", value=float(np.mean(list(vals.values()))) if vals else 0.0, source=ctx.artifact_rel("monthly_trend.csv"))


HANDLERS = {
    "claim_volume": claim_volume,
    "denial_rate": denial_rate,
    "fraud_prevalence": fraud_prevalence,
    "financial_summary": financial_summary,
    "monthly_trend": monthly_trend,
}
