# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `run_004` / condition `skill_learning`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- providers: 150 rows, 7 columns

### join_check

- medical_claims.member_id->members.member_id: many_to_one, unmatched left rows: 0 / 12845 = 0.000000
- medical_claims.rendering_npi->providers.provider_npi: many_to_one, unmatched left rows: 0 / 12845 = 0.000000
- medical_claims.billing_npi->providers.provider_npi: many_to_one, unmatched left rows: 0 / 12845 = 0.000000
- pharmacy_claims.member_id->members.member_id: many_to_one, unmatched left rows: 0 / 18310 = 0.000000
- pharmacy_claims.pharmacy_npi->providers.provider_npi: no_match, unmatched left rows: 18310 / 18310 = 1.000000
- adherence.member_id->members.member_id: many_to_one, unmatched left rows: 0 / 10627 = 0.000000

### group_comparison

- provider_specialty: groups 25, flagged small (n < 0): 0
- provider_specialty = ASC: paid_amount sum: 775948.850000
- provider_specialty = Cardiology: paid_amount sum: 93897.520000
- provider_specialty = Clinical Laboratory: paid_amount sum: 168400.070000
- provider_specialty = Critical Access Hospital: paid_amount sum: 898337.360000
- provider_specialty = DME Supplier: paid_amount sum: 634611.680000
- provider_specialty = Diagnostic Radiology: paid_amount sum: 66168.880000
- provider_specialty = Endocrinology: paid_amount sum: 419000.420000
- provider_specialty = Family Medicine: paid_amount sum: 489734.370000
- provider_specialty = Gastroenterology: paid_amount sum: 135994.040000
- provider_specialty = General Acute Care Hospital: paid_amount sum: 463652.270000
- provider_specialty = Geriatrics: paid_amount sum: 409148.240000
- provider_specialty = Home Health: paid_amount sum: 265949.330000
- provider_specialty = Internal Medicine: paid_amount sum: 453841.470000
- provider_specialty = Nephrology: paid_amount sum: 310059.460000
- provider_specialty = Neurology: paid_amount sum: 213627.260000
- provider_specialty = OB/GYN: paid_amount sum: 304013.210000
- provider_specialty = Oncology: paid_amount sum: 287539.790000
- provider_specialty = Orthopedic Surgery: paid_amount sum: 442598.510000
- provider_specialty = Outpatient Clinic: paid_amount sum: 365534.050000
- provider_specialty = Pediatrics: paid_amount sum: 414771.480000
- provider_specialty = Physical Therapy: paid_amount sum: 299024.710000
- provider_specialty = Psychiatry: paid_amount sum: 146237.020000
- provider_specialty = Pulmonology: paid_amount sum: 407541.670000
- provider_specialty = SNF: paid_amount sum: 833672.860000
- provider_specialty = Urology: paid_amount sum: 484111.250000

## Artifacts

- `artifacts/tasks/run_004/skill_learning/T3/attempt_1/group_comparison.csv`
- `artifacts/tasks/run_004/skill_learning/T3/attempt_1/group_comparison.png`
- `artifacts/tasks/run_004/skill_learning/T3/attempt_1/metrics.json`
- `artifacts/tasks/run_004/skill_learning/T3/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.

## Method

- Seed: 42; plan sha256: `b537841779a7b04d8f3b825c886b0c5ed39277925dafb916e9ad052c79db8906`.
- Components (canonical order): load_tables, join_check, group_comparison, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty'], 'metrics': ['claim_count', 'paid_amount_sum'], 'denominator': 'all_claims', 'min_group_size': 0}`
- `write_report` params: `{'caveats': ['synthetic_data', 'sample_preview', 'descriptive_only'], 'show_denominators': True, 'cite_artifacts': False}`
- `join_check` params: `{'pairs': ['medical_claims.member_id->members.member_id', 'medical_claims.rendering_npi->providers.provider_npi', 'medical_claims.billing_npi->providers.provider_npi', 'pharmacy_claims.member_id->members.member_id', 'pharmacy_claims.pharmacy_npi->providers.provider_npi', 'adherence.member_id->members.member_id']}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'sample_preview', 'descriptive_only'].
