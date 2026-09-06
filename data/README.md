# Data: HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview)

> **Every record in this directory is synthetic.** The dataset card states: no real claim
> records, no PHI, no real member identifiers, no real NPIs. All counts and patterns
> described below are properties of the generator's output and must not be presented
> as evidence about real-world healthcare claims.

## Source and retrieval

| item | value |
|---|---|
| Dataset | HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview) |
| Publisher | XpertSystems.ai |
| Hugging Face repository | `xpertsystems/hlt008-sample` (dataset, public, not gated) — <https://huggingface.co/datasets/xpertsystems/hlt008-sample> |
| Pinned revision (commit SHA) | `7309ddb30e67468748b7aa9182d8517fe28c2f9c` |
| Retrieved | 2026-09-06T13:19:44+00:00 (UTC) by `src/download_data.py` |
| Retrieval method | `huggingface_hub.hf_hub_download(repo_id, filename, repo_type="dataset", revision=<sha>, local_dir="data/raw")`, one call per file; the repository is never loaded as a single combined table (the files have different schemas) |
| Hub metadata at download time | licence `cc-by-nc-4.0`, `gated=False`, `private=False`, resolved sha equal to the pinned revision, per-file sizes equal to the local files |
| Download record | `data/raw/download_record.json` (bytes, SHA-256, Hub size and action per file) |

The download is the **only network access in this project**. Experiment runs read the
local files and `data/processed/manifest.json` only.

## Licence and attribution

The sample is released under **Creative Commons Attribution-NonCommercial 4.0
(CC BY-NC 4.0)**. This repository uses it for a non-commercial, educational
experiment. The dataset card (attribution source) is preserved verbatim at
`data/raw/DATASET_CARD.md` (19,082 bytes, SHA-256
`ee8f1162818a4dc36c69f9833da2d3f873a848f27cbb3544014398a8a021a416`).

Attribution text used in reports:

> HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview), XpertSystems.ai,
> <https://huggingface.co/datasets/xpertsystems/hlt008-sample>, revision
> `7309ddb3`, licence CC BY-NC 4.0. 100% synthetic data; no PHI.

Citation requested by the publisher:

```bibtex
@dataset{xpertsystems_hlt008_sample_2026,
  author    = {XpertSystems.ai},
  title     = {HLT-008 Synthetic Healthcare Claims Dataset (Sample Preview)},
  year      = 2026,
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/xpertsystems/hlt008-sample}
}
```

## Expected vs received files

Card-stated shapes are approximate ("~") for the three large tables; the received
shapes are exact.

| file | card-stated rows × cols | received rows × cols | bytes | SHA-256 |
|---|---:|---:|---:|---|
| `members.csv` | 500 × 44 | 500 × 44 | 79,935 | `4b5c811048ed5966c17339490a472440cb4a792e23ab4136bd02077e6a694fc1` |
| `providers.csv` | 150 × 7 | 150 × 7 | 10,610 | `8a3a41e69ce6bf343066df4a883a52ac8b76d3ae1f935930e5b800dfac9b2551` |
| `medical_claims.csv` | ~12,800 × 54 | 12,845 × 54 | 3,525,830 | `96ede50f98bbcdc82d0bb251945d794d934c55376cc1a0c45bbf35590578f41d` |
| `pharmacy_claims.csv` | ~18,300 × 35 | 18,310 × 35 | 4,335,821 | `7341275cee178873267ee608bb1a5df28386fbe5b72ee39fa7b25dffdccc92c6` |
| `adherence.csv` | ~10,600 × 7 | 10,627 × 7 | 520,053 | `b89e2343d5f8f8811c99660ef319bda88e4b5f27d772498a39e746e799956653` |
| `README.md` → `DATASET_CARD.md` | — | — | 19,082 | `ee8f1162818a4dc36c69f9833da2d3f873a848f27cbb3544014398a8a021a416` |

All five CSV files are UTF-8 without BOM, LF line endings, one header row. Byte
sizes match the sizes recorded when the revision was pinned and the sizes reported
by the Hub for that revision.

## Schema summary

Full column lists with dtype, null count, distinct count and three sorted sample
values (truncated to 50 characters) are in `data/processed/manifest.json`
(`tables.<name>.columns`); richer per-table profiles (value counts for
low-cardinality columns, numeric summaries, key checks, domain checks) are in
`artifacts/data_profile/<name>.profile.json`, summarised in
`artifacts/data_profile/SUMMARY.md`.

### `members` (500 rows × 44 columns) — key `member_id`
Demographics (`age`, `age_band`, `sex`, `race_ethnicity`, `state`, `zip_code`),
insurance (`payer_type`, `plan_type`, `income_band`, `dual_eligible_flag`,
`lis_flag`), risk (`hcc_risk_score`, `n_chronic_conditions`, `care_management_flag`),
enrollment (`enrollment_start` 2020-01-03…2021-01-01, `enrollment_end` constant
2023-12-31) and 27 binary `ccw_*` chronic-condition flags.

