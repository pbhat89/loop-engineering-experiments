"""T5 — Fraud-pattern exploration: class prevalence, flagged-vs-unflagged feature comparison, leakage assessment."""
from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd

from src.analyses.common import ID_FIELDS, LABEL_DERIVED_FIELDS, PROTECTED_ATTRIBUTES, Ctx, key_str, rate, sorted_counts

NUMERIC_FEATURES = {"billed_amount", "allowed_amount", "paid_amount", "service_units", "length_of_stay"}
MEMBER_FEATURES = {"member_sex": "sex", "member_race_ethnicity": "race_ethnicity", "member_age_band": "age_band", "member_payer_type": "payer_type"}


def class_prevalence(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, ["fraud_label"], "medical_claims")
    pos = int((mc["fraud_label"] == 1).sum())
    total = int(len(mc))
    neg = total - pos
    out = {"positives": pos, "negatives": neg, "total": total, "prevalence": rate(pos, total), "imbalance_ratio": (neg / pos) if pos else None}
    ctx.metrics["class_prevalence"] = out
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["fraud_label = 0", "fraud_label = 1"], [neg, pos], color=["#4C72B0", "#C44E52"])
    ax.set_title(f"Fraud label prevalence: {pos} / {total} = {out['prevalence']:.4f}")
    ax.set_ylabel("claims")
    ctx.save_fig(fig, "fraud_prevalence.png")
    ctx.result("class_prevalence", "Fraud prevalence", value=out["prevalence"], numerator=pos, denominator=total, source="metrics.json#class_prevalence")
    ctx.result("class_prevalence", "Imbalance ratio (negatives per positive)", value=out["imbalance_ratio"], source="metrics.json#class_prevalence.imbalance_ratio")


def _with_member_features(ctx: Ctx, mc: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    wanted = [f for f in features if f in MEMBER_FEATURES]
    if not wanted:
        return mc
    members = ctx.table("members")
    ctx.require_columns(members, ["member_id"] + [MEMBER_FEATURES[f] for f in wanted], "members")
    ctx.require_columns(mc, ["member_id"], "medical_claims")
    right = members[["member_id"] + [MEMBER_FEATURES[f] for f in wanted]].rename(columns={MEMBER_FEATURES[f]: f for f in wanted})
    return mc.merge(right, on="member_id", how="left", validate="many_to_one")


def feature_comparison(ctx: Ctx, params: dict) -> None:
    features = list(params["features"])
    ctx.state["t5_features"] = features
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, ["fraud_label"], "medical_claims")
    df = _with_member_features(ctx, mc, features)
    ctx.require_columns(df, features, "medical_claims(+members)")
    flagged, unflagged = df[df["fraud_label"] == 1], df[df["fraud_label"] != 1]
    out: dict[str, dict] = {}
    rows = []
    for f in features:
        kind = "numeric" if f in NUMERIC_FEATURES else "categorical"
        info: dict = {"kind": kind, "n_flagged": int(len(flagged)), "n_unflagged": int(len(unflagged))}
        for grp_name, grp in (("flagged", flagged), ("unflagged", unflagged)):
            if kind == "numeric":
                s = pd.to_numeric(grp[f], errors="coerce").dropna()
                stats = {"mean": float(s.mean()) if len(s) else None, "median": float(s.median()) if len(s) else None}
                info[grp_name] = stats
                rows += [{"feature": f, "kind": kind, "group": grp_name, "key": k, "value": v} for k, v in stats.items()]
            else:
                n = int(len(grp))
                shares = {v: rate(c, n) for v, c in sorted_counts(grp[f])}
                info[grp_name] = shares
                rows += [{"feature": f, "kind": kind, "group": grp_name, "key": k, "value": v} for k, v in shares.items()]
        out[f] = info
        if kind == "numeric":
            ctx.result("feature_comparison", f"{f} mean (flagged / unflagged) = {info['flagged']['mean']:.6f} / {info['unflagged']['mean']:.6f}", source="metrics.json#feature_comparison")
        else:
            top_f = max(info["flagged"].items(), key=lambda kv: (kv[1], kv[0]))[0] if info["flagged"] else None
            ctx.result("feature_comparison", f"{f}: most common value among flagged = {key_str(top_f)}; share", value=info["flagged"].get(top_f), source="metrics.json#feature_comparison")
    ctx.metrics["feature_comparison"] = out
    ctx.write_csv("fraud_comparison.csv", pd.DataFrame(rows, columns=["feature", "kind", "group", "key", "value"]))


def leakage_assessment(ctx: Ctx, params: dict) -> None:
    planned = ctx.state.get("t5_features")
    if planned is None:
        planned = []
        for step in ctx.plan.get("steps", []):
            if step.get("component") == "feature_comparison":
                planned = list((step.get("params") or {}).get("features") or [])
    risky = set(LABEL_DERIVED_FIELDS) | set(PROTECTED_ATTRIBUTES) | set(ID_FIELDS)
    out = {
        "label_derived_fields": list(LABEL_DERIVED_FIELDS),
        "id_fields": list(ID_FIELDS),
        "protected_attributes": list(PROTECTED_ATTRIBUTES),
        "flagged_in_plan": [f for f in planned if f in risky],
    }
    ctx.metrics["leakage_risks"] = out
    ctx.result("leakage_assessment", f"Label-derived: {out['label_derived_fields']}; protected: {out['protected_attributes']}; flagged features in this plan: {out['flagged_in_plan'] or 'none'}", source="metrics.json#leakage_risks")
    ctx.result("leakage_assessment", "Plan features that are label-derived, protected or identifiers", value=len(out["flagged_in_plan"]), source="metrics.json#leakage_risks.flagged_in_plan")


HANDLERS = {"class_prevalence": class_prevalence, "feature_comparison": feature_comparison, "leakage_assessment": leakage_assessment}
