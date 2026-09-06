# A2 — Data steward: verification notes

Date: 2026-09-06 (UTC). Agent A2. Repository `claims-skill-loop`. All commands run from the
repository root with `uv run` (the `VIRTUAL_ENV` mismatch warning is harmless and omitted below).

## Deliverables

| unit | artifact | status |
|---|---|---|
| 1 | `src/download_data.py` | done — pinned per-file download, SHA-256 record, `load_manifest()`, idempotent CLI |
| 2 | `src/profile_data.py` + `artifacts/data_profile/*.profile.json` + `SUMMARY.md` | done — deterministic |
| 3 | `data/processed/manifest.json` | done — LEAD §13 shape plus documented extensions |
| 4 | `data/README.md` | done |
| 5 | `tests/test_data_contract.py` | done — 54 passed |

Also written: `data/raw/DATASET_CARD.md` (dataset card, attribution), `data/raw/download_record.json`.

## Commands run and outcomes

### 1. Metadata inspection + download (the project's only network access)

```
uv run python -m src.download_data
[download_data] metadata: licence=cc-by-nc-4.0 sha=7309ddb30e67468748b7aa9182d8517fe28c2f9c gated=False private=False
[download_data] downloading adherence.csv ... medical_claims.csv ... members.csv ... pharmacy_claims.csv ... providers.csv ... README.md -> DATASET_CARD.md
file                       bytes    expected  action     sha256
adherence.csv             520053      520053  downloaded b89e2343d5f8f8811c99660ef319bda88e4b5f27d772498a39e746e799956653
medical_claims.csv       3525830     3525830  downloaded 96ede50f98bbcdc82d0bb251945d794d934c55376cc1a0c45bbf35590578f41d
members.csv                79935       79935  downloaded 4b5c811048ed5966c17339490a472440cb4a792e23ab4136bd02077e6a694fc1
pharmacy_claims.csv      4335821     4335821  downloaded 7341275cee178873267ee608bb1a5df28386fbe5b72ee39fa7b25dffdccc92c6
providers.csv              10610       10610  downloaded 8a3a41e69ce6bf343066df4a883a52ac8b76d3ae1f935930e5b800dfac9b2551
DATASET_CARD.md            19082       19082  downloaded ee8f1162818a4dc36c69f9833da2d3f873a848f27cbb3544014398a8a021a416
exit=0
```

Re-verified against the lead's facts: public, not gated, licence `cc-by-nc-4.0`, resolved commit equals the
pinned revision, every byte size equals both the lead-recorded size and the size the Hub reports for that
revision (`hub_bytes` in the download record). The Hub did not expose LFS SHA-256 digests for these files
(they are stored as regular git blobs), so the local SHA-256 values above are the reference digests from
now on. `retrieved_at = 2026-09-06T13:19:44+00:00`.

Second run (idempotence): every file reported `present with <n> bytes - skipped`, exit 0, record rewritten
with identical hashes. `hf_hub_download`'s `.cache/huggingface` metadata directory inside `data/raw` is
removed after each run so `git status` stays clean; completeness is tracked by size + SHA-256 instead.

### 2. Profiling

```
uv run python -m src.profile_data
members              500 rows x  44 cols  keys=['member_id']
providers            150 rows x   7 cols  keys=['provider_npi']
medical_claims     12845 rows x  54 cols  keys=['claim_id']
pharmacy_claims    18310 rows x  35 cols  keys=['rx_claim_id']
adherence          10627 rows x   7 cols  keys=[['member_id', 'therapeutic_class']]
  medical_claims.member_id        -> members.member_id      many_to_one  unmatched 0/12845
  pharmacy_claims.member_id       -> members.member_id      many_to_one  unmatched 0/18310
  adherence.member_id             -> members.member_id      many_to_one  unmatched 0/10627
  medical_claims.rendering_npi    -> providers.provider_npi many_to_one  unmatched 0/12845
  medical_claims.billing_npi      -> providers.provider_npi many_to_one  unmatched 0/12845
  pharmacy_claims.pharmacy_npi    -> providers.provider_npi no_match     unmatched 18310/18310
  pharmacy_claims.prescriber_npi  -> providers.provider_npi no_match     unmatched 18310/18310
exit=0
```

Determinism: ran twice, `diff` of the five `*.profile.json` files: identical; `manifest.json` and
`SUMMARY.md` differ only in the single `generated_at` line. JSON is written with sorted keys.

Card-stated vs received shapes: members 500×44 (exact), providers 150×7 (exact), medical_claims
~12,800 → **12,845**×54, pharmacy_claims ~18,300 → **18,310**×35, adherence ~10,600 → **10,627**×7.

### 3. Tests

```
uv run --extra dev pytest tests/test_data_contract.py -q
......................................................                   [100%]
exit=0        (54 passed)
```

Skip path: `raw_files_present()` returns `False` for a directory without the five CSVs (checked against
`data/processed`), which triggers the module-level `skipif` with the reason
"data/raw has no CSV files - run `uv run python -m src.download_data` first".

## Anomalies and data-quality findings (all computed; see `artifacts/data_profile/SUMMARY.md`)

Synthetic-data reminder: every item below describes the generator's output, not real claims behaviour.