### `providers` (150 rows × 7 columns) — key `provider_npi`
`provider_npi`, `provider_type`, `specialty` (25 values), `nucc_taxonomy`, `state`,
`network_status` (In-Network 126 / Out-of-Network 24), `group_id` (149 distinct;
`GRP4198` appears twice).

### `medical_claims` (12,845 rows × 54 columns) — key `claim_id`
Identity (`claim_id`, `member_id`, `claim_type`, `service_date_from`,
`service_date_to`, `adjudication_date`, `plan_id`); provider attribution
(`rendering_npi`, `billing_npi`, `provider_specialty`, `network_status`); diagnosis
(`primary_icd10_cm`, `dx2`; `dx3`–`dx5` empty); procedure (`cpt_code`,
`cpt_category`, `modifier1`/`modifier2` empty, `revenue_code`, `service_units`);
inpatient detail (`drg_code`, `drg_type`, `mdc_code`, `length_of_stay`, `poa_flag` —
populated only for `Institutional-IP`); place of service (`place_of_service`,
`pos_description`); financials (`billed_amount`, `allowed_amount`, `paid_amount`,
`member_deductible`, `member_copay`, `member_coinsurance`, `member_oop`,
`cob_amount`); adjudication (`claim_status`, `denial_code_carc`,
`denial_reason_desc` empty, `auth_required_flag`, `auth_number` empty); flags
(`er_flag`, `preventive_flag`, `elective_flag`, `high_cost_flag`,
`readmission_flag_30d`); labels (`fraud_label`, `fraud_pattern_type`); HEDIS flags
(`hedis_bcs`, `hedis_col`, `hedis_cdc_a1c`, `hedis_awv`, `hedis_depression`).

### `pharmacy_claims` (18,310 rows × 35 columns) — key `rx_claim_id`
Identity (`rx_claim_id`, `member_id`, `fill_date`, `paid_date`, `end_date`,
`pharmacy_npi`, `prescriber_npi`, `plan_id`, `bin_number`, `pcn_code`); drug coding
(`ndc_11`, `drug_name_generic`, `drug_name_brand`, `therapeutic_class`, `atc_code`);
pricing (`ingredient_cost`, `dispensing_fee`, `gross_amount_due`, `copay_amount`,
`plan_paid`, `dir_fee_amount`, `awp_per_unit`, `nadac_per_unit`); dispensing
(`formulary_tier`, `days_supply`, `quantity_dispensed`, `refill_number`,
`pharmacy_type`, `dispense_as_written_code`, `specialty_rx_flag`,
`compounded_flag`, `controlled_substance_flag` constant 0); anomaly flags
(`early_refill_flag`, `fraud_label_rx`, `diversion_flag`). The card lists 34 names;
the file also carries `end_date` (= `fill_date` + `days_supply` on every row).

### `adherence` (10,627 rows × 7 columns) — composite key (`member_id`, `therapeutic_class`)
`member_id`, `therapeutic_class` (37 values), `total_days_supply`, `n_fills`, `pdc`,
`mpr`, `adherence_flag_pdc80`.

### Dtype policy (`src/profile_data.load_table`)
Identifier and code columns are read as strings (pandas 3 `str` dtype): `member_id`,
`zip_code`, `provider_npi`, `group_id`, `nucc_taxonomy`, `claim_id`, `plan_id`,
`rendering_npi`, `billing_npi`, ICD/CPT/DRG/MDC/revenue/POS codes, `denial_code_carc`,
`rx_claim_id`, `pharmacy_npi`, `prescriber_npi`, `bin_number`, `pcn_code`, `ndc_11`,
`atc_code`, `dispense_as_written_code`. This matters: `ndc_11` and `revenue_code`
carry leading zeros (`00440280560`, `0636`) that pandas' default inference drops,
and 10-digit NPIs would otherwise become `int64`. Flags stay `int64`, measures stay
`int64`/`float64`, dates stay ISO `yyyy-mm-dd` strings unless
`load_table(name, parse_dates=True)` is used (then `pd.to_datetime(errors="coerce")`).

## Keys and relationships (from `manifest.json`)

| from | to | cardinality | unmatched rows / denominator |
|---|---|---|---:|
| `medical_claims.member_id` | `members.member_id` | many_to_one | 0 / 12,845 |
| `pharmacy_claims.member_id` | `members.member_id` | many_to_one | 0 / 18,310 |
| `adherence.member_id` | `members.member_id` | many_to_one | 0 / 10,627 |
| `medical_claims.rendering_npi` | `providers.provider_npi` | many_to_one | 0 / 12,845 |
| `medical_claims.billing_npi` | `providers.provider_npi` | many_to_one | 0 / 12,845 |
| `pharmacy_claims.pharmacy_npi` | `providers.provider_npi` | **no_match** | 18,310 / 18,310 |
| `pharmacy_claims.prescriber_npi` | `providers.provider_npi` | **no_match** | 18,310 / 18,310 |

