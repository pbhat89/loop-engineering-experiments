# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `stub_003` / condition `self_refine`, attempt 2: status **ok**; 3 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- providers: 150 rows, 7 columns

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

- `artifacts/tasks/stub_003/self_refine/T3/attempt_2/group_comparison.csv`
- `artifacts/tasks/stub_003/self_refine/T3/attempt_2/group_comparison.png`
- `artifacts/tasks/stub_003/self_refine/T3/attempt_2/metrics.json`
- `artifacts/tasks/stub_003/self_refine/T3/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `66c6edb4a3095d5c48ce33f87fe3c57eefa5419dde069eed323d6ad8342fc405`.
- Components (canonical order): load_tables, group_comparison, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty'], 'metrics': ['claim_count', 'paid_amount_sum'], 'denominator': 'all_claims', 'min_group_size': 0}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
