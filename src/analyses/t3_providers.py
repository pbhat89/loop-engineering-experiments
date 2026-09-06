"""T3 — Provider and network patterns: provider join, group comparison, provider ranking (join_check shared).

Groups use the claim-level columns ``provider_specialty`` / ``network_status`` of medical_claims;
the providers table is used by the join check, the provider join and the ranking.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.analyses.common import ADJUDICATED_STATUSES, DENIED, Ctx, key_str, rate, rate_dict


def provider_join(ctx: Ctx, params: dict) -> None:
    mc, prov = ctx.table("medical_claims"), ctx.table("providers")
    key = params["provider_key"]
    ctx.require_columns(mc, [key], "medical_claims")
    ctx.require_columns(prov, ["provider_npi"], "providers")
    validate = None if params["validate"] == "none" else params["validate"]
    merged = mc[[key]].merge(prov[["provider_npi"]], left_on=key, right_on="provider_npi", how=params["how"], validate=validate)
    matched_mask = mc[key].isin(prov["provider_npi"].dropna().unique()) & mc[key].notna()
    out = {
        "provider_key": key,
        "how": params["how"],
        "validate": params["validate"],
        "rows_before": int(len(mc)),
        "rows_after": int(len(merged)),
        "unmatched": int((~matched_mask).sum()),
        "providers_matched": int(mc.loc[matched_mask, key].nunique()),
    }
    ctx.metrics["provider_join"] = out
    ctx.result("provider_join", f"{key} -> providers.provider_npi ({params['how']}, validate={params['validate']}): rows before -> after {out['rows_before']} -> {out['rows_after']}; unmatched claims", value=rate(out["unmatched"], out["rows_before"]), numerator=out["unmatched"], denominator=out["rows_before"], source="metrics.json#provider_join")
    ctx.result("provider_join", "Distinct providers matched", value=out["providers_matched"], source="metrics.json#provider_join.providers_matched")


def _group_series(mc: pd.DataFrame, key: str) -> pd.Series:
    cols = key.split("+")
    if len(cols) == 1:
        return mc[cols[0]].map(key_str)
    return mc[cols[0]].map(key_str) + "|" + mc[cols[1]].map(key_str)


def group_comparison(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    needed = {"claim_status", "fraud_label", "paid_amount"}
    for k in params["group_by"]:
        needed.update(k.split("+"))
    ctx.require_columns(mc, sorted(needed), "medical_claims")
    metrics = params["metrics"]
    min_size = int(params["min_group_size"])
    den_opt = params["denominator"]
    denied = mc["claim_status"] == DENIED
    fraud = mc["fraud_label"] == 1
    adjudicated = mc["claim_status"].isin(ADJUDICATED_STATUSES) if den_opt == "adjudicated_claims" else pd.Series(True, index=mc.index)
    paid = pd.to_numeric(mc["paid_amount"], errors="coerce")
    groups: dict[str, dict] = {}
    rows = []
    for key in params["group_by"]:
        g = _group_series(mc, key)
        groups[key] = {}
        for value in sorted(g.unique().tolist()):
            m = g == value
            n = int(m.sum())
            info: dict = {"n": n}
            if "claim_count" in metrics:
                info["claim_count"] = n
            if "paid_amount_sum" in metrics:
                info["paid_amount_sum"] = float(paid[m].sum())
            if "paid_amount_mean" in metrics:
                info["paid_amount_mean"] = float(paid[m].mean()) if n else 0.0
            if "denial_rate" in metrics:
                info["denial_rate"] = rate_dict(int((denied & m & adjudicated).sum()), int((m & adjudicated).sum()))
            if "fraud_rate" in metrics:
                info["fraud_rate"] = rate_dict(int((fraud & m).sum()), n)
            info["small_group_flag"] = bool(n < min_size)
            groups[key][value] = info
            row = {"group_by": key, "group_value": value, "n": n}
            for mname in ("claim_count", "paid_amount_sum", "paid_amount_mean"):
                if mname in info:
                    row[mname] = info[mname]
            for mname in ("denial_rate", "fraud_rate"):
                if mname in info:
                    row[f"{mname}_numerator"] = info[mname]["numerator"]
                    row[f"{mname}_denominator"] = info[mname]["denominator"]
                    row[mname] = info[mname]["value"]
            row["small_group_flag"] = info["small_group_flag"]
            rows.append(row)
    ctx.metrics["group_comparison"] = {"min_group_size": min_size, "denominator_option": den_opt, "groups": groups}
    ctx.write_csv("group_comparison.csv", pd.DataFrame(rows))
    first = params["group_by"][0]
    items = sorted(groups[first].items(), key=lambda kv: (-kv[1]["n"], kv[0]))
    fig, ax = plt.subplots(figsize=(max(8, min(16, 0.5 * len(items) + 4)), 5))
    ax.bar([k for k, _ in items], [v["n"] for _, v in items], color=["#C44E52" if v["small_group_flag"] else "#4C72B0" for _, v in items])
    ax.set_title(f"Claim count by {first} (red = below min_group_size {min_size})")
    ax.set_ylabel("claims")
    ax.tick_params(axis="x", rotation=60)
    for lbl in ax.get_xticklabels():
        lbl.set_horizontalalignment("right")
    ctx.save_fig(fig, "group_comparison.png")
    for key, values in groups.items():
        flagged = sum(1 for v in values.values() if v["small_group_flag"])
        ctx.result("group_comparison", f"{key}: groups {len(values)}, flagged small (n < {min_size})", value=flagged, source="metrics.json#group_comparison.groups")
        for value, info in values.items():
            if "denial_rate" in info:
                dr = info["denial_rate"]
                ctx.result("group_comparison", f"{key} = {value} (n={info['n']}{', small group' if info['small_group_flag'] else ''}): denial rate [{den_opt}]", value=dr["value"], numerator=dr["numerator"], denominator=dr["denominator"], source=f"metrics.json#group_comparison.groups.{key}")
            if "fraud_rate" in info:
                fr = info["fraud_rate"]
                ctx.result("group_comparison", f"{key} = {value}: fraud rate", value=fr["value"], numerator=fr["numerator"], denominator=fr["denominator"], source=f"metrics.json#group_comparison.groups.{key}")
            if "paid_amount_sum" in info:
                ctx.result("group_comparison", f"{key} = {value}: paid_amount sum", value=info["paid_amount_sum"], source=ctx.artifact_rel("group_comparison.csv"))


def provider_ranking(ctx: Ctx, params: dict) -> None:
    mc, prov = ctx.table("medical_claims"), ctx.table("providers")
    ctx.require_columns(mc, ["rendering_npi", "claim_status", "paid_amount"], "medical_claims")
    ctx.require_columns(prov, ["provider_npi", "specialty", "network_status"], "providers")
    metric, top_n, min_claims = params["metric"], int(params["top_n"]), int(params["min_claims"])
    grp = mc.groupby("rendering_npi", sort=True)
    stats = pd.DataFrame(
        {
            "n": grp.size(),
            "paid_amount_sum": grp["paid_amount"].sum(),
            "denied": grp["claim_status"].apply(lambda s: int((s == DENIED).sum())),
        }
    )
    stats["claim_count"] = stats["n"]
    stats["denial_rate"] = stats.apply(lambda r: rate(int(r["denied"]), int(r["n"])), axis=1)
    stats = stats[stats["n"] >= min_claims].reset_index().rename(columns={"rendering_npi": "provider_npi"})
    stats = stats.merge(prov[["provider_npi", "specialty", "network_status"]], on="provider_npi", how="left")
    stats["value"] = stats[metric].astype(float)
    stats = stats.sort_values(["value", "provider_npi"], ascending=[False, True], kind="stable").head(top_n)
    rows = [
        {"provider_npi": str(r.provider_npi), "specialty": key_str(r.specialty), "network_status": key_str(r.network_status), "n": int(r.n), "value": float(r.value)}
        for r in stats.itertuples(index=False)
    ]
    ctx.metrics["provider_ranking"] = {"metric": metric, "top_n": top_n, "min_claims": min_claims, "rows": rows}
    ctx.write_csv("provider_ranking.csv", pd.DataFrame(rows, columns=["provider_npi", "specialty", "network_status", "n", "value"]))
    ctx.result("provider_ranking", f"Top {top_n} providers by {metric} (min_claims={min_claims}); providers ranked", value=len(rows), source=ctx.artifact_rel("provider_ranking.csv"))
    for i, r in enumerate(rows, 1):
        ctx.result("provider_ranking", f"#{i} {r['provider_npi']} ({r['specialty']}, {r['network_status']}, n={r['n']}): {metric}", value=r["value"], source="metrics.json#provider_ranking.rows")


HANDLERS = {"provider_join": provider_join, "group_comparison": group_comparison, "provider_ranking": provider_ranking}