* **Duplicate IDs:** none. `claim_id`, `rx_claim_id`, `members.member_id`, `providers.provider_npi` are
  unique and non-null; (`member_id`, `therapeutic_class`) is unique in `adherence`; no duplicate full rows.
  Only `providers.group_id` repeats (`GRP4198` twice; 149 distinct of 150).
* **Orphan keys:** none for member joins or medical-claim NPI joins (0 unmatched; all 500 members and all
  150 providers referenced). `pharmacy_claims.pharmacy_npi` / `prescriber_npi` are unique per row (18,310
  distinct each) and match **no** provider: pharmacy claims cannot be joined to `providers`.
* `rendering_npi == billing_npi` on all 12,845 medical claims; claim-level `network_status` and
  `provider_specialty` agree with the provider directory on all rows.
* **Unparseable dates:** 0 in all eight date columns (ISO `yyyy-mm-dd`). Ranges: `service_date_from`
  2021-01-01…2023-12-31; `service_date_to` to 2024-01-09; `adjudication_date` 2021-01-08…2024-02-11;
  `fill_date` 2021-01-01…2023-12-31; `paid_date` to 2024-01-04; `end_date` to 2024-03-30;
  `enrollment_start` 2020-01-03…2021-01-01; `enrollment_end` constant 2023-12-31. 36 medical claims have
  `adjudication_date < service_date_to` (never `< service_date_from`) — this is the ~0.3% the dataset card's
  "claim date validity 99.7%" refers to. All medical claims fall inside the member's enrollment window.
* **Denial codes:** `denial_code_carc` present on all 1,286 Denied claims and on no other status
  (11,559 nulls = Paid 10,511 + Adjusted 542 + Pended 506). 10 distinct CARC values. `denial_reason_desc`
  and `auth_number` are entirely empty.
* **Label-derived fields:** `fraud_pattern_type` is non-null iff `fraud_label == 1` (647 rows, 5.037%).
  `high_cost_flag` (300 rows, 2.34%) is perfectly separable on `billed_amount` (flag 0 max 7,688.20; flag 1
  min 10,299.58) — any threshold in that gap reproduces it exactly. Both must be excluded from T6/T7 features.
* **Status/amount quirks:** Denied claims have `paid_amount == 0`; 404/506 Pended and 430/542 Adjusted claims
  have `paid_amount > 0`; 2,228 Paid claims have `paid_amount == 0`. `paid <= allowed <= billed` holds
  everywhere; no negative amounts; `member_oop == deductible + copay + coinsurance` on all rows.
* **Empty / structural / constant columns:** all-null `dx3, dx4, dx5, modifier1, modifier2,
  denial_reason_desc, auth_number`; `drg_code, drg_type, mdc_code, poa_flag` populated only for the 1,931
  Institutional-IP claims; `revenue_code` null for the 7,041 Professional claims; constant
  `members.enrollment_end`, `pharmacy_claims.controlled_substance_flag`, `adherence.adherence_flag_pdc80`
  (all 0 — max PDC 0.4447, so no positive class).
* `adherence.pdc == mpr` on every row; `pdc = round(total_days_supply / 1095, 4)` (card says 1096).
* `members.age_band` null for 2 members with `age == 0`.
* Leading zeros: `ndc_11` (e.g. `00440280560`) and `revenue_code` (`0636`) — lost by default pandas inference;
  `load_table` forces these and all identifier/code columns to `str`.

## Interface deviations from LEAD §13 / plan.md §10

* `columns[].dtype` values are `str`, `int64`, `float64` (pandas 3.0.5 default string dtype), not `object`
  as in the §13 example. Consumers should not compare against `"object"`.
* Additive fields only (nothing renamed or removed): top-level `manifest_version`, `generated_at`,
  `generator`, `pandas_version`, `conventions`, `consistency_checks`, `findings`; `source.*` adds
  `pretty_name`, `publisher`, `url`, `dataset_card_path`, `dataset_card_sha256`, `attribution`, `synthetic`;
  per table adds `n_columns`, `composite_keys`, `date_unparseable`, `all_null_columns`, `constant_columns`,
  `string_columns_forced`, `profile_path`; per relationship adds `from_rows`, `from_null_keys`,
  `from_distinct`, `unmatched_from_distinct`, `to_distinct`, `to_unique`, `to_keys_unreferenced`,
  `match_rate`. `cardinality` uses the extra value `no_match` when zero rows join.
* `candidate_keys` lists only single columns verified unique and non-null; multi-column keys go in
  `composite_keys` (adherence: `[["member_id", "therapeutic_class"]]`, `candidate_keys: []`).
* `download_data` writes `data/raw/download_record.json` (bytes/SHA-256/Hub metadata); the §13 manifest
  itself is written by `profile_data` and read via `download_data.load_manifest()`.

## Open items / requests to other agents

* A3 (goldens): use `manifest.tables.*.rows` (12,845 / 18,310 / 10,627, not the card's approximations),
  treat `fraud_pattern_type` and `high_cost_flag` as label-derived, and note that any T4 "missing denial
  code" metric is 0 among Denied claims and 11,559 overall.
* A6 (executor): pharmacy → provider joins are impossible in this sample; plan components should not offer
  them, or must report `no_match`.
* No blockers. No secrets written. Network was used once, for the download only.
