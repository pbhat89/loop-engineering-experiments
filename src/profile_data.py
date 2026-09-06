"""Deterministic profiling of the HLT-008 sample tables (A2, data steward).

Reads the five CSV files downloaded by :mod:`src.download_data` (never the network),
profiles each table separately, checks candidate keys, date columns and cross-table
relationships, and writes:

* ``artifacts/data_profile/<table>.profile.json`` - one machine-readable profile per table
* ``artifacts/data_profile/SUMMARY.md``            - short human-readable summary
* ``data/processed/manifest.json``                 - the data contract (shape: LEAD_DESIGN_DECISIONS §13)

Everything is computed from the files; nothing is hard-coded. All JSON is written
with sorted keys; the only timestamps are ``generated_at`` (manifest, summary) and the
``retrieved_at`` copied from the download record. Sample values are truncated to 50
characters so dataset text never reaches an operator prompt except as short samples.

CLI::

    uv run python -m src.profile_data

Public helpers used by other modules::

    from src.profile_data import load_table, TABLES, STRING_COLUMNS, DATE_COLUMNS
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from src.download_data import (
    DOWNLOAD_RECORD_PATH,
    LICENSE,
    MANIFEST_PATH,
    PRETTY_NAME,
    PUBLISHER,
    RAW_DIR,
    REPO_ID,
    REVISION,
    CARD_PATH,
    TABLE_FILES,
    DATASET_URL,
    load_download_record,
    verify_local_files,
)
from src.utils import ARTIFACTS_DIR, atomic_write_text, ensure_dir, rel, sha256_file, utc_now

TABLES: tuple[str, ...] = tuple(TABLE_FILES)  # members, providers, medical_claims, pharmacy_claims, adherence
PROFILE_DIR = ARTIFACTS_DIR / "data_profile"
SAMPLE_MAX_CHARS = 50
SAMPLE_COUNT = 3
VALUE_COUNTS_MAX_UNIQUE = 12  # low-cardinality columns get full value counts (status, flags, codes)

# --------------------------------------------------------------------------- #
# Dtype policy                                                                #
# --------------------------------------------------------------------------- #
# Identifiers and codes are always read as strings: they are never summed, and
# several carry leading zeros (NDC-11, revenue codes) or are 10-digit NPIs that
# pandas would otherwise coerce to int64. Flags (0/1) stay integer; measures stay
# numeric. Columns listed here that are absent from a file are ignored, so schema
# drift surfaces in the profile rather than as a crash.
STRING_COLUMNS: dict[str, tuple[str, ...]] = {
    "members": ("member_id", "zip_code"),
    "providers": ("provider_npi", "group_id", "nucc_taxonomy"),
    "medical_claims": (
        "claim_id", "member_id", "plan_id", "rendering_npi", "billing_npi",
        "primary_icd10_cm", "dx2", "dx3", "dx4", "dx5",
        "drg_code", "drg_type", "mdc_code", "poa_flag",
        "cpt_code", "modifier1", "modifier2", "revenue_code", "place_of_service",
        "denial_code_carc", "denial_reason_desc", "auth_number",
    ),
    "pharmacy_claims": (
        "rx_claim_id", "member_id", "pharmacy_npi", "prescriber_npi", "plan_id",
        "bin_number", "pcn_code", "ndc_11", "atc_code", "dispense_as_written_code",
    ),
    "adherence": ("member_id",),
}

# Known date columns (ISO yyyy-mm-dd in this revision). Name-based detection below
# also catches any new *_date / *_start / *_end column.
DATE_COLUMNS: dict[str, tuple[str, ...]] = {
    "members": ("enrollment_start", "enrollment_end"),
    "providers": (),
    "medical_claims": ("service_date_from", "service_date_to", "adjudication_date"),
    "pharmacy_claims": ("fill_date", "paid_date", "end_date"),
    "adherence": (),
}
_DATE_NAME_RE = re.compile(r"(^|_)(date|dt)($|_)|_start$|_end$", re.IGNORECASE)

# Candidate keys to check (single and composite). The manifest lists only those
# that are verified unique and non-null.
CANDIDATE_KEYS: dict[str, tuple[tuple[str, ...], ...]] = {
    "members": (("member_id",),),
    "providers": (("provider_npi",), ("group_id",)),
    "medical_claims": (("claim_id",), ("member_id",)),
    "pharmacy_claims": (("rx_claim_id",), ("member_id",)),
    "adherence": (("member_id",), ("member_id", "therapeutic_class")),
}

# (from_table, from_column, to_table, to_column)
RELATIONSHIPS: tuple[tuple[str, str, str, str], ...] = (
    ("medical_claims", "member_id", "members", "member_id"),
    ("pharmacy_claims", "member_id", "members", "member_id"),
    ("adherence", "member_id", "members", "member_id"),
    ("medical_claims", "rendering_npi", "providers", "provider_npi"),
    ("medical_claims", "billing_npi", "providers", "provider_npi"),
    ("pharmacy_claims", "pharmacy_npi", "providers", "provider_npi"),
    ("pharmacy_claims", "prescriber_npi", "providers", "provider_npi"),
)


# --------------------------------------------------------------------------- #
# Loading                                                                     #
# --------------------------------------------------------------------------- #
def table_path(name: str, raw_dir: Path | str = RAW_DIR) -> Path:
    if name not in TABLE_FILES:
        raise KeyError(f"unknown table {name!r}; expected one of {list(TABLE_FILES)}")
    return Path(raw_dir) / TABLE_FILES[name]


def load_table(name: str, raw_dir: Path | str = RAW_DIR, parse_dates: bool = False) -> pd.DataFrame:
    """Load one table with the project's stable dtype policy.

    * identifier/code columns (``STRING_COLUMNS``) are read as strings;
    * everything else uses pandas inference with ``low_memory=False`` (whole-file
      inference, no chunk-dependent mixed types);
    * ``parse_dates=True`` converts ``DATE_COLUMNS`` with ``pd.to_datetime(errors="coerce")``;
      by default dates stay as ISO strings so callers control parsing.
    """
    path = table_path(name, raw_dir)
    if not path.is_file():
        raise FileNotFoundError(f"{rel(path)} missing - run `uv run python -m src.download_data` first")
    header = pd.read_csv(path, nrows=0).columns
    dtype = {c: str for c in STRING_COLUMNS.get(name, ()) if c in header}
    df = pd.read_csv(path, dtype=dtype, low_memory=False)
    if parse_dates:
        for col in date_columns_for(name, list(df.columns)):
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_all_tables(raw_dir: Path | str = RAW_DIR) -> dict[str, pd.DataFrame]:
    return {name: load_table(name, raw_dir) for name in TABLES}


def date_columns_for(name: str, columns: list[str]) -> list[str]:
    known = [c for c in DATE_COLUMNS.get(name, ()) if c in columns]
    detected = [c for c in columns if c not in known and _DATE_NAME_RE.search(c)]
    return known + detected


# --------------------------------------------------------------------------- #
# Small helpers                                                               #
# --------------------------------------------------------------------------- #
def _trunc(value: Any, n: int = SAMPLE_MAX_CHARS) -> str:
    s = str(value)
    return s if len(s) <= n else s[: n - 1] + "…"


def _py(v: Any) -> Any:
    """Convert numpy scalars to plain Python for JSON."""
    if hasattr(v, "item"):
        try:
            return v.item()
        except Exception:  # pragma: no cover - defensive
            return str(v)
    return v


def _sample_values(s: pd.Series, k: int = SAMPLE_COUNT) -> list[str]:
    vals = s.dropna().unique().tolist()
    if not vals:
        return []
    try:
        vals = sorted(vals)
    except TypeError:
        vals = sorted(vals, key=str)
    return [_trunc(v) for v in vals[:k]]


def _is_numeric(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s.dtype) and not pd.api.types.is_bool_dtype(s.dtype)


def _value_counts(s: pd.Series) -> dict[str, int]:
    vc = s.value_counts(dropna=False)
    out: dict[str, int] = {}
    for key, cnt in vc.items():
        label = "<null>" if pd.isna(key) else _trunc(key)
        out[label] = out.get(label, 0) + int(cnt)
    return dict(sorted(out.items()))


def _round(x: Any, nd: int = 4) -> float | None:
    if x is None or pd.isna(x):
        return None
    return round(float(x), nd)


# --------------------------------------------------------------------------- #
# Per-table profile                                                           #
# --------------------------------------------------------------------------- #
def profile_columns(df: pd.DataFrame) -> list[dict[str, Any]]:
    rows = len(df)
    out = []
    for col in df.columns:
        s = df[col]
        null_count = int(s.isna().sum())
        n_unique = int(s.nunique(dropna=True))
        entry: dict[str, Any] = {
            "name": col,
            "dtype": str(s.dtype),
            "null_count": null_count,
            "null_fraction": _round(null_count / rows if rows else 0.0, 6),
            "n_unique": n_unique,
            "sample_values": _sample_values(s),
            "all_null": null_count == rows,
            "is_constant": n_unique == 1 and null_count == 0,
        }
        if _is_numeric(s) and null_count < rows:
            entry["numeric_summary"] = {
                "min": _py(s.min()),
                "max": _py(s.max()),
                "mean": _round(s.mean(), 4),
                "sum": _round(s.sum(), 2),
            }
        if 0 < n_unique <= VALUE_COUNTS_MAX_UNIQUE:
            entry["value_counts"] = _value_counts(s)
        out.append(entry)
    return out


def check_keys(df: pd.DataFrame, name: str) -> list[dict[str, Any]]:
    checks = []
    for cols in CANDIDATE_KEYS.get(name, ()):
        present = [c for c in cols if c in df.columns]
        if len(present) != len(cols):
            checks.append({"columns": list(cols), "present": False})
            continue
        sub = df[list(cols)]
        n_null = int(sub.isna().any(axis=1).sum())
        nn = sub.dropna()
        n_dup_rows = int(nn.duplicated(keep=False).sum())
        n_distinct = int(len(nn.drop_duplicates()))
        checks.append({
            "columns": list(cols),
            "present": True,
            "rows": int(len(df)),
            "null_key_rows": n_null,
            "distinct_keys": n_distinct,
            "duplicate_key_rows": n_dup_rows,
            "extra_rows_beyond_distinct": int(len(nn) - n_distinct),
            "is_unique": n_dup_rows == 0 and n_null == 0,
        })
    return checks


def profile_dates(df: pd.DataFrame, name: str) -> tuple[list[str], dict[str, list[str]], dict[str, int]]:
    cols = date_columns_for(name, list(df.columns))
    ranges: dict[str, list[str]] = {}
    unparseable: dict[str, int] = {}
    for col in cols:
        raw = df[col]
        parsed = pd.to_datetime(raw, errors="coerce")
        unparseable[col] = int((raw.notna() & parsed.isna()).sum())
        if parsed.notna().any():
            ranges[col] = [parsed.min().strftime("%Y-%m-%d"), parsed.max().strftime("%Y-%m-%d")]
        else:
            ranges[col] = [None, None]
    return cols, ranges, unparseable


def _has(df: pd.DataFrame, *cols: str) -> bool:
    return all(c in df.columns for c in cols)


def domain_checks(df: pd.DataFrame, name: str) -> dict[str, Any]:
    """Table-specific consistency facts. Each guarded by column presence."""
    out: dict[str, Any] = {}
    if name == "medical_claims":
        if _has(df, "claim_status", "denial_code_carc"):
            grp: dict[str, Any] = {}
            for status, g in df.groupby("claim_status", sort=True):
                present = int(g["denial_code_carc"].notna().sum())
                grp[str(status)] = {"rows": int(len(g)), "with_denial_code": present, "missing_denial_code": int(len(g) - present)}
            out["denial_code_by_claim_status"] = grp
            out["denial_code_missing_total"] = int(df["denial_code_carc"].isna().sum())
            out["denial_code_counts"] = _value_counts(df["denial_code_carc"].dropna())
        if _has(df, "fraud_label", "fraud_pattern_type"):
            lbl = df["fraud_label"]
            pat = df["fraud_pattern_type"].notna()
            out["fraud_pattern_by_label"] = {
                str(int(v)): {"rows": int((lbl == v).sum()), "with_pattern": int((pat & (lbl == v)).sum()),
                              "without_pattern": int((~pat & (lbl == v)).sum())}
                for v in sorted(lbl.dropna().unique())
            }
            out["fraud_pattern_type_present_iff_fraud_label_1"] = bool((pat == (lbl == 1)).all())
            out["fraud_label_prevalence"] = _round(lbl.mean(), 6)
        if _has(df, "high_cost_flag"):
            sep: dict[str, Any] = {}
            for col in ("billed_amount", "allowed_amount", "paid_amount"):
                if col in df.columns:
                    f0 = df.loc[df["high_cost_flag"] == 0, col]
                    f1 = df.loc[df["high_cost_flag"] == 1, col]
                    sep[col] = {"flag0_max": _round(f0.max(), 2), "flag1_min": _round(f1.min(), 2),
                                "perfectly_separable": bool(len(f0) and len(f1) and f1.min() > f0.max())}
            out["high_cost_flag_separability"] = sep
            out["high_cost_flag_prevalence"] = _round(df["high_cost_flag"].mean(), 6)
        if _has(df, "claim_status", "paid_amount"):
            out["paid_amount_by_claim_status"] = {
                str(k): {"rows": int(len(g)), "paid_sum": _round(g["paid_amount"].sum(), 2),
                         "paid_max": _round(g["paid_amount"].max(), 2), "rows_paid_gt_0": int((g["paid_amount"] > 0).sum())}
                for k, g in df.groupby("claim_status", sort=True)
            }
        if _has(df, "billed_amount", "allowed_amount", "paid_amount"):
            out["amount_order_violations"] = {
                "paid_gt_allowed": int((df["paid_amount"] > df["allowed_amount"] + 1e-9).sum()),
                "allowed_gt_billed": int((df["allowed_amount"] > df["billed_amount"] + 1e-9).sum()),
                "negative_amounts": int((df[["billed_amount", "allowed_amount", "paid_amount"]] < 0).any(axis=1).sum()),
            }
        if _has(df, "service_date_from", "service_date_to", "adjudication_date"):
            sf = pd.to_datetime(df["service_date_from"], errors="coerce")
            st = pd.to_datetime(df["service_date_to"], errors="coerce")
            ad = pd.to_datetime(df["adjudication_date"], errors="coerce")
            out["date_order_violations"] = {
                "service_to_before_from": int((st < sf).sum()),
                "adjudication_before_service_from": int((ad < sf).sum()),
                "adjudication_before_service_to": int((ad < st).sum()),
            }
        if _has(df, "rendering_npi", "billing_npi"):
            out["rendering_npi_equals_billing_npi_fraction"] = _round((df["rendering_npi"] == df["billing_npi"]).mean(), 6)
        if _has(df, "claim_type", "drg_code"):
            out["drg_code_present_by_claim_type"] = {
                str(k): {"rows": int(len(g)), "with_drg": int(g["drg_code"].notna().sum())}
                for k, g in df.groupby("claim_type", sort=True)
            }
    elif name == "pharmacy_claims":
        if _has(df, "fill_date", "paid_date", "end_date", "days_supply"):
            fd = pd.to_datetime(df["fill_date"], errors="coerce")
            pdd = pd.to_datetime(df["paid_date"], errors="coerce")
            ed = pd.to_datetime(df["end_date"], errors="coerce")
            out["date_order_violations"] = {"paid_before_fill": int((pdd < fd).sum()), "end_before_fill": int((ed < fd).sum())}
            out["end_date_equals_fill_plus_days_supply_fraction"] = _round(((ed - fd).dt.days == df["days_supply"]).mean(), 6)
        for col in ("fraud_label_rx", "diversion_flag", "early_refill_flag"):
            if col in df.columns:
                out[f"{col}_prevalence"] = _round(df[col].mean(), 6)
        for col in ("pharmacy_npi", "prescriber_npi"):
            if col in df.columns:
                out[f"{col}_distinct_equals_rows"] = bool(df[col].nunique() == len(df))
    elif name == "adherence":
        if _has(df, "pdc", "mpr"):
            out["pdc_equals_mpr_all_rows"] = bool((df["pdc"] == df["mpr"]).all())
        if "pdc" in df.columns:
            out["pdc_min"] = _py(df["pdc"].min())
            out["pdc_max"] = _py(df["pdc"].max())
            out["rows_pdc_ge_0_80"] = int((df["pdc"] >= 0.8).sum())
        if "adherence_flag_pdc80" in df.columns:
            out["adherence_flag_pdc80_distinct_values"] = sorted(_py(v) for v in df["adherence_flag_pdc80"].dropna().unique())
    elif name == "members":
        if _has(df, "age_band", "age"):
            miss = df.loc[df["age_band"].isna(), ["member_id", "age"]]
            out["age_band_null_rows"] = [{"member_id": _trunc(r.member_id), "age": _py(r.age)} for r in miss.itertuples()]
        if "enrollment_end" in df.columns:
            out["enrollment_end_distinct_values"] = [_trunc(v) for v in sorted(df["enrollment_end"].dropna().unique())][:5]
    elif name == "providers":
        if "group_id" in df.columns:
            dup = df["group_id"][df["group_id"].duplicated(keep=False)]
            out["group_id_duplicate_values"] = [_trunc(v) for v in sorted(dup.dropna().unique())]
    return out


def build_profile(name: str, df: pd.DataFrame, raw_dir: Path | str = RAW_DIR) -> dict[str, Any]:
    path = table_path(name, raw_dir)
    cols = profile_columns(df)
    key_checks = check_keys(df, name)
    date_cols, date_ranges, date_unparseable = profile_dates(df, name)
    null_cells = int(df.isna().sum().sum())
    return {
        "table": name,
        "path": rel(path),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "columns": cols,
        "candidate_keys": [k["columns"][0] for k in key_checks if k.get("is_unique") and len(k["columns"]) == 1],
        "composite_keys": [k["columns"] for k in key_checks if k.get("is_unique") and len(k["columns"]) > 1],
        "key_checks": key_checks,
        "date_columns": date_cols,
        "date_ranges": date_ranges,
        "date_unparseable": date_unparseable,
        "missingness": {
            "total_cells": int(df.size),
            "null_cells": null_cells,
            "null_fraction": _round(null_cells / df.size if df.size else 0.0, 6),
            "columns_with_nulls": {c["name"]: c["null_count"] for c in cols if c["null_count"]},
            "all_null_columns": [c["name"] for c in cols if c["all_null"]],
        },
        "constant_columns": [c["name"] for c in cols if c["is_constant"]],
        "string_columns_forced": [c for c in STRING_COLUMNS.get(name, ()) if c in df.columns],
        "domain_checks": domain_checks(df, name),
    }


# --------------------------------------------------------------------------- #
# Relationships                                                               #
# --------------------------------------------------------------------------- #
def build_relationships(tables: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    out = []
    for ft, fc, tt, tc in RELATIONSHIPS:
        entry: dict[str, Any] = {"from": f"{ft}.{fc}", "to": f"{tt}.{tc}"}
        if ft not in tables or tt not in tables or fc not in tables[ft].columns or tc not in tables[tt].columns:
            entry.update({"cardinality": "unknown", "error": "column or table missing"})
            out.append(entry)
            continue
        f = tables[ft][fc]
        t = tables[tt][tc]
        f_nonnull = f.dropna()
        t_keys = set(t.dropna().unique())
        f_keys = set(f_nonnull.unique())
        matched = f_nonnull.isin(t_keys)
        unmatched_rows = int((~matched).sum())
        from_unique = f_nonnull.is_unique
        to_unique = t.dropna().is_unique
        if matched.sum() == 0:
            cardinality = "no_match"
        elif to_unique and from_unique:
            cardinality = "one_to_one"
        elif to_unique:
            cardinality = "many_to_one"
        elif from_unique:
            cardinality = "one_to_many"
        else:
            cardinality = "many_to_many"
        entry.update({
            "cardinality": cardinality,
            "unmatched_from": unmatched_rows,
            "unmatched_from_denominator": int(len(f_nonnull)),
            "from_rows": int(len(f)),
            "from_null_keys": int(f.isna().sum()),
            "from_distinct": int(len(f_keys)),
            "unmatched_from_distinct": int(len(f_keys - t_keys)),
            "to_distinct": int(len(t_keys)),
            "to_unique": bool(to_unique),
            "to_keys_unreferenced": int(len(t_keys - f_keys)),
            "match_rate": _round(matched.mean() if len(f_nonnull) else 0.0, 6),
        })
        out.append(entry)
    return out


def build_consistency_checks(tables: dict[str, pd.DataFrame]) -> list[dict[str, Any]]:
    """Cross-table attribute agreement (e.g. claim-level network_status vs provider directory)."""
    out = []
    med, prov = tables.get("medical_claims"), tables.get("providers")
    if med is not None and prov is not None and _has(med, "rendering_npi", "network_status", "provider_specialty") \
            and _has(prov, "provider_npi", "network_status", "specialty"):
        j = med[["rendering_npi", "network_status", "provider_specialty"]].merge(
            prov[["provider_npi", "network_status", "specialty"]].rename(
                columns={"network_status": "provider_network_status"}),
            left_on="rendering_npi", right_on="provider_npi", how="left", validate="many_to_one")
        joined = j["provider_npi"].notna()
        out.append({"check": "medical_claims.network_status == providers.network_status (join on rendering_npi = provider_npi)",
                    "rows": int(len(j)), "rows_joined": int(joined.sum()),
                    "rows_consistent": int((joined & (j["network_status"] == j["provider_network_status"])).sum())})
        out.append({"check": "medical_claims.provider_specialty == providers.specialty (join on rendering_npi = provider_npi)",
                    "rows": int(len(j)), "rows_joined": int(joined.sum()),
                    "rows_consistent": int((joined & (j["provider_specialty"] == j["specialty"])).sum())})
    mem = tables.get("members")
    if med is not None and mem is not None and _has(med, "member_id", "service_date_from") and _has(mem, "member_id", "enrollment_start", "enrollment_end"):
        j = med[["member_id", "service_date_from"]].merge(mem[["member_id", "enrollment_start", "enrollment_end"]], on="member_id", how="left")
        sf = pd.to_datetime(j["service_date_from"], errors="coerce")
        es = pd.to_datetime(j["enrollment_start"], errors="coerce")
        ee = pd.to_datetime(j["enrollment_end"], errors="coerce")
        out.append({"check": "medical_claims.service_date_from within members enrollment window",
                    "rows": int(len(j)), "rows_joined": int(j["enrollment_start"].notna().sum()),
                    "rows_consistent": int(((sf >= es) & (sf <= ee)).sum())})
    return out


# --------------------------------------------------------------------------- #
# Findings (plain-language, computed)                                          #
# --------------------------------------------------------------------------- #
def derive_findings(profiles: dict[str, dict[str, Any]], relationships: list[dict[str, Any]]) -> list[str]:
    f: list[str] = []
    for name, p in profiles.items():
        for k in p["key_checks"]:
            if k.get("present") and not k["is_unique"] and len(k["columns"]) == 1 and k["columns"][0] != "member_id":
                f.append(f"{name}.{k['columns'][0]} is not unique ({k['duplicate_key_rows']} rows share a value).")
        if p["missingness"]["all_null_columns"]:
            f.append(f"{name}: entirely empty columns: {', '.join(p['missingness']['all_null_columns'])}.")
        if p["constant_columns"]:
            f.append(f"{name}: constant columns (single value, no variance): {', '.join(p['constant_columns'])}.")
        for col, n in p["date_unparseable"].items():
            if n:
                f.append(f"{name}.{col}: {n} non-null values could not be parsed as dates.")
        d = p["domain_checks"]
        if name == "medical_claims":
            if d.get("fraud_pattern_type_present_iff_fraud_label_1"):
                f.append("medical_claims.fraud_pattern_type is populated exactly when fraud_label == 1: it is label-derived and must be excluded from any fraud model.")
            sep = d.get("high_cost_flag_separability", {})
            for col, s in sep.items():
                if s.get("perfectly_separable"):
                    f.append(f"medical_claims.high_cost_flag is perfectly separable on {col} (flag 0 max {s['flag0_max']}, flag 1 min {s['flag1_min']}): treat it as derived from the claim amount, not as an independent target.")
            byst = d.get("denial_code_by_claim_status", {})
            denied = byst.get("Denied")
            if denied is not None:
                f.append(f"medical_claims.denial_code_carc: {denied['missing_denial_code']} of {denied['rows']} Denied claims lack a code; {d.get('denial_code_missing_total')} nulls overall, all on non-denied statuses.")
            dov = d.get("date_order_violations", {})
            if dov.get("adjudication_before_service_to"):
                f.append(f"medical_claims: {dov['adjudication_before_service_to']} claims have adjudication_date earlier than service_date_to (none earlier than service_date_from).")
            if d.get("rendering_npi_equals_billing_npi_fraction") == 1.0:
                f.append("medical_claims.rendering_npi == billing_npi on every row; the two provider joins are redundant.")
            pend = d.get("paid_amount_by_claim_status", {}).get("Pended")
            if pend and pend["rows_paid_gt_0"]:
                f.append(f"medical_claims: {pend['rows_paid_gt_0']} of {pend['rows']} Pended claims carry paid_amount > 0.")
        if name == "adherence":
            if d.get("pdc_equals_mpr_all_rows"):
                f.append("adherence.pdc == adherence.mpr on every row (no independent information).")
            if d.get("rows_pdc_ge_0_80") == 0:
                f.append(f"adherence: no row reaches PDC 0.80 (max {d.get('pdc_max')}); adherence_flag_pdc80 has no positive class.")
        if name == "members" and d.get("age_band_null_rows"):
            f.append(f"members: {len(d['age_band_null_rows'])} rows have null age_band (age {sorted({r['age'] for r in d['age_band_null_rows']})}).")
    for r in relationships:
        if r.get("cardinality") == "no_match":
            f.append(f"{r['from']} never matches {r['to']} ({r['unmatched_from']} of {r['unmatched_from_denominator']} rows unmatched, {r['from_distinct']} distinct values): pharmacy claims cannot be joined to the provider directory.")
        elif r.get("unmatched_from"):
            f.append(f"{r['from']} -> {r['to']}: {r['unmatched_from']} of {r['unmatched_from_denominator']} rows unmatched.")
    return f


# --------------------------------------------------------------------------- #
# Manifest + summary                                                          #
# --------------------------------------------------------------------------- #
def build_manifest(profiles: dict[str, dict[str, Any]], relationships: list[dict[str, Any]],
                   consistency: list[dict[str, Any]], record: dict[str, Any], generated_at: str) -> dict[str, Any]:
    tables: dict[str, Any] = {}
    for name, p in profiles.items():
        tables[name] = {
            "path": p["path"],
            "sha256": p["sha256"],
            "bytes": p["bytes"],
            "rows": p["rows"],
            "n_columns": p["n_columns"],
            "columns": [{"name": c["name"], "dtype": c["dtype"], "null_count": c["null_count"],
                         "n_unique": c["n_unique"], "sample_values": c["sample_values"]} for c in p["columns"]],
            "candidate_keys": p["candidate_keys"],
            "composite_keys": p["composite_keys"],
            "date_columns": p["date_columns"],
            "date_ranges": p["date_ranges"],
            "date_unparseable": p["date_unparseable"],
            "all_null_columns": p["missingness"]["all_null_columns"],
            "constant_columns": p["constant_columns"],
            "string_columns_forced": p["string_columns_forced"],
            "profile_path": rel(PROFILE_DIR / f"{name}.profile.json"),
        }
    src = record.get("source", {})
    return {
        "manifest_version": "1",
        "generated_at": generated_at,
        "generator": "src/profile_data.py",
        "pandas_version": pd.__version__,
        "source": {
            "repo": REPO_ID,
            "repo_type": "dataset",
            "revision": REVISION,
            "url": DATASET_URL,
            "license": LICENSE,
            "pretty_name": PRETTY_NAME,
            "publisher": PUBLISHER,
            "retrieved_at": src.get("retrieved_at"),
            "dataset_card_path": rel(CARD_PATH),
            "dataset_card_sha256": (record.get("dataset_card") or {}).get("sha256"),
            "attribution": f"{PRETTY_NAME} by {PUBLISHER}, {DATASET_URL}, licence CC BY-NC 4.0. 100% synthetic; no PHI.",
            "synthetic": True,
        },
        "conventions": {
            "dtype_policy": "identifier/code columns are read as str (see tables.*.string_columns_forced); flags stay int64; measures numeric; dates are ISO yyyy-mm-dd strings unless load_table(parse_dates=True)",
            "sample_values": f"first {SAMPLE_COUNT} distinct non-null values in sorted order, truncated to {SAMPLE_MAX_CHARS} characters",
            "relationships.unmatched_from_denominator": "rows of the from-table with a non-null key",
            "candidate_keys": "single columns verified unique and non-null; composite_keys are multi-column keys verified unique",
        },
        "tables": tables,
        "relationships": relationships,
        "consistency_checks": consistency,
        "findings": derive_findings(profiles, relationships),
    }


def render_summary(manifest: dict[str, Any], profiles: dict[str, dict[str, Any]]) -> str:
    L: list[str] = []
    src = manifest["source"]
    L.append("# Data profile summary — HLT-008 sample (synthetic)\n")
    L.append(f"Generated {manifest['generated_at']} by `{manifest['generator']}` (pandas {manifest['pandas_version']}).  ")
    L.append(f"Source `{src['repo']}` @ `{src['revision']}`, licence `{src['license']}`, retrieved {src['retrieved_at']}.\n")
    L.append("> All records are **synthetic** (dataset card: no real claims, members, NPIs or PHI). Every count below "
             "describes the generator's output, not real-world healthcare behaviour.\n")
    L.append("## Tables\n")
    L.append("| table | rows | cols | bytes | sha256 (12) | candidate keys | date range |")
    L.append("|---|---:|---:|---:|---|---|---|")
    for name, t in manifest["tables"].items():
        keys = ", ".join(t["candidate_keys"] + ["+".join(k) for k in t["composite_keys"]]) or "—"
        dr = "; ".join(f"{c}: {r[0]}…{r[1]}" for c, r in t["date_ranges"].items()) or "—"
        L.append(f"| {name} | {t['rows']} | {t['n_columns']} | {t['bytes']} | `{t['sha256'][:12]}` | {keys} | {dr} |")
    L.append("\n## Key checks\n")
    L.append("| table | key | rows | null keys | distinct | duplicate rows | unique |")
    L.append("|---|---|---:|---:|---:|---:|---|")
    for name, p in profiles.items():
        for k in p["key_checks"]:
            if k.get("present"):
                L.append(f"| {name} | {'+'.join(k['columns'])} | {k['rows']} | {k['null_key_rows']} | {k['distinct_keys']} | {k['duplicate_key_rows']} | {'yes' if k['is_unique'] else 'no'} |")
    L.append("\n## Relationships\n")
    L.append("| from | to | cardinality | unmatched rows / denominator | unmatched distinct | to-keys unreferenced | match rate |")
    L.append("|---|---|---|---:|---:|---:|---:|")
    for r in manifest["relationships"]:
        if "error" in r:
            L.append(f"| {r['from']} | {r['to']} | unknown | — | — | — | — |")
        else:
            L.append(f"| {r['from']} | {r['to']} | {r['cardinality']} | {r['unmatched_from']} / {r['unmatched_from_denominator']} | {r['unmatched_from_distinct']} | {r['to_keys_unreferenced']} | {r['match_rate']} |")
    if manifest["consistency_checks"]:
        L.append("\n## Cross-table consistency\n")
        L.append("| check | rows | joined | consistent |")
        L.append("|---|---:|---:|---:|")
        for c in manifest["consistency_checks"]:
            L.append(f"| {c['check']} | {c['rows']} | {c['rows_joined']} | {c['rows_consistent']} |")
    L.append("\n## Missingness and degenerate columns\n")
    for name, p in profiles.items():
        m = p["missingness"]
        L.append(f"- **{name}**: {m['null_cells']} null cells of {m['total_cells']} ({m['null_fraction']:.4f}); "
                 f"columns with nulls: {', '.join(f'{c} ({n})' for c, n in m['columns_with_nulls'].items()) or 'none'}; "
                 f"all-null: {', '.join(m['all_null_columns']) or 'none'}; constant: {', '.join(p['constant_columns']) or 'none'}.")
    L.append("\n## Date columns\n")
    for name, p in profiles.items():
        if p["date_columns"]:
            parts = [f"{c} [{p['date_ranges'][c][0]} … {p['date_ranges'][c][1]}], unparseable {p['date_unparseable'][c]}" for c in p["date_columns"]]
            L.append(f"- **{name}**: " + "; ".join(parts))
    L.append("\n## Findings for downstream tasks\n")
    for fnd in manifest["findings"]:
        L.append(f"- {fnd}")
    L.append("\n## Per-table domain checks (computed)\n")
    for name, p in profiles.items():
        if p["domain_checks"]:
            L.append(f"### {name}\n")
            L.append("```json")
            L.append(json.dumps(p["domain_checks"], indent=2, sort_keys=True, ensure_ascii=False))
            L.append("```\n")
    L.append(f"Machine-readable profiles: `{rel(PROFILE_DIR)}/<table>.profile.json`; contract: `{rel(MANIFEST_PATH)}`.")
    return "\n".join(L) + "\n"


def _dump_json(path: Path, obj: Any) -> None:
    atomic_write_text(path, json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------- #
# Orchestration                                                               #
# --------------------------------------------------------------------------- #
def run_profile(raw_dir: Path | str = RAW_DIR, profile_dir: Path | str = PROFILE_DIR,
                manifest_path: Path | str = MANIFEST_PATH, quiet: bool = False) -> dict[str, Any]:
    raw_dir = Path(raw_dir)
    problems = verify_local_files(raw_dir)
    if problems:
        raise FileNotFoundError("raw data incomplete: " + "; ".join(problems) + " - run `uv run python -m src.download_data`")
    record_path = raw_dir / DOWNLOAD_RECORD_PATH.name
    record = load_download_record(record_path) if record_path.exists() else {"source": {}, "dataset_card": None}
    for fname, e in (record.get("files") or {}).items():
        actual = sha256_file(raw_dir / fname)
        if e.get("sha256") and e["sha256"] != actual:
            raise RuntimeError(f"{fname}: SHA-256 {actual} differs from download record {e['sha256']} - re-run download_data --force")

    tables = load_all_tables(raw_dir)
    profiles = {name: build_profile(name, df, raw_dir) for name, df in tables.items()}
    relationships = build_relationships(tables)
    consistency = build_consistency_checks(tables)
    generated_at = utc_now()
    manifest = build_manifest(profiles, relationships, consistency, record, generated_at)

    profile_dir = ensure_dir(profile_dir)
    for name, p in profiles.items():
        _dump_json(profile_dir / f"{name}.profile.json", p)
    atomic_write_text(profile_dir / "SUMMARY.md", render_summary(manifest, profiles))
    _dump_json(Path(manifest_path), manifest)
    if not quiet:
        for name, t in manifest["tables"].items():
            print(f"{name:<17}{t['rows']:>7} rows x {t['n_columns']:>3} cols  keys={t['candidate_keys'] or t['composite_keys']}")
        for r in relationships:
            if "error" not in r:
                print(f"  {r['from']:<32}-> {r['to']:<22}{r['cardinality']:<13}unmatched {r['unmatched_from']}/{r['unmatched_from_denominator']}")
        print(f"wrote {rel(manifest_path)}, {rel(profile_dir)}/*.profile.json, {rel(profile_dir / 'SUMMARY.md')}")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="profile_data", description="Profile the downloaded HLT-008 tables and write the data contract.")
    parser.add_argument("--raw-dir", default=str(RAW_DIR))
    parser.add_argument("--profile-dir", default=str(PROFILE_DIR))
    parser.add_argument("--manifest", default=str(MANIFEST_PATH))
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    try:
        run_profile(args.raw_dir, args.profile_dir, args.manifest, quiet=args.quiet)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
