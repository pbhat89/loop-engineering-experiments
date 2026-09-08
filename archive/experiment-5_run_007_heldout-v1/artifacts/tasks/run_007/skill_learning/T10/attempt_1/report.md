# T10 — Specialty spend and denials

## Summary

Task T10 (Specialty spend and denials) for run `run_007` / condition `skill_learning`, attempt 1: status **ok**; 5 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]
- providers: 150 rows, 7 columns [source: metrics.json#tables]

### provider_join

- rendering_npi -> providers.provider_npi (inner, validate=many_to_one): rows before -> after 12845 -> 12845; unmatched claims: 0 / 12845 = 0.000000 [source: metrics.json#provider_join]
- Distinct providers matched: 150 [source: metrics.json#provider_join.providers_matched]

### group_comparison

- provider_specialty: groups 25, flagged small (n < 30): 0 [source: metrics.json#group_comparison.groups]
- provider_specialty = ASC (n=966): denial rate [adjudicated_claims]: 93 / 929 = 0.100108 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = ASC: paid_amount sum: 775948.850000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Cardiology (n=157): denial rate [adjudicated_claims]: 20 / 151 = 0.132450 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Cardiology: paid_amount sum: 93897.520000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Clinical Laboratory (n=254): denial rate [adjudicated_claims]: 25 / 243 = 0.102881 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Clinical Laboratory: paid_amount sum: 168400.070000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Critical Access Hospital (n=1225): denial rate [adjudicated_claims]: 137 / 1172 = 0.116894 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Critical Access Hospital: paid_amount sum: 898337.360000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = DME Supplier (n=841): denial rate [adjudicated_claims]: 80 / 809 = 0.098888 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = DME Supplier: paid_amount sum: 634611.680000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Diagnostic Radiology (n=71): denial rate [adjudicated_claims]: 4 / 68 = 0.058824 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Diagnostic Radiology: paid_amount sum: 66168.880000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Endocrinology (n=509): denial rate [adjudicated_claims]: 55 / 482 = 0.114108 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Endocrinology: paid_amount sum: 419000.420000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Family Medicine (n=586): denial rate [adjudicated_claims]: 57 / 572 = 0.099650 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Family Medicine: paid_amount sum: 489734.370000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Gastroenterology (n=200): denial rate [adjudicated_claims]: 23 / 193 = 0.119171 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Gastroenterology: paid_amount sum: 135994.040000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = General Acute Care Hospital (n=619): denial rate [adjudicated_claims]: 53 / 591 = 0.089679 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = General Acute Care Hospital: paid_amount sum: 463652.270000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Geriatrics (n=515): denial rate [adjudicated_claims]: 48 / 492 = 0.097561 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Geriatrics: paid_amount sum: 409148.240000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Home Health (n=358): denial rate [adjudicated_claims]: 29 / 345 = 0.084058 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Home Health: paid_amount sum: 265949.330000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Internal Medicine (n=636): denial rate [adjudicated_claims]: 68 / 617 = 0.110211 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Internal Medicine: paid_amount sum: 453841.470000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Nephrology (n=493): denial rate [adjudicated_claims]: 46 / 470 = 0.097872 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Nephrology: paid_amount sum: 310059.460000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Neurology (n=271): denial rate [adjudicated_claims]: 18 / 265 = 0.067925 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Neurology: paid_amount sum: 213627.260000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = OB/GYN (n=363): denial rate [adjudicated_claims]: 30 / 348 = 0.086207 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = OB/GYN: paid_amount sum: 304013.210000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Oncology (n=405): denial rate [adjudicated_claims]: 47 / 384 = 0.122396 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Oncology: paid_amount sum: 287539.790000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Orthopedic Surgery (n=685): denial rate [adjudicated_claims]: 79 / 663 = 0.119155 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Orthopedic Surgery: paid_amount sum: 442598.510000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Outpatient Clinic (n=481): denial rate [adjudicated_claims]: 36 / 455 = 0.079121 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Outpatient Clinic: paid_amount sum: 365534.050000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Pediatrics (n=499): denial rate [adjudicated_claims]: 53 / 478 = 0.110879 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pediatrics: paid_amount sum: 414771.480000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Physical Therapy (n=399): denial rate [adjudicated_claims]: 50 / 379 = 0.131926 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Physical Therapy: paid_amount sum: 299024.710000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Psychiatry (n=191): denial rate [adjudicated_claims]: 21 / 180 = 0.116667 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Psychiatry: paid_amount sum: 146237.020000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Pulmonology (n=543): denial rate [adjudicated_claims]: 47 / 523 = 0.089866 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pulmonology: paid_amount sum: 407541.670000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = SNF (n=964): denial rate [adjudicated_claims]: 103 / 933 = 0.110397 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = SNF: paid_amount sum: 833672.860000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]
- provider_specialty = Urology (n=614): denial rate [adjudicated_claims]: 64 / 597 = 0.107203 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Urology: paid_amount sum: 484111.250000 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv]

### provider_ranking

- Top 10 providers by paid_amount_sum (min_claims=0); providers ranked: 10 [source: artifacts/tasks/run_007/skill_learning/T10/attempt_1/provider_ranking.csv]
- #1 1450094833 (Outpatient Clinic, In-Network, n=82): paid_amount_sum: 126138.730000 [source: metrics.json#provider_ranking.rows]
- #2 1847081578 (Urology, Out-of-Network, n=84): paid_amount_sum: 108309.730000 [source: metrics.json#provider_ranking.rows]
- #3 1696843572 (Critical Access Hospital, Out-of-Network, n=100): paid_amount_sum: 98833.820000 [source: metrics.json#provider_ranking.rows]
- #4 1434029575 (Endocrinology, In-Network, n=90): paid_amount_sum: 98269.400000 [source: metrics.json#provider_ranking.rows]
- #5 1780163051 (SNF, In-Network, n=91): paid_amount_sum: 97847.530000 [source: metrics.json#provider_ranking.rows]
- #6 1752470395 (Home Health, In-Network, n=104): paid_amount_sum: 97662.930000 [source: metrics.json#provider_ranking.rows]
- #7 1168246159 (Internal Medicine, In-Network, n=77): paid_amount_sum: 96552.300000 [source: metrics.json#provider_ranking.rows]
- #8 1486164553 (DME Supplier, In-Network, n=90): paid_amount_sum: 96244.070000 [source: metrics.json#provider_ranking.rows]
- #9 1590915516 (Physical Therapy, Out-of-Network, n=102): paid_amount_sum: 95888.540000 [source: metrics.json#provider_ranking.rows]
- #10 1991459367 (Neurology, Out-of-Network, n=93): paid_amount_sum: 95775.570000 [source: metrics.json#provider_ranking.rows]

## Artifacts

- `artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.csv`
- `artifacts/tasks/run_007/skill_learning/T10/attempt_1/group_comparison.png`
- `artifacts/tasks/run_007/skill_learning/T10/attempt_1/provider_ranking.csv`
- `artifacts/tasks/run_007/skill_learning/T10/attempt_1/metrics.json`
- `artifacts/tasks/run_007/skill_learning/T10/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.

## Method

- Seed: 42; plan sha256: `acf4cf0d022611f03f925fd3edf1d9ee4e2420c87f5b1bb561186bfcf061af6e`.
- Components (canonical order): load_tables, provider_join, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `provider_join` params: `{'provider_key': 'rendering_npi', 'how': 'inner', 'validate': 'many_to_one'}`
- `group_comparison` params: `{'group_by': ['provider_specialty'], 'metrics': ['claim_count', 'paid_amount_sum', 'paid_amount_mean', 'denial_rate'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `provider_ranking` params: `{'metric': 'paid_amount_sum', 'top_n': 10, 'min_claims': 0}`
- `write_report` params: `{'caveats': ['synthetic_data', 'small_groups'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'small_groups'].