* `claim_id`, `rx_claim_id`, `member_id` (members) and `provider_npi` are unique and
  non-null; (`member_id`, `therapeutic_class`) is unique in `adherence`. No duplicate
  full rows in any table.
* Every one of the 500 members appears in all three member-level tables; every one
  of the 150 providers is referenced by medical claims.
* `rendering_npi == billing_npi` on every medical claim, and the claim-level
  `network_status` / `provider_specialty` agree with the provider directory on all
  12,845 rows.
* Pharmacy `pharmacy_npi` and `prescriber_npi` are unique per row (18,310 distinct
  each) and never match the provider directory: pharmacy claims **cannot** be joined
  to providers.
* All medical `service_date_from` values fall inside the member's enrollment window.

## Data-quality findings relevant to the task suite

* **Label-derived fields.** `fraud_pattern_type` is populated exactly when
  `fraud_label == 1` (647 of 12,845 rows, 5.04%) — leakage for any fraud model.
  `high_cost_flag` (300 rows, 2.34%) is perfectly separable on `billed_amount`
  (flag 0 max 7,688.20; flag 1 min 10,299.58): it is a threshold on the claim
  amount, not an independent target.
* **Denial codes.** `denial_code_carc` is present on all 1,286 `Denied` claims and
  absent on every other status (11,559 nulls: Paid 10,511, Adjusted 542, Pended
  506). Ten distinct CARC values. `denial_reason_desc` is entirely empty.
* **Claim status mix.** Paid 10,511; Denied 1,286; Adjusted 542; Pended 506.
  Denied claims have `paid_amount` 0; 404 of 506 Pended and 430 of 542 Adjusted
  claims carry a positive `paid_amount`; 2,228 `Paid` claims have `paid_amount` 0.
  Denominator choices therefore change every rate.
* **Entirely empty columns** in `medical_claims`: `dx3`, `dx4`, `dx5`, `modifier1`,
  `modifier2`, `denial_reason_desc`, `auth_number`.
* **Structurally missing columns**: `drg_code`, `drg_type`, `mdc_code`, `poa_flag`
  are populated only for the 1,931 `Institutional-IP` claims; `revenue_code` is
  empty for the 7,041 `Professional` claims.
* **Dates.** All date columns parse with zero failures. `service_date_from` spans
  2021-01-01…2023-12-31; `service_date_to` and `adjudication_date` run into early
  2024. 36 claims have `adjudication_date` earlier than `service_date_to` (never
  earlier than `service_date_from`).
* **Constant columns**: `members.enrollment_end`, `pharmacy_claims.controlled_substance_flag`,
  `adherence.adherence_flag_pdc80` (all 0: no row reaches PDC 0.80; max 0.4447).
* `adherence.pdc == adherence.mpr` on every row; `pdc` equals
  `round(total_days_supply / 1095, 4)` (the card describes a 1,096-day window).
* `members.age_band` is null for 2 members whose `age` is 0.
* `providers.group_id` is not unique (`GRP4198` twice).

## Limitations

* **Synthetic and statistically assigned.** Fraud labels are a Bernoulli draw with
  rule-mapped pattern types (dataset card); nothing here validates against real
  adjudication. Findings illustrate analytical method, not healthcare reality.
* **Sample preview.** 500 members, 150 providers, three years (2021–2023). Small
  groups (e.g. by specialty × network) are unstable; the card itself states the
  sample is not sufficient for serious fraud-model training.
* **Non-commercial licence.** CC BY-NC 4.0 permits this educational use with
  attribution; commercial use requires the publisher's commercial licence.
* Codes are synthetic: NPIs, NDC-11 strings, plan/group identifiers are not real
  registry values; ICD-10 coverage is 50 codes.

## Reproducing the download and the profile

```bash
# from the repository root (Git Bash paths)
uv run python -m src.download_data            # idempotent: skips files present with the pinned size
uv run python -m src.download_data --force    # re-download everything
uv run python -m src.profile_data             # rewrites artifacts/data_profile/* and data/processed/manifest.json
uv run --extra dev pytest tests/test_data_contract.py -q
```

`src/download_data.py` pins `REVISION = "7309ddb30e67468748b7aa9182d8517fe28c2f9c"`
and refuses to proceed if any file is missing, has an unexpected size, or the Hub
reports a different licence or commit.

## Files in this directory

```
data/
├── README.md                  this file
├── raw/                       git-ignored CSVs (re-created by src/download_data.py)
│   ├── DATASET_CARD.md        dataset card (attribution; committed)
│   ├── download_record.json   per-file bytes/SHA-256 and Hub metadata (committed)
│   └── *.csv                  five tables
└── processed/
    └── manifest.json          data contract used by every other module
```
