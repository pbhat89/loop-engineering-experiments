"""T4 — Denial analysis: denial code ranking (with missing-code quantification) and denial rates by segment."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.analyses.common import DENIED, Ctx, key_str, rate, sorted_counts, status_mask


def denial_code_ranking(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, ["claim_status", "denial_code_carc"], "medical_claims")
    scope, quantify = params["scope"], params["quantify_missing"]
    denied_mask = mc["claim_status"] == DENIED
    base = mc[denied_mask] if scope == "denied_claims" else mc
    n_scope = int(len(base))
    codes = [
        {"code": code, "n": n, "share": rate(n, n_scope)}
        for code, n in sorted_counts(base["denial_code_carc"].dropna())
    ]
    out: dict = {"scope": scope, "quantify_missing": quantify, "codes": codes}
    missing = mc["denial_code_carc"].isna()
    if quantify != "none":
        mdc = {
            "definition": "denial_code_carc is null",
            "overall": int(missing.sum()),
            "overall_denominator": int(len(mc)),
            "among_denied": int((missing & denied_mask).sum()),
            "among_denied_denominator": int(denied_mask.sum()),
        }
        if quantify == "by_status":
            mdc["by_status"] = {
                key_str(s): {"missing": int((missing & (mc["claim_status"] == s)).sum()), "n": int((mc["claim_status"] == s).sum())}
                for s in sorted(mc["claim_status"].dropna().unique().tolist())
            }
        out["missing_denial_codes"] = mdc
    ctx.metrics["denial_code_ranking"] = out
    ctx.write_csv("denial_code_ranking.csv", pd.DataFrame(codes, columns=["code", "n", "share"]))
    ctx.result("denial_code_ranking", f"Scope {scope}: claims in scope {n_scope}; distinct denial codes", value=len(codes), source="metrics.json#denial_code_ranking")
    for c in codes:
        ctx.result("denial_code_ranking", f"Code {c['code']}: share of claims in scope", value=c["share"], numerator=c["n"], denominator=n_scope, source=ctx.artifact_rel("denial_code_ranking.csv"))
    if quantify != "none":
        mdc = out["missing_denial_codes"]
        ctx.result("denial_code_ranking", "Missing denial code overall", value=rate(mdc["overall"], mdc["overall_denominator"]), numerator=mdc["overall"], denominator=mdc["overall_denominator"], source="metrics.json#denial_code_ranking.missing_denial_codes")
        ctx.result("denial_code_ranking", "Missing denial code among denied claims", value=rate(mdc["among_denied"], mdc["among_denied_denominator"]), numerator=mdc["among_denied"], denominator=mdc["among_denied_denominator"], source="metrics.json#denial_code_ranking.missing_denial_codes")
        for s, info in (mdc.get("by_status") or {}).items():
            ctx.result("denial_code_ranking", f"Missing denial code among status {s}", value=rate(info["missing"], info["n"]), numerator=info["missing"], denominator=info["n"], source="metrics.json#denial_code_ranking.missing_denial_codes.by_status")


def denial_rate_by_segment(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    segments = params["segments"]
    ctx.require_columns(mc, ["claim_status"] + segments, "medical_claims")
    den_opt, min_size = params["denominator"], int(params["min_group_size"])
    denied = mc["claim_status"] == DENIED
    in_den = status_mask(mc, den_opt)
    out: dict[str, dict] = {}
    rows = []
    for seg in segments:
        s = mc[seg].map(key_str)
        out[seg] = {}
        for value in sorted(s.unique().tolist()):
            m = s == value
            num, den = int((denied & m & in_den).sum()), int((m & in_den).sum())
            out[seg][value] = {"numerator": num, "denominator": den, "rate": rate(num, den), "small_group_flag": bool(den < min_size)}
            rows.append({"segment": seg, "value": value, **out[seg][value]})
    ctx.metrics["denial_rate_by_segment"] = {"denominator_option": den_opt, "min_group_size": min_size, "segments": out}
    ctx.write_csv("denial_rates_by_segment.csv", pd.DataFrame(rows, columns=["segment", "value", "numerator", "denominator", "rate", "small_group_flag"]))
    n = len(segments)
    fig, axes = plt.subplots(n, 1, figsize=(10, 3.2 * n), squeeze=False)
    for ax, seg in zip(axes[:, 0], segments):
        items = sorted(out[seg].items(), key=lambda kv: (-kv[1]["rate"], kv[0]))
        ax.bar([k for k, _ in items], [v["rate"] for _, v in items], color=["#C44E52" if v["small_group_flag"] else "#4C72B0" for _, v in items])
        ax.set_title(f"Denial rate by {seg} (denominator: {den_opt}; red = n < {min_size})")
        ax.set_ylabel("denial rate")
        ax.tick_params(axis="x", rotation=45 if len(items) > 6 else 0)
        for lbl in ax.get_xticklabels():
            lbl.set_horizontalalignment("right" if len(items) > 6 else "center")
    ctx.save_fig(fig, "denial_rate_by_segment.png")
    for seg, values in out.items():
        for value, info in values.items():
            ctx.result("denial_rate_by_segment", f"{seg} = {value}{' (small group)' if info['small_group_flag'] else ''}: denial rate [{den_opt}]", value=info["rate"], numerator=info["numerator"], denominator=info["denominator"], source=f"metrics.json#denial_rate_by_segment.segments.{seg}")


HANDLERS = {"denial_code_ranking": denial_code_ranking, "denial_rate_by_segment": denial_rate_by_segment}
