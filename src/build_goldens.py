"""Build the frozen golden evaluation pack (Phase 1.5) from the raw data with independent reference code.

    uv run python -m src.build_goldens            # (re)build goldens/*.json|yaml + artifacts/reports/golden_review.md
    uv run python -m src.build_goldens --check    # recompute and diff against the committed files (exit 1 on drift)

Rules (LEAD §6, Addendum A): pandas/numpy + the data manifest only; deterministic; **never imports
src/task_runner.py or src/analyses/** so the goldens share no code with the executor. The only scikit-learn
call is ``train_test_split`` because the skeleton fixes the split convention in its terms. Every value carries
its definition (numerator, denominator, filters, seed, split) so the user can review it manually once.

Conventions (docs/LEAD_CATALOGUE_SKELETON.md §0): adjudicated = claim_status in {Paid, Denied, Adjusted};
month key = %Y-%m of the chosen date column; split = train_test_split(np.arange(n), test_size, random_state=seed,
shuffle=True[, stratify]) on load_table row order; threshold = numpy.percentile (linear); positive = amount > threshold.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml
from sklearn.model_selection import train_test_split

from src.profile_data import load_table
from src.utils import REPO_ROOT, atomic_write_text, read_json, utc_now

GOLDENS_DIR = REPO_ROOT / "goldens"
REVIEW_PATH = REPO_ROOT / "artifacts" / "reports" / "golden_review.md"
MANIFEST_PATH = REPO_ROOT / "data" / "processed" / "manifest.json"
GOLDEN_VERSION = "1"
BUILDER = "src/build_goldens.py"
SEED = 42
TEST_SIZE = 0.25
MIN_GROUP_SIZE = 30
RATE_TOL = 1e-6
CURRENCY_TOL = 0.01

ADJUDICATED = ("Paid", "Denied", "Adjusted")
ID_FIELDS = ["claim_id", "member_id", "rendering_npi", "billing_npi", "plan_id", "auth_number", "rx_claim_id", "provider_npi"]
PROTECTED = ["member_sex", "member_race_ethnicity", "member_age_band", "member_income_band"]

GOLDEN_FILES = {
    "T1": "T1_data_contract.json",
    "T2": "T2_portfolio_metrics.json",
    "T3": "T3_provider_network_metrics.json",
    "T4": "T4_denial_analysis_metrics.json",
    "T5": "T5_fraud_exploration_metrics.json",
    "T6": "T6_fraud_model_contract.json",
    "T7": "T7_high_cost_model_contract.json",
    "T8": "T8_executive_brief_rubric.yaml",
}

# caveat id -> keywords any of which satisfies the caveat in report text (case-insensitive substrings)
CAVEAT_KEYWORDS = {
    "synthetic_data": ["synthetic", "simulated"],
    "sample_preview": ["preview", "sample values"],
    "descriptive_only": ["descriptive"],
    "association_not_causation": ["associat", "not causal", "causation"],
    "small_groups": ["small group", "small segment", "unstable", "fewer than"],
    "class_imbalance": ["imbalanc", "rare", "minority class"],
    "model_limitations": ["baseline", "limitation"],
    "no_operational_use": ["operational", "not be used", "must not be used"],
}

JOIN_PAIRS = [
    ("medical_claims", "member_id", "members", "member_id"),
    ("medical_claims", "rendering_npi", "providers", "provider_npi"),
    ("medical_claims", "billing_npi", "providers", "provider_npi"),
    ("pharmacy_claims", "member_id", "members", "member_id"),
    ("pharmacy_claims", "pharmacy_npi", "providers", "provider_npi"),
    ("adherence", "member_id", "members", "member_id"),
]
DUP_KEYS = [
    ("medical_claims", ["claim_id"]),
    ("pharmacy_claims", ["rx_claim_id"]),
    ("members", ["member_id"]),
    ("providers", ["provider_npi"]),
    ("adherence", ["member_id"]),
    ("adherence", ["member_id", "therapeutic_class"]),
]
MEDICAL_DATE_COLUMNS = ["service_date_from", "service_date_to", "adjudication_date"]
T5_PERMITTED = ["claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status", "billed_amount",
                "allowed_amount", "paid_amount", "service_units", "length_of_stay", "er_flag", "auth_required_flag",
                "high_cost_flag", "member_payer_type"]


# --------------------------------------------------------------------------- helpers
def _py(v: Any) -> Any:
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, dict):
        return {str(k): _py(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_py(x) for x in v]
    return v


def caveats(*ids: str) -> list[dict]:
    return [{"id": i, "any_of": CAVEAT_KEYWORDS[i]} for i in ids]


def metric(value: Any, tolerance: float, **definition: Any) -> dict:
    return {"value": _py(value), "tolerance": tolerance, "definition": definition}


def rate(numerator: int, denominator: int) -> float:
    return float(numerator) / float(denominator) if denominator else float("nan")


def month_series(s: pd.Series) -> tuple[dict[str, int], int]:
    parsed = pd.to_datetime(s, errors="coerce")
    unparseable = int(parsed.isna().sum())
    counts = parsed.dropna().dt.strftime("%Y-%m").value_counts().sort_index()
    return {str(k): int(v) for k, v in counts.items()}, unparseable


def split_indices(n: int, stratify: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    return train_test_split(np.arange(n), test_size=TEST_SIZE, random_state=SEED, shuffle=True, stratify=stratify)


class Review:
    """Collects one row per golden value for artifacts/reports/golden_review.md."""

    def __init__(self) -> None:
        self.rows: list[tuple[str, str, str, str, str, str]] = []

    def add(self, task: str, metric_name: str, value: Any, definition: str, tolerance: str, sanity: str) -> None:
        self.rows.append((task, metric_name, str(value), definition, tolerance, sanity))

    def render(self, built_at: str, revision: str) -> str:
        head = [
            "# Golden pack review (Phase 1.5 user checkpoint)",
            "",
            f"Built {built_at} by `{BUILDER}` from dataset revision `{revision}` (synthetic HLT-008 sample). "
            "Every row is one frozen reference value; the definition states numerator / denominator / filters / seed / split. "
            "Review once, then the lead freezes `config/freeze_manifest.json`. Rebuild with "
            "`uv run python -m src.build_goldens`; verify with `--check`.",
            "",
            "| task | metric | value | definition | tolerance | sanity |",
            "|---|---|---|---|---|---|",
        ]
        body = [f"| {t} | `{m}` | {v} | {d} | {tol} | {s} |" for t, m, v, d, tol, s in self.rows]
        return "\n".join(head + body) + "\n"


def ok(flag: bool, text: str) -> str:
    return ("OK: " if flag else "FAIL: ") + text


# --------------------------------------------------------------------------- per-task builders
def build_t1(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc = tables["medical_claims"]
    expected_exact: dict[str, Any] = {}
    expected_exact["tables"] = {name: {"rows": int(df.shape[0]), "columns": int(df.shape[1])} for name, df in tables.items()}
    for name, df in tables.items():
        review.add("T1", f"tables.{name}.rows", df.shape[0], "len(load_table(name))", "exact", ok(True, f"{df.shape[1]} columns"))

    all_null = sorted(c for c in mc.columns if mc[c].isna().all())
    expected_exact["missingness.all_null_columns.medical_claims"] = all_null
    review.add("T1", "missingness.all_null_columns.medical_claims", ", ".join(all_null), "columns of medical_claims with null_count == rows",
               "exact (order-insensitive)", ok(len(all_null) == 7, "7 columns expected from A2 profile"))

    dups: dict[str, dict] = {}
    for table, cols in DUP_KEYS:
        df = tables[table]
        n_rows = int(len(df))
        n_unique = int(len(df.drop_duplicates(subset=cols)))
        key = f"{table}.{'+'.join(cols)}"
        dups[key] = {"n_rows": n_rows, "n_unique": n_unique, "duplicate_rows": n_rows - n_unique, "is_candidate_key": n_rows == n_unique}
        expect_key = key != "adherence.member_id"  # A2: only the composite member_id+therapeutic_class is unique in adherence
        review.add("T1", f"duplicates.{key}", f"{n_unique} unique of {n_rows}", "rows vs drop_duplicates(subset=key)", "exact",
                   ok((n_rows == n_unique) == expect_key, "candidate key" if expect_key else "not a key (composite key expected instead)"))
    expected_exact["duplicates"] = dups

    ranges: dict[str, dict] = {}
    for col in MEDICAL_DATE_COLUMNS:
        parsed = pd.to_datetime(mc[col], errors="coerce")
        ranges[f"medical_claims.{col}"] = {"min": parsed.min().strftime("%Y-%m-%d"), "max": parsed.max().strftime("%Y-%m-%d"),
                                          "unparseable": int(parsed.isna().sum())}
        review.add("T1", f"date_ranges.medical_claims.{col}", f"{ranges[f'medical_claims.{col}']['min']} .. {ranges[f'medical_claims.{col}']['max']}",
                   "pd.to_datetime(errors='coerce') min/max", "exact", ok(ranges[f"medical_claims.{col}"]["unparseable"] == 0, "0 unparseable"))
    expected_exact["date_ranges"] = ranges
    adj = pd.to_datetime(mc["adjudication_date"], errors="coerce")
    sto = pd.to_datetime(mc["service_date_to"], errors="coerce")
    sfrom = pd.to_datetime(mc["service_date_from"], errors="coerce")
    adj_before_end = int((adj < sto).sum())
    end_before_start = int((sto < sfrom).sum())
    expected_exact["date_consistency.adjudication_before_service_end"] = adj_before_end
    review.add("T1", "date_consistency.adjudication_before_service_end", adj_before_end, "count(adjudication_date < service_date_to)", "exact",
               ok(adj_before_end == 36 and end_before_start == 0, f"A2 reported 36; service_end_before_start = {end_before_start}"))

    joins: dict[str, dict] = {}
    for lt, lk, rt, rk in JOIN_PAIRS:
        left, right = tables[lt], tables[rt]
        right_keys = right[rk].dropna()
        right_unique = bool(right_keys.is_unique)
        matched_mask = left[lk].isin(set(right_keys))
        unmatched = int((~matched_mask).sum())
        rows_after = int(len(left.merge(right[[rk]].drop_duplicates(), left_on=lk, right_on=rk, how="inner")))
        if rows_after == 0:
            card = "no_match"
        elif not right_unique:
            card = "many_to_many"
        elif left[lk].is_unique:
            card = "one_to_one"
        else:
            card = "many_to_one"
        pair = f"{lt}.{lk}->{rt}.{rk}"
        joins[pair] = {"cardinality": card, "rows_left": int(len(left)), "rows_after_inner_join": rows_after, "unmatched_left": unmatched,
                       "unmatched_left_denominator": int(len(left)), "right_key_unique": right_unique}
        review.add("T1", f"join_check.{pair}", f"{card}, unmatched {unmatched}/{len(left)}", "left keys not in right key set; inner join row count", "exact",
                   ok(rows_after + unmatched == len(left), "matched + unmatched = rows_left"))
    expected_exact["join_check"] = joins

    return {
        "expected_exact": expected_exact,
        "expected_metrics": {},
        "contracts": {"missingness.scope": "all_columns"},
        "metric_ranges": {},
        "prohibited_fields": [],
        "required_caveats": caveats("synthetic_data", "sample_preview"),
    }


def build_t2(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc = tables["medical_claims"]
    n = int(len(mc))
    status = mc["claim_status"].value_counts()
    by_status = {str(k): {"n": int(v)} for k, v in status.items()}
    denied = int((mc["claim_status"] == "Denied").sum())
    adjudicated = int(mc["claim_status"].isin(ADJUDICATED).sum())
    fraud = int((mc["fraud_label"] == 1).sum())
    series, unparseable = month_series(mc["service_date_from"])
    months = sorted(series)

    expected_exact = {
        "claim_volume.total_claims": n,
        "claim_volume.by.claim_status": by_status,
        "denial_rate.numerator": denied,
        "denial_rate.denominator": adjudicated,
        "fraud_prevalence.numerator": fraud,
        "fraud_prevalence.denominator": n,
        "monthly_trend.n_months": len(months),
        "monthly_trend.first_month": months[0],
        "monthly_trend.last_month": months[-1],
        "monthly_trend.unparseable_dates": unparseable,
        "monthly_trend.series.claim_count": series,
    }
    review.add("T2", "claim_volume.total_claims", n, "all rows of medical_claims", "exact", ok(n == 12845, "A2 row count"))
    review.add("T2", "claim_volume.by.claim_status", ", ".join(f"{k} {v['n']}" for k, v in by_status.items()), "value_counts(claim_status)", "exact",
               ok(sum(v["n"] for v in by_status.values()) == n, "status counts sum to total"))
    expected_metrics = {
        "denial_rate": metric(rate(denied, adjudicated), RATE_TOL, numerator="claim_status == 'Denied'",
                              denominator="claim_status in {Paid, Denied, Adjusted} (Pended excluded)", denominator_option="adjudicated_claims",
                              numerator_value=denied, denominator_value=adjudicated),
        "fraud_prevalence": metric(rate(fraud, n), RATE_TOL, numerator="fraud_label == 1", denominator="all medical claims",
                                   denominator_option="all_claims", numerator_value=fraud, denominator_value=n),
    }
    review.add("T2", "denial_rate", f"{rate(denied, adjudicated):.6f}", f"{denied} denied / {adjudicated} adjudicated (Paid+Denied+Adjusted)", str(RATE_TOL),
               ok(adjudicated == n - int(status.get("Pended", 0)), "adjudicated = total - Pended"))
    review.add("T2", "fraud_prevalence", f"{rate(fraud, n):.6f}", f"{fraud} fraud_label==1 / {n} all claims", str(RATE_TOL), ok(fraud == 647, "A2 reported 647"))
    for col in ["billed_amount", "allowed_amount", "paid_amount"]:
        s = mc[col].astype(float)
        stats = {"sum": float(s.sum()), "mean": float(s.mean()), "median": float(s.median()),
                 "p90": float(np.percentile(s.values, 90)), "p99": float(np.percentile(s.values, 99))}
        for stat, val in stats.items():
            expected_metrics[f"financial_summary.{col}.{stat}"] = metric(val, CURRENCY_TOL, column=col, statistic=stat, rows="all medical claims",
                                                                        quantile_method="numpy.percentile linear")
        review.add("T2", f"financial_summary.{col}", f"sum {stats['sum']:.2f}; mean {stats['mean']:.2f}; median {stats['median']:.2f}; p90 {stats['p90']:.2f}; p99 {stats['p99']:.2f}",
                   "sum/mean/median/p90/p99 over all rows", str(CURRENCY_TOL), ok(stats["median"] <= stats["p90"] <= stats["p99"], "median <= p90 <= p99"))
    review.add("T2", "monthly_trend.series.claim_count", f"{len(months)} months {months[0]}..{months[-1]}; min {min(series.values())}, max {max(series.values())} per month",
               "count per %Y-%m of service_date_from", "exact per month", ok(sum(series.values()) + unparseable == n, "monthly counts + unparseable = total"))
    return {
        "expected_exact": expected_exact,
        "expected_metrics": expected_metrics,
        "contracts": {
            "denial_rate.denominator_option": "adjudicated_claims",
            "monthly_trend.date_column": "service_date_from",
            "report.show_denominators": True,
            "financial_summary": {"includes": ["billed_amount", "allowed_amount", "paid_amount"]},
        },
        "metric_ranges": {},
        "prohibited_fields": [],
        "required_caveats": caveats("synthetic_data", "descriptive_only"),
    }


def _group_stats(mc: pd.DataFrame, column: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for value, g in mc.groupby(column, sort=True):
        n = int(len(g))
        denied = int((g["claim_status"] == "Denied").sum())
        adjudicated = int(g["claim_status"].isin(ADJUDICATED).sum())
        fraud = int((g["fraud_label"] == 1).sum())
        out[str(value)] = {
            "n": n, "claim_count": n,
            "paid_amount_sum": float(g["paid_amount"].sum()), "paid_amount_mean": float(g["paid_amount"].mean()),
            "denial_rate": {"value": rate(denied, adjudicated), "numerator": denied, "denominator": adjudicated},
            "fraud_rate": {"value": rate(fraud, n), "numerator": fraud, "denominator": n},
            "small_group_flag": n < MIN_GROUP_SIZE,
        }
    return out


def build_t3(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc, pr = tables["medical_claims"], tables["providers"]
    n = int(len(mc))
    groups = {col: _group_stats(mc, col) for col in ["provider_specialty", "network_status"]}
    exact_groups = {
        col: {v: {"n": s["n"], "claim_count": s["claim_count"], "small_group_flag": s["small_group_flag"],
                  "denial_rate": {"numerator": s["denial_rate"]["numerator"], "denominator": s["denial_rate"]["denominator"]},
                  "fraud_rate": {"numerator": s["fraud_rate"]["numerator"], "denominator": s["fraud_rate"]["denominator"]}}
              for v, s in stats.items()}
        for col, stats in groups.items()
    }
    expected_metrics: dict[str, dict] = {}
    for v, s in groups["network_status"].items():
        expected_metrics[f"group_comparison.groups.network_status.{v}.denial_rate.value"] = metric(
            s["denial_rate"]["value"], RATE_TOL, numerator=f"denied claims with network_status == '{v}'",
            denominator=f"adjudicated claims with network_status == '{v}'", numerator_value=s["denial_rate"]["numerator"],
            denominator_value=s["denial_rate"]["denominator"])
        review.add("T3", f"group_comparison.groups.network_status.{v}", f"n {s['n']}; denial {s['denial_rate']['numerator']}/{s['denial_rate']['denominator']} = {s['denial_rate']['value']:.6f}; fraud {s['fraud_rate']['numerator']}/{s['n']}",
                   "per network_status: n = all claims; denial over adjudicated; fraud over n; small if n < 30", f"n exact; rate {RATE_TOL}",
                   ok(not s["small_group_flag"], "group not small"))
    spec = groups["provider_specialty"]
    review.add("T3", "group_comparison.groups.provider_specialty", f"{len(spec)} specialties; n {min(s['n'] for s in spec.values())}..{max(s['n'] for s in spec.values())}; small flags {sum(s['small_group_flag'] for s in spec.values())}",
               "per specialty: n, denial numerator/denominator (adjudicated), fraud numerator/denominator, small_group_flag (n < 30)", "exact",
               ok(sum(s["n"] for s in spec.values()) == n and sum(s["denial_rate"]["numerator"] for s in spec.values()) == 1286, "n sums to 12845, denied sums to 1286"))
    review.add("T3", "group_comparison.groups.network_status (totals)", f"n sum {sum(s['n'] for s in groups['network_status'].values())}",
               "sum over network_status groups", "exact", ok(sum(s["n"] for s in groups["network_status"].values()) == n, "sums to 12845"))

    counts = mc["rendering_npi"].value_counts()
    top = counts.sort_values(ascending=False).head(10)
    prov = pr.set_index("provider_npi")
    rows = [{"provider_npi": str(npi), "specialty": str(prov.loc[npi, "specialty"]), "network_status": str(prov.loc[npi, "network_status"]), "n": int(c)}
            for npi, c in top.items()]
    tenth, eleventh = int(counts.iloc[9]), int(counts.iloc[10])
    review.add("T3", "provider_ranking.rows", "; ".join(f"{r['provider_npi']} {r['n']}" for r in rows), "top 10 rendering_npi by claim count (ties inside the top 10 matched order-insensitively)",
               "exact (order-insensitive)", ok(tenth > eleventh, f"no tie at the boundary (10th {tenth} > 11th {eleventh})"))

    pair = "medical_claims.rendering_npi->providers.provider_npi"
    right_keys = pr["provider_npi"].dropna()
    unmatched = int((~mc["rendering_npi"].isin(set(right_keys))).sum())
    rows_after = int(len(mc.merge(pr[["provider_npi"]].drop_duplicates(), left_on="rendering_npi", right_on="provider_npi", how="inner")))
    join = {"cardinality": "many_to_one" if rows_after and right_keys.is_unique else "no_match", "rows_left": n, "rows_after_inner_join": rows_after,
            "unmatched_left": unmatched, "unmatched_left_denominator": n, "right_key_unique": bool(right_keys.is_unique)}
    review.add("T3", f"join_check.{pair}", f"{join['cardinality']}, unmatched {unmatched}/{n}, rows after inner join {rows_after}", "rendering_npi in providers.provider_npi", "exact",
               ok(unmatched == 0 and rows_after == n, "full match, no row-count change"))
    return {
        "expected_exact": {
            "group_comparison.groups.network_status": exact_groups["network_status"],
            "group_comparison.groups.provider_specialty": exact_groups["provider_specialty"],
            "provider_ranking.rows": rows,
            f"join_check.{pair}": join,
        },
        "expected_metrics": expected_metrics,
        "contracts": {
            "group_comparison.denominator_option": "adjudicated_claims",
            "group_comparison.min_group_size": MIN_GROUP_SIZE,
            "group_comparison.groups": {"includes": ["provider_specialty", "network_status"]},
            "group_comparison.metrics_each_group": {"each_has": ["claim_count", "paid_amount_sum", "denial_rate", "fraud_rate"]},
            "report.show_denominators": True,
        },
        "metric_ranges": {},
        "prohibited_fields": [],
        "required_caveats": caveats("synthetic_data", "small_groups", "association_not_causation"),
        "reference": {"paid_amount_sum_by_network_status": {v: s["paid_amount_sum"] for v, s in groups["network_status"].items()}},
    }


def build_t4(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc = tables["medical_claims"]
    n = int(len(mc))
    denied_mask = mc["claim_status"] == "Denied"
    n_denied = int(denied_mask.sum())
    code_counts = mc.loc[denied_mask, "denial_code_carc"].value_counts()
    codes = [{"code": str(c), "n": int(k), "share": rate(int(k), n_denied)} for c, k in sorted(code_counts.items(), key=lambda kv: (-kv[1], kv[0]))]
    missing_overall = int(mc["denial_code_carc"].isna().sum())
    missing_denied = int(mc.loc[denied_mask, "denial_code_carc"].isna().sum())
    by_status = {str(s): {"missing": int(g["denial_code_carc"].isna().sum()), "n": int(len(g))} for s, g in mc.groupby("claim_status", sort=True)}
    missing = {"overall": missing_overall, "overall_denominator": n, "among_denied": missing_denied, "among_denied_denominator": n_denied}
    review.add("T4", "denial_code_ranking.codes", "; ".join(f"{c['code']} {c['n']}" for c in codes), "value_counts(denial_code_carc) among denied claims; share = n / denied",
               "exact (share float)", ok(sum(c["n"] for c in codes) == n_denied and abs(sum(c["share"] for c in codes) - 1) < 1e-9, "counts sum to 1286; shares sum to 1"))
    review.add("T4", "denial_code_ranking.missing_denial_codes", f"overall {missing_overall}/{n}; among denied {missing_denied}/{n_denied}", "denial_code_carc.isna()", "exact",
               ok(missing_overall + n_denied == n and missing_denied == 0, "missing overall = total - denied; none missing among denied"))

    segments: dict[str, dict] = {}
    expected_metrics: dict[str, dict] = {}
    for seg in ["claim_type", "provider_specialty", "network_status", "place_of_service", "auth_required_flag"]:
        seg_vals: dict[str, dict] = {}
        for value, g in mc.groupby(seg, sort=True):
            denied = int((g["claim_status"] == "Denied").sum())
            adjudicated = int(g["claim_status"].isin(ADJUDICATED).sum())
            seg_vals[str(value)] = {"numerator": denied, "denominator": adjudicated, "rate": rate(denied, adjudicated),
                                    "small_group_flag": adjudicated < MIN_GROUP_SIZE}
        segments[seg] = seg_vals
        num_sum = sum(v["numerator"] for v in seg_vals.values())
        den_sum = sum(v["denominator"] for v in seg_vals.values())
        review.add("T4", f"denial_rate_by_segment.segments.{seg}", f"{len(seg_vals)} values; rates {min(v['rate'] for v in seg_vals.values()):.4f}..{max(v['rate'] for v in seg_vals.values()):.4f}; small flags {sum(v['small_group_flag'] for v in seg_vals.values())}",
                   "per value: denied / adjudicated in segment; small if denominator < 30; values keyed by str()", "exact counts",
                   ok(num_sum == 1286 and den_sum == 12339, "numerators sum to 1286, denominators to 12339"))
    prof = segments["claim_type"]["Professional"]
    expected_metrics["denial_rate_by_segment.segments.claim_type.Professional.rate"] = metric(
        prof["rate"], RATE_TOL, numerator="denied Professional claims", denominator="adjudicated Professional claims",
        numerator_value=prof["numerator"], denominator_value=prof["denominator"])
    review.add("T4", "denial_rate_by_segment.segments.claim_type.Professional.rate", f"{prof['rate']:.6f}", f"{prof['numerator']} / {prof['denominator']}", str(RATE_TOL), ok(True, "rate in (0, 1)"))
    exact_segments = {seg: {v: {"numerator": s["numerator"], "denominator": s["denominator"], "small_group_flag": s["small_group_flag"]} for v, s in vals.items()}
                      for seg, vals in segments.items()}
    return {
        "expected_exact": {
            "denial_code_ranking.codes": codes,
            "denial_code_ranking.missing_denial_codes": missing,
            "denial_code_ranking.missing_denial_codes.by_status": by_status,
            "denial_rate_by_segment.segments": exact_segments,
        },
        "expected_metrics": expected_metrics,
        "contracts": {
            "denial_code_ranking.scope": "denied_claims",
            "denial_rate_by_segment.denominator_option": "adjudicated_claims",
            "denial_rate_by_segment.min_group_size": MIN_GROUP_SIZE,
            "denial_rate_by_segment.segments": {"includes": ["claim_type", "provider_specialty", "network_status", "place_of_service", "auth_required_flag"]},
            "report.show_denominators": True,
        },
        "metric_ranges": {},
        "prohibited_fields": [],
        "required_caveats": caveats("synthetic_data", "small_groups"),
    }


def build_t5(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc = tables["medical_claims"]
    n = int(len(mc))
    flagged = mc["fraud_label"] == 1
    pos, neg = int(flagged.sum()), int((~flagged).sum())
    prevalence, imbalance = rate(pos, n), rate(neg, pos)
    review.add("T5", "class_prevalence", f"positives {pos}; negatives {neg}; prevalence {prevalence:.6f}; imbalance_ratio {imbalance:.4f}",
               "fraud_label == 1 over all claims; imbalance = negatives / positives", f"counts exact; rates {RATE_TOL}", ok(pos + neg == n, "positives + negatives = total"))
    billed_f, billed_u = float(mc.loc[flagged, "billed_amount"].mean()), float(mc.loc[~flagged, "billed_amount"].mean())
    ct_f = {str(k): float(v) for k, v in mc.loc[flagged, "claim_type"].value_counts(normalize=True).sort_index().items()}
    ct_u = {str(k): float(v) for k, v in mc.loc[~flagged, "claim_type"].value_counts(normalize=True).sort_index().items()}
    review.add("T5", "feature_comparison.billed_amount.{flagged,unflagged}.mean", f"flagged {billed_f:.4f}; unflagged {billed_u:.4f}", "mean billed_amount by fraud_label", str(RATE_TOL),
               ok(billed_f > 0 and billed_u > 0, "positive means"))
    review.add("T5", "feature_comparison.claim_type.flagged", "; ".join(f"{k} {v:.4f}" for k, v in ct_f.items()), "value_counts(normalize=True) within flagged claims", str(RATE_TOL),
               ok(abs(sum(ct_f.values()) - 1) < 1e-9, "shares sum to 1"))
    return {
        "expected_exact": {"class_prevalence": {"positives": pos, "negatives": neg, "total": n}},
        "expected_metrics": {
            "class_prevalence.prevalence": metric(prevalence, RATE_TOL, numerator="fraud_label == 1", denominator="all medical claims", numerator_value=pos, denominator_value=n),
            "class_prevalence.imbalance_ratio": metric(imbalance, RATE_TOL, numerator="fraud_label == 0", denominator="fraud_label == 1", numerator_value=neg, denominator_value=pos),
            "feature_comparison.billed_amount.flagged.mean": metric(billed_f, RATE_TOL, statistic="mean billed_amount", rows="fraud_label == 1", n=pos),
            "feature_comparison.billed_amount.unflagged.mean": metric(billed_u, RATE_TOL, statistic="mean billed_amount", rows="fraud_label == 0", n=neg),
            "feature_comparison.claim_type.flagged": {"values": ct_f, "tolerance": RATE_TOL, "definition": {"statistic": "share of claim_type within fraud_label == 1", "n": pos}},
            "feature_comparison.claim_type.unflagged": {"values": ct_u, "tolerance": RATE_TOL, "definition": {"statistic": "share of claim_type within fraud_label == 0", "n": neg}},
        },
        "contracts": {
            "feature_comparison": {"min_count": 4, "from": T5_PERMITTED},
            "leakage_risks.label_derived_fields": {"includes": ["fraud_pattern_type"]},
        },
        "metric_ranges": {},
        "prohibited_fields": ["fraud_pattern_type", "member_sex", "member_race_ethnicity", "member_age_band"],
        "required_caveats": caveats("synthetic_data", "class_imbalance", "association_not_causation", "no_operational_use"),
        "reference": {"id_fields": ID_FIELDS, "protected_attributes": PROTECTED, "label_derived_fields": ["fraud_pattern_type"]},
    }


def build_t6(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc = tables["medical_claims"]
    n = int(len(mc))
    y = mc["fraud_label"].to_numpy()
    tr, te = split_indices(n, stratify=y)
    prev_tr, prev_te = float(y[tr].mean()), float(y[te].mean())
    review.add("T6", "split", f"n_train {len(tr)}; n_test {len(te)}; prevalence_train {prev_tr:.6f}; prevalence_test {prev_te:.6f}",
               f"train_test_split(np.arange({n}), test_size={TEST_SIZE}, random_state={SEED}, shuffle=True, stratify=fraud_label)", "sizes exact",
               ok(len(tr) + len(te) == n and abs(prev_tr - prev_te) < 0.001, "sizes sum to total; stratified prevalences match"))
    return {
        "expected_exact": {"split": {"n_train": int(len(tr)), "n_test": int(len(te))}, "seed": SEED},
        "expected_metrics": {},
        "contracts": {
            "split.test_size": TEST_SIZE, "split.stratify": True, "preprocessing.fit_on": "train_only",
            "models_logistic": {"includes": ["logistic_regression"]},
            "models_tree": {"any_of": ["random_forest", "gradient_boosting"]},
            "models_metrics": {"each_has": ["precision", "recall", "f1", "pr_auc", "roc_auc", "confusion_matrix"]},
        },
        "metric_ranges": {
            # Sanity range only: on this synthetic label, leakage-free models score ROC-AUC ~= 0.50 (A6 measured
            # 0.499-0.515), so the floor sits below chance to avoid failing honest models on noise.
            "models.*.roc_auc": {"min": 0.40, "max": 1.0},
            "models.*.pr_auc": {"min": {"ref": "split.prevalence_test", "factor": 0.5}, "max": 1.0},
            "split.prevalence_test": {"min": 0.03, "max": 0.07},
        },
        "prohibited_fields": ["fraud_pattern_type", "claim_id", "member_id", "rendering_npi"],
        "required_caveats": caveats("synthetic_data", "class_imbalance", "model_limitations", "no_operational_use"),
        "reference": {"prevalence_train": prev_tr, "prevalence_test": prev_te, "n_positive_train": int(y[tr].sum()), "n_positive_test": int(y[te].sum()),
                      "split_definition": f"train_test_split(np.arange(n), test_size={TEST_SIZE}, random_state={SEED}, shuffle=True, stratify=fraud_label)"},
    }


def build_t7(tables: dict[str, pd.DataFrame], review: Review) -> dict:
    mc = tables["medical_claims"]
    n = int(len(mc))
    paid = mc["paid_amount"].to_numpy(dtype=float)
    tr, te = split_indices(n)
    threshold = float(np.percentile(paid[tr], 95))
    threshold_all = float(np.percentile(paid, 95))
    pos_tr, pos_te = int((paid[tr] > threshold).sum()), int((paid[te] > threshold).sum())
    review.add("T7", "target_definition.threshold_value", f"{threshold:.4f}", f"numpy.percentile(paid_amount[train], 95) with train from train_test_split(np.arange({n}), test_size={TEST_SIZE}, random_state={SEED}, shuffle=True)",
               str(CURRENCY_TOL), ok(abs(threshold - threshold_all) > CURRENCY_TOL, f"differs from the all-data percentile {threshold_all:.4f}, so the check discriminates"))
    review.add("T7", "target_definition.positive_rate_{train,test}", f"train {pos_tr}/{len(tr)} = {rate(pos_tr, len(tr)):.6f}; test {pos_te}/{len(te)} = {rate(pos_te, len(te)):.6f}",
               "paid_amount > threshold_value in each partition", str(RATE_TOL), ok(abs(rate(pos_tr, len(tr)) - 0.05) < 0.002, "train positive rate about 5 percent"))
    review.add("T7", "split", f"n_train {len(tr)}; n_test {len(te)}", "plain split, no stratification", "exact", ok(len(tr) + len(te) == n, "sizes sum to total"))
    return {
        "expected_exact": {"split": {"n_train": int(len(tr)), "n_test": int(len(te))}, "seed": SEED},
        "expected_metrics": {
            "target_definition.threshold_value": metric(threshold, CURRENCY_TOL, amount_column="paid_amount", percentile=95, threshold_source="train_only",
                                                        split=f"train_test_split(np.arange(n), test_size={TEST_SIZE}, random_state={SEED}, shuffle=True)",
                                                        method="numpy.percentile linear interpolation", all_data_threshold_for_reference=threshold_all),
            "target_definition.positive_rate_train": metric(rate(pos_tr, len(tr)), RATE_TOL, numerator="train rows with paid_amount > threshold_value", denominator="n_train",
                                                            numerator_value=pos_tr, denominator_value=int(len(tr))),
            "target_definition.positive_rate_test": metric(rate(pos_te, len(te)), RATE_TOL, numerator="test rows with paid_amount > threshold_value", denominator="n_test",
                                                           numerator_value=pos_te, denominator_value=int(len(te))),
        },
        "contracts": {
            "target_definition.threshold_source": "train_only", "target_definition.amount_column": "paid_amount", "target_definition.percentile": 95,
            "preprocessing.fit_on": "train_only", "split.test_size": TEST_SIZE,
            "models_logistic": {"includes": ["logistic_regression"]},
            "models_tree": {"any_of": ["random_forest", "gradient_boosting"]},
            "models_metrics": {"each_has": ["pr_auc", "roc_auc", "precision_at_top_5pct", "recall_at_top_5pct"]},
        },
        "metric_ranges": {
            # Sanity range only: on this synthetic label, leakage-free models score ROC-AUC ~= 0.50 (A6 measured
            # 0.499-0.515), so the floor sits below chance to avoid failing honest models on noise.
            # D-21: a target band rather than a floor. Leakage-free models reach 0.89-0.91 on this data; amount features
            # (the target is derived from them) push ROC-AUC to 0.997-1.0, so anything above 0.95 is treated as suspicious.
            "models.*.roc_auc": {"min": 0.60, "max": 0.95},
            "models.*.pr_auc": {"min": {"ref": "target_definition.positive_rate_test", "factor": 0.5}, "max": 1.0},
            "models.*.precision_at_top_5pct": {"min": 0.0, "max": 1.0},
        },
        "prohibited_fields": ["billed_amount", "allowed_amount", "paid_amount", "member_oop", "cob_amount", "high_cost_flag", "claim_id", "member_id"],
        "required_caveats": caveats("synthetic_data", "model_limitations", "no_operational_use"),
        "reference": {"n_positive_train": pos_tr, "n_positive_test": pos_te, "all_data_threshold": threshold_all},
    }


def build_t8(review: Review) -> dict:
    review.add("T8", "brief contracts", "sources >= {T2,T5,T6,T7} + one of {T3,T4}; 5 sections; cite_artifacts; causal_language avoid; <= 600 words",
               "structural golden (no data values)", "n/a", ok(True, "forbidden phrases: causes, drives, leads to, because of"))
    return {
        "expected_exact": {},
        "expected_metrics": {},
        "contracts": {
            "findings_core_sources": {"includes": ["T2", "T5", "T6", "T7"], "field": "task_id"},
            "findings_segment_source": {"any_of": ["T3", "T4"], "field": "task_id"},
            "brief.sections": {"includes": ["key_findings", "model_results", "limitations", "synthetic_caveats", "next_steps"]},
            "brief.cite_artifacts": True,
            "brief.n_cited_statements": {"equals_metric": "brief.n_numeric_statements"},
            "brief.causal_language": "avoid",
        },
        "metric_ranges": {},
        "prohibited_fields": [],
        "required_caveats": caveats("synthetic_data", "no_operational_use"),
        "forbidden_phrases": ["causes", "drives", "leads to", "because of"],
        "max_words": 600,
        "required_findings": [
            {"task_id": "T2", "metric_key": "denial_rate", "why": "headline denial rate with numerator and denominator"},
            {"task_id": "T2", "metric_key": "claim_volume.total_claims", "why": "portfolio size"},
            {"task_id": "T5", "metric_key": "class_prevalence", "why": "fraud-label prevalence and imbalance"},
            {"task_id": "T6", "metric_key": "models.*.roc_auc", "why": "fraud model discrimination"},
            {"task_id": "T7", "metric_key": "target_definition.threshold_value", "why": "high-cost threshold from the training split"},
        ],
        "artifact_reference_requirement": "every numeric statement ends with [source: <artifact path or metrics.json#key>]",
    }


# --------------------------------------------------------------------------- assembly
def build_all() -> tuple[dict[str, dict], str]:
    manifest = read_json(MANIFEST_PATH, default=None)
    if not manifest:
        raise SystemExit(f"{MANIFEST_PATH} missing - run `uv run python -m src.profile_data` first")
    revision = (manifest.get("source") or {}).get("revision", "unknown")
    sha = {f"{name}.csv": t.get("sha256") for name, t in (manifest.get("tables") or {}).items()}
    tables = {name: load_table(name) for name in ["members", "providers", "medical_claims", "pharmacy_claims", "adherence"]}
    suite = yaml.safe_load((REPO_ROOT / "config" / "tasks.yaml").read_text(encoding="utf-8"))
    spec = {t["task_id"]: t for t in suite["tasks"]}
    review = Review()
    built_at = utc_now()
    bodies = {"T1": build_t1(tables, review), "T2": build_t2(tables, review), "T3": build_t3(tables, review), "T4": build_t4(tables, review),
              "T5": build_t5(tables, review), "T6": build_t6(tables, review), "T7": build_t7(tables, review), "T8": build_t8(review)}
    goldens: dict[str, dict] = {}
    for tid, body in bodies.items():
        inputs = spec[tid]["input_tables"] or list(tables)
        goldens[tid] = _py({
            "task_id": tid, "golden_version": GOLDEN_VERSION, "built_at": built_at, "builder": BUILDER,
            "dataset_revision": revision, "data_sha256": {f"{n}.csv": sha.get(f"{n}.csv") for n in inputs},
            "required_artifacts": list(spec[tid]["required_artifacts"]),
            **body,
        })
    return goldens, review.render(built_at, revision)


def dump(tid: str, golden: dict) -> str:
    if GOLDEN_FILES[tid].endswith(".yaml"):
        return yaml.safe_dump(golden, sort_keys=False, allow_unicode=True, width=120)
    return json.dumps(golden, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def load_committed(tid: str) -> dict | None:
    path = GOLDENS_DIR / GOLDEN_FILES[tid]
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    return yaml.safe_load(text) if path.suffix == ".yaml" else json.loads(text)


def _strip(g: dict) -> dict:
    return {k: v for k, v in g.items() if k != "built_at"}


def _diff(a: Any, b: Any, path: str = "") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append(f"{path}.{k}: added in recomputation")
            elif k not in b:
                out.append(f"{path}.{k}: missing in recomputation")
            else:
                out += _diff(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: list length {len(a)} != {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _diff(x, y, f"{path}[{i}]")]
    if isinstance(a, float) or isinstance(b, float):
        try:
            if abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(a))):
                return []
        except (TypeError, ValueError):
            pass
        return [f"{path}: {a!r} != {b!r}"]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="recompute and diff against committed goldens (exit 1 on drift); writes nothing")
    args = ap.parse_args(argv)
    goldens, review_md = build_all()
    if args.check:
        drift: list[str] = []
        for tid, g in goldens.items():
            committed = load_committed(tid)
            if committed is None:
                drift.append(f"{GOLDEN_FILES[tid]}: not committed")
                continue
            drift += [f"{GOLDEN_FILES[tid]}{d}" for d in _diff(_strip(committed), _strip(g))]
        if drift:
            print("golden drift detected:")
            for d in drift:
                print("  " + d)
            return 1
        print(f"golden pack check clean: {len(goldens)} files match the recomputation (built_at ignored)")
        return 0
    GOLDENS_DIR.mkdir(parents=True, exist_ok=True)
    for tid, g in goldens.items():
        atomic_write_text(GOLDENS_DIR / GOLDEN_FILES[tid], dump(tid, g))
        print(f"wrote goldens/{GOLDEN_FILES[tid]}")
    atomic_write_text(REVIEW_PATH, review_md)
    print(f"wrote {REVIEW_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"denial_rate {goldens['T2']['expected_metrics']['denial_rate']['value']:.6f} | fraud_prevalence {goldens['T2']['expected_metrics']['fraud_prevalence']['value']:.6f} | "
          f"T7 threshold {goldens['T7']['expected_metrics']['target_definition.threshold_value']['value']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
