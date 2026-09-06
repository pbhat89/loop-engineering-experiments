"""Data-contract tests (A2).

Skip cleanly when ``data/raw`` has no CSV files; otherwise assert that the
manifest, the files on disk and ``load_table`` agree, that the columns the task
suite relies on exist, and that the key/relationship facts recorded in the
manifest still hold. No network access.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.download_data import (
    CARD_PATH,
    EXPECTED_BYTES,
    LICENSE,
    MANIFEST_PATH,
    REPO_ID,
    REVISION,
    TABLE_FILES,
    load_manifest,
    raw_files_present,
)
from src.profile_data import STRING_COLUMNS, TABLES, load_table
from src.utils import REPO_ROOT, sha256_file

pytestmark = pytest.mark.skipif(
    not raw_files_present(),
    reason="data/raw has no CSV files - run `uv run python -m src.download_data` first",
)

# Observed for revision 7309ddb3 (see data/README.md). Schema drift fails loudly.
EXPECTED_ROWS = {"members": 500, "providers": 150, "medical_claims": 12845, "pharmacy_claims": 18310, "adherence": 10627}
EXPECTED_N_COLUMNS = {"members": 44, "providers": 7, "medical_claims": 54, "pharmacy_claims": 35, "adherence": 7}
UNIQUE_KEYS = {"members": "member_id", "providers": "provider_npi", "medical_claims": "claim_id", "pharmacy_claims": "rx_claim_id"}
COMPOSITE_KEYS = {"adherence": ["member_id", "therapeutic_class"]}

REQUIRED_COLUMNS = {
    "members": [
        "member_id", "age", "age_band", "sex", "race_ethnicity", "state", "zip_code", "payer_type", "plan_type",
        "income_band", "dual_eligible_flag", "lis_flag", "hcc_risk_score", "n_chronic_conditions",
        "enrollment_start", "enrollment_end", "care_management_flag", "ccw_diabetes",
    ],
    "providers": ["provider_npi", "provider_type", "specialty", "nucc_taxonomy", "state", "network_status", "group_id"],
    "medical_claims": [
        "claim_id", "member_id", "claim_type", "service_date_from", "service_date_to", "adjudication_date", "plan_id",
        "rendering_npi", "billing_npi", "provider_specialty", "network_status", "primary_icd10_cm", "dx2",
        "drg_code", "mdc_code", "length_of_stay", "cpt_code", "cpt_category", "revenue_code", "place_of_service",
        "pos_description", "service_units", "billed_amount", "allowed_amount", "paid_amount", "member_deductible",
        "member_copay", "member_coinsurance", "member_oop", "cob_amount", "claim_status", "denial_code_carc",
        "denial_reason_desc", "auth_required_flag", "auth_number", "er_flag", "preventive_flag", "elective_flag",
        "high_cost_flag", "readmission_flag_30d", "fraud_label", "fraud_pattern_type",
        "hedis_bcs", "hedis_col", "hedis_cdc_a1c", "hedis_awv", "hedis_depression",
    ],
    "pharmacy_claims": [
        "rx_claim_id", "member_id", "fill_date", "paid_date", "pharmacy_npi", "prescriber_npi", "plan_id", "ndc_11",
        "drug_name_generic", "drug_name_brand", "therapeutic_class", "atc_code", "formulary_tier", "days_supply",
        "quantity_dispensed", "refill_number", "pharmacy_type", "ingredient_cost", "dispensing_fee",
        "gross_amount_due", "copay_amount", "plan_paid", "early_refill_flag", "fraud_label_rx", "diversion_flag",
        "controlled_substance_flag", "end_date",
    ],
    "adherence": ["member_id", "therapeutic_class", "total_days_supply", "n_fills", "pdc", "mpr", "adherence_flag_pdc80"],
}

# (from_table, from_col, to_table, to_col, expected_unmatched_rows) - as recorded in the manifest.
RELATIONSHIP_EXPECTATIONS = [
    ("medical_claims", "member_id", "members", "member_id", 0),
    ("pharmacy_claims", "member_id", "members", "member_id", 0),
    ("adherence", "member_id", "members", "member_id", 0),
    ("medical_claims", "rendering_npi", "providers", "provider_npi", 0),
    ("medical_claims", "billing_npi", "providers", "provider_npi", 0),
    ("pharmacy_claims", "pharmacy_npi", "providers", "provider_npi", 18310),
    ("pharmacy_claims", "prescriber_npi", "providers", "provider_npi", 18310),
]


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip("data/processed/manifest.json missing - run `uv run python -m src.profile_data`")
    return load_manifest()


@pytest.fixture(scope="module")
def tables() -> dict[str, pd.DataFrame]:
    return {name: load_table(name) for name in TABLES}


# --------------------------------------------------------------------------- #
# Manifest <-> files                                                          #
# --------------------------------------------------------------------------- #
def test_manifest_source_is_pinned(manifest):
    assert manifest["source"]["repo"] == REPO_ID
    assert manifest["source"]["revision"] == REVISION
    assert manifest["source"]["license"] == LICENSE
    assert manifest["source"]["synthetic"] is True
    assert set(manifest["tables"]) == set(TABLES)


def test_manifest_has_section_13_shape(manifest):
    for name, t in manifest["tables"].items():
        for key in ("path", "sha256", "bytes", "rows", "columns", "candidate_keys", "date_columns", "date_ranges"):
            assert key in t, f"{name} lacks {key}"
        for c in t["columns"]:
            assert set(c) >= {"name", "dtype", "null_count", "n_unique", "sample_values"}
            assert all(len(s) <= 50 for s in c["sample_values"]), f"{name}.{c['name']} sample exceeds 50 chars"
            assert len(c["sample_values"]) <= 3
    for r in manifest["relationships"]:
        assert set(r) >= {"from", "to", "cardinality", "unmatched_from", "unmatched_from_denominator"}


@pytest.mark.parametrize("name", TABLES)
def test_manifest_matches_file_on_disk(manifest, name):
    t = manifest["tables"][name]
    path = REPO_ROOT / t["path"]
    assert path.name == TABLE_FILES[name]
    assert path.is_file(), f"{t['path']} missing"
    assert path.stat().st_size == t["bytes"] == EXPECTED_BYTES[TABLE_FILES[name]]
    assert sha256_file(path) == t["sha256"]


def test_dataset_card_saved_for_attribution():
    assert CARD_PATH.is_file()
    text = CARD_PATH.read_text(encoding="utf-8")
    assert "license: cc-by-nc-4.0" in text
    assert "xpertsystems/hlt008-sample" in text


# --------------------------------------------------------------------------- #
# load_table <-> manifest                                                     #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", TABLES)
def test_load_table_matches_manifest_rows_and_columns(manifest, tables, name):
    df = tables[name]
    t = manifest["tables"][name]
    assert len(df) == t["rows"] == EXPECTED_ROWS[name]
    assert df.shape[1] == t["n_columns"] == EXPECTED_N_COLUMNS[name]
    assert list(df.columns) == [c["name"] for c in t["columns"]]
    for c in t["columns"]:
        s = df[c["name"]]
        assert str(s.dtype) == c["dtype"], f"{name}.{c['name']} dtype {s.dtype} != manifest {c['dtype']}"
        assert int(s.isna().sum()) == c["null_count"]
        assert int(s.nunique(dropna=True)) == c["n_unique"]


@pytest.mark.parametrize("name", TABLES)
def test_required_columns_present(tables, name):
    missing = [c for c in REQUIRED_COLUMNS[name] if c not in tables[name].columns]
    assert not missing, f"{name} missing required columns: {missing}"


def test_unknown_table_rejected():
    with pytest.raises(KeyError):
        load_table("claims")


# --------------------------------------------------------------------------- #
# Dtype policy                                                                #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name", TABLES)
def test_identifier_and_code_columns_are_strings(tables, name):
    df = tables[name]
    for col in STRING_COLUMNS[name]:
        assert col in df.columns, f"{name}.{col} listed in STRING_COLUMNS but absent"
        assert pd.api.types.is_string_dtype(df[col].dtype), f"{name}.{col} is {df[col].dtype}, expected str"


def test_leading_zeros_and_npi_width_preserved(tables):
    rx, med, prov = tables["pharmacy_claims"], tables["medical_claims"], tables["providers"]
    assert (rx["ndc_11"].str.len() == 11).all()
    assert rx["ndc_11"].str.startswith("0").any()
    rev = med["revenue_code"].dropna()
    assert (rev.str.len() == 4).all() and rev.str.startswith("0").all()
    for s in (prov["provider_npi"], med["rendering_npi"], med["billing_npi"], rx["pharmacy_npi"], rx["prescriber_npi"]):
        assert (s.str.len() == 10).all()
    assert (tables["members"]["zip_code"].str.len() == 5).all()


def test_flags_and_amounts_are_numeric(tables):
    med = tables["medical_claims"]
    for col in ("fraud_label", "high_cost_flag", "auth_required_flag", "er_flag"):
        assert pd.api.types.is_integer_dtype(med[col].dtype)
        assert set(med[col].unique()) <= {0, 1}
    for col in ("billed_amount", "allowed_amount", "paid_amount"):
        assert pd.api.types.is_float_dtype(med[col].dtype)


def test_parse_dates_option(manifest):
    med = load_table("medical_claims", parse_dates=True)
    for col in manifest["tables"]["medical_claims"]["date_columns"]:
        assert pd.api.types.is_datetime64_any_dtype(med[col].dtype)
        assert med[col].isna().sum() == 0


# --------------------------------------------------------------------------- #
# Keys                                                                        #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("name,key", sorted(UNIQUE_KEYS.items()))
def test_single_column_keys_unique(manifest, tables, name, key):
    s = tables[name][key]
    assert s.isna().sum() == 0
    assert s.is_unique, f"{name}.{key} has {s.duplicated().sum()} duplicate rows"
    assert manifest["tables"][name]["candidate_keys"] == [key]


def test_adherence_composite_key_unique(manifest, tables):
    cols = COMPOSITE_KEYS["adherence"]
    assert not tables["adherence"].duplicated(cols).any()
    assert manifest["tables"]["adherence"]["composite_keys"] == [cols]
    assert manifest["tables"]["adherence"]["candidate_keys"] == []


@pytest.mark.parametrize("name", TABLES)
def test_no_duplicate_full_rows(tables, name):
    assert not tables[name].duplicated().any()


# --------------------------------------------------------------------------- #
# Relationships and dates                                                     #
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("ft,fc,tt,tc,expected_unmatched", RELATIONSHIP_EXPECTATIONS)
def test_relationships_match_manifest(manifest, tables, ft, fc, tt, tc, expected_unmatched):
    entry = next(r for r in manifest["relationships"] if r["from"] == f"{ft}.{fc}" and r["to"] == f"{tt}.{tc}")
    f = tables[ft][fc].dropna()
    unmatched = int((~f.isin(set(tables[tt][tc].dropna()))).sum())
    assert unmatched == entry["unmatched_from"] == expected_unmatched
    assert entry["unmatched_from_denominator"] == len(f) == len(tables[ft])
    assert tables[tt][tc].is_unique
    assert entry["cardinality"] == ("no_match" if expected_unmatched == len(f) else "many_to_one")


def test_every_member_and_provider_is_referenced(tables):
    members = set(tables["members"]["member_id"])
    for name in ("medical_claims", "pharmacy_claims", "adherence"):
        assert set(tables[name]["member_id"]) == members
    assert set(tables["medical_claims"]["rendering_npi"]) == set(tables["providers"]["provider_npi"])


@pytest.mark.parametrize("name", TABLES)
def test_date_ranges_match_manifest(manifest, tables, name):
    t = manifest["tables"][name]
    for col in t["date_columns"]:
        raw = tables[name][col]
        parsed = pd.to_datetime(raw, errors="coerce")
        assert int((raw.notna() & parsed.isna()).sum()) == t["date_unparseable"][col] == 0
        assert [parsed.min().strftime("%Y-%m-%d"), parsed.max().strftime("%Y-%m-%d")] == t["date_ranges"][col]
    assert set(t["date_columns"]) == {c for c in tables[name].columns if c.endswith(("_date", "_start", "_end")) or "date_" in c}


# --------------------------------------------------------------------------- #
# Observed facts the goldens depend on (documented in data/README.md)         #
# --------------------------------------------------------------------------- #
def test_denial_code_present_iff_denied(tables):
    med = tables["medical_claims"]
    assert set(med["claim_status"].unique()) == {"Paid", "Denied", "Adjusted", "Pended"}
    assert (med["denial_code_carc"].notna() == (med["claim_status"] == "Denied")).all()
    assert med["denial_code_carc"].isna().sum() == 11559


def test_fraud_pattern_type_is_label_derived(tables):
    med = tables["medical_claims"]
    assert (med["fraud_pattern_type"].notna() == (med["fraud_label"] == 1)).all()
    assert int(med["fraud_label"].sum()) == 647


def test_high_cost_flag_is_a_billed_amount_threshold(tables):
    med = tables["medical_claims"]
    flag0_max = med.loc[med["high_cost_flag"] == 0, "billed_amount"].max()
    flag1_min = med.loc[med["high_cost_flag"] == 1, "billed_amount"].min()
    assert flag1_min > flag0_max
    assert int(med["high_cost_flag"].sum()) == 300


def test_all_null_columns_recorded(manifest):
    assert manifest["tables"]["medical_claims"]["all_null_columns"] == [
        "dx3", "dx4", "dx5", "modifier1", "modifier2", "denial_reason_desc", "auth_number",
    ]
