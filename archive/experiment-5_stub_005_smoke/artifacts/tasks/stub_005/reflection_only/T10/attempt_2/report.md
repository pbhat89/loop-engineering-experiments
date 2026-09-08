# T10 — Specialty spend and denials

## Summary

Task T10 (Specialty spend and denials) for run `stub_005` / condition `reflection_only`, attempt 2: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- providers: 150 rows, 7 columns

### group_comparison

- provider_specialty: groups 25, flagged small (n < 30): 0
- provider_specialty = ASC (n=966): denial rate [adjudicated_claims]: 0.100108
- provider_specialty = ASC: paid_amount sum: 775948.850000
- provider_specialty = Cardiology (n=157): denial rate [adjudicated_claims]: 0.132450
- provider_specialty = Cardiology: paid_amount sum: 93897.520000
- provider_specialty = Clinical Laboratory (n=254): denial rate [adjudicated_claims]: 0.102881
- provider_specialty = Clinical Laboratory: paid_amount sum: 168400.070000
- provider_specialty = Critical Access Hospital (n=1225): denial rate [adjudicated_claims]: 0.116894
- provider_specialty = Critical Access Hospital: paid_amount sum: 898337.360000
- provider_specialty = DME Supplier (n=841): denial rate [adjudicated_claims]: 0.098888
- provider_specialty = DME Supplier: paid_amount sum: 634611.680000
- provider_specialty = Diagnostic Radiology (n=71): denial rate [adjudicated_claims]: 0.058824
- provider_specialty = Diagnostic Radiology: paid_amount sum: 66168.880000
- provider_specialty = Endocrinology (n=509): denial rate [adjudicated_claims]: 0.114108
- provider_specialty = Endocrinology: paid_amount sum: 419000.420000
- provider_specialty = Family Medicine (n=586): denial rate [adjudicated_claims]: 0.099650
- provider_specialty = Family Medicine: paid_amount sum: 489734.370000
- provider_specialty = Gastroenterology (n=200): denial rate [adjudicated_claims]: 0.119171
- provider_specialty = Gastroenterology: paid_amount sum: 135994.040000
- provider_specialty = General Acute Care Hospital (n=619): denial rate [adjudicated_claims]: 0.089679
- provider_specialty = General Acute Care Hospital: paid_amount sum: 463652.270000
- provider_specialty = Geriatrics (n=515): denial rate [adjudicated_claims]: 0.097561
- provider_specialty = Geriatrics: paid_amount sum: 409148.240000
- provider_specialty = Home Health (n=358): denial rate [adjudicated_claims]: 0.084058
- provider_specialty = Home Health: paid_amount sum: 265949.330000
- provider_specialty = Internal Medicine (n=636): denial rate [adjudicated_claims]: 0.110211
- provider_specialty = Internal Medicine: paid_amount sum: 453841.470000
- provider_specialty = Nephrology (n=493): denial rate [adjudicated_claims]: 0.097872
- provider_specialty = Nephrology: paid_amount sum: 310059.460000
- provider_specialty = Neurology (n=271): denial rate [adjudicated_claims]: 0.067925
- provider_specialty = Neurology: paid_amount sum: 213627.260000
- provider_specialty = OB/GYN (n=363): denial rate [adjudicated_claims]: 0.086207
- provider_specialty = OB/GYN: paid_amount sum: 304013.210000
- provider_specialty = Oncology (n=405): denial rate [adjudicated_claims]: 0.122396
- provider_specialty = Oncology: paid_amount sum: 287539.790000
- provider_specialty = Orthopedic Surgery (n=685): denial rate [adjudicated_claims]: 0.119155
- provider_specialty = Orthopedic Surgery: paid_amount sum: 442598.510000
- provider_specialty = Outpatient Clinic (n=481): denial rate [adjudicated_claims]: 0.079121
- provider_specialty = Outpatient Clinic: paid_amount sum: 365534.050000
- provider_specialty = Pediatrics (n=499): denial rate [adjudicated_claims]: 0.110879
- provider_specialty = Pediatrics: paid_amount sum: 414771.480000
- provider_specialty = Physical Therapy (n=399): denial rate [adjudicated_claims]: 0.131926
- provider_specialty = Physical Therapy: paid_amount sum: 299024.710000
- provider_specialty = Psychiatry (n=191): denial rate [adjudicated_claims]: 0.116667
- provider_specialty = Psychiatry: paid_amount sum: 146237.020000
- provider_specialty = Pulmonology (n=543): denial rate [adjudicated_claims]: 0.089866
- provider_specialty = Pulmonology: paid_amount sum: 407541.670000
- provider_specialty = SNF (n=964): denial rate [adjudicated_claims]: 0.110397
- provider_specialty = SNF: paid_amount sum: 833672.860000
- provider_specialty = Urology (n=614): denial rate [adjudicated_claims]: 0.107203
- provider_specialty = Urology: paid_amount sum: 484111.250000

### provider_ranking

- Top 10 providers by paid_amount_sum (min_claims=30); providers ranked: 10
- #1 1450094833 (Outpatient Clinic, In-Network, n=82): paid_amount_sum: 126138.730000
- #2 1847081578 (Urology, Out-of-Network, n=84): paid_amount_sum: 108309.730000
- #3 1696843572 (Critical Access Hospital, Out-of-Network, n=100): paid_amount_sum: 98833.820000
- #4 1434029575 (Endocrinology, In-Network, n=90): paid_amount_sum: 98269.400000
- #5 1780163051 (SNF, In-Network, n=91): paid_amount_sum: 97847.530000
- #6 1752470395 (Home Health, In-Network, n=104): paid_amount_sum: 97662.930000
- #7 1168246159 (Internal Medicine, In-Network, n=77): paid_amount_sum: 96552.300000
- #8 1486164553 (DME Supplier, In-Network, n=90): paid_amount_sum: 96244.070000
- #9 1590915516 (Physical Therapy, Out-of-Network, n=102): paid_amount_sum: 95888.540000
- #10 1991459367 (Neurology, Out-of-Network, n=93): paid_amount_sum: 95775.570000

## Artifacts

- `artifacts/tasks/stub_005/reflection_only/T10/attempt_2/group_comparison.csv`
- `artifacts/tasks/stub_005/reflection_only/T10/attempt_2/group_comparison.png`
- `artifacts/tasks/stub_005/reflection_only/T10/attempt_2/provider_ranking.csv`
- `artifacts/tasks/stub_005/reflection_only/T10/attempt_2/metrics.json`
- `artifacts/tasks/stub_005/reflection_only/T10/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `ded2714d0a6533afc67db6c12d3c934a8059f7ab86fff3ee8c8bc06b151b8f5c`.
- Components (canonical order): load_tables, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty'], 'metrics': ['claim_count', 'paid_amount_sum', 'paid_amount_mean', 'denial_rate'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- `provider_ranking` params: `{'metric': 'paid_amount_sum', 'top_n': 10, 'min_claims': 30}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
