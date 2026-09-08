# T10 — Specialty spend and denials

## Summary

Task T10 (Specialty spend and denials) for run `run_007` / condition `reflection_only`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]
- providers: 150 rows, 7 columns [source: metrics.json#tables]

### group_comparison

- provider_specialty: groups 25, flagged small (n < 30): 0 [source: metrics.json#group_comparison.groups]
- provider_specialty = ASC (n=966): denial rate [all_claims]: 93 / 966 = 0.096273 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = ASC: paid_amount sum: 775948.850000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Cardiology (n=157): denial rate [all_claims]: 20 / 157 = 0.127389 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Cardiology: paid_amount sum: 93897.520000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Clinical Laboratory (n=254): denial rate [all_claims]: 25 / 254 = 0.098425 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Clinical Laboratory: paid_amount sum: 168400.070000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Critical Access Hospital (n=1225): denial rate [all_claims]: 137 / 1225 = 0.111837 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Critical Access Hospital: paid_amount sum: 898337.360000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = DME Supplier (n=841): denial rate [all_claims]: 80 / 841 = 0.095125 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = DME Supplier: paid_amount sum: 634611.680000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Diagnostic Radiology (n=71): denial rate [all_claims]: 4 / 71 = 0.056338 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Diagnostic Radiology: paid_amount sum: 66168.880000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Endocrinology (n=509): denial rate [all_claims]: 55 / 509 = 0.108055 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Endocrinology: paid_amount sum: 419000.420000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Family Medicine (n=586): denial rate [all_claims]: 57 / 586 = 0.097270 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Family Medicine: paid_amount sum: 489734.370000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Gastroenterology (n=200): denial rate [all_claims]: 23 / 200 = 0.115000 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Gastroenterology: paid_amount sum: 135994.040000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = General Acute Care Hospital (n=619): denial rate [all_claims]: 53 / 619 = 0.085622 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = General Acute Care Hospital: paid_amount sum: 463652.270000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Geriatrics (n=515): denial rate [all_claims]: 48 / 515 = 0.093204 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Geriatrics: paid_amount sum: 409148.240000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Home Health (n=358): denial rate [all_claims]: 29 / 358 = 0.081006 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Home Health: paid_amount sum: 265949.330000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Internal Medicine (n=636): denial rate [all_claims]: 68 / 636 = 0.106918 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Internal Medicine: paid_amount sum: 453841.470000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Nephrology (n=493): denial rate [all_claims]: 46 / 493 = 0.093306 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Nephrology: paid_amount sum: 310059.460000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Neurology (n=271): denial rate [all_claims]: 18 / 271 = 0.066421 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Neurology: paid_amount sum: 213627.260000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = OB/GYN (n=363): denial rate [all_claims]: 30 / 363 = 0.082645 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = OB/GYN: paid_amount sum: 304013.210000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Oncology (n=405): denial rate [all_claims]: 47 / 405 = 0.116049 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Oncology: paid_amount sum: 287539.790000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Orthopedic Surgery (n=685): denial rate [all_claims]: 79 / 685 = 0.115328 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Orthopedic Surgery: paid_amount sum: 442598.510000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Outpatient Clinic (n=481): denial rate [all_claims]: 36 / 481 = 0.074844 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Outpatient Clinic: paid_amount sum: 365534.050000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Pediatrics (n=499): denial rate [all_claims]: 53 / 499 = 0.106212 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pediatrics: paid_amount sum: 414771.480000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Physical Therapy (n=399): denial rate [all_claims]: 50 / 399 = 0.125313 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Physical Therapy: paid_amount sum: 299024.710000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Psychiatry (n=191): denial rate [all_claims]: 21 / 191 = 0.109948 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Psychiatry: paid_amount sum: 146237.020000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Pulmonology (n=543): denial rate [all_claims]: 47 / 543 = 0.086556 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pulmonology: paid_amount sum: 407541.670000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = SNF (n=964): denial rate [all_claims]: 103 / 964 = 0.106846 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = SNF: paid_amount sum: 833672.860000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]
- provider_specialty = Urology (n=614): denial rate [all_claims]: 64 / 614 = 0.104235 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Urology: paid_amount sum: 484111.250000 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv]

### provider_ranking

- Top 10 providers by paid_amount_sum (min_claims=30); providers ranked: 10 [source: artifacts/tasks/run_007/reflection_only/T10/attempt_1/provider_ranking.csv]
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

- `artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.csv`
- `artifacts/tasks/run_007/reflection_only/T10/attempt_1/group_comparison.png`
- `artifacts/tasks/run_007/reflection_only/T10/attempt_1/provider_ranking.csv`
- `artifacts/tasks/run_007/reflection_only/T10/attempt_1/metrics.json`
- `artifacts/tasks/run_007/reflection_only/T10/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.

## Method

- Seed: 42; plan sha256: `6e0390a624a366966b0812ba3efa59007cf4d252e349a057b055c91f7c9f94d7`.
- Components (canonical order): load_tables, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty'], 'metrics': ['claim_count', 'paid_amount_sum', 'paid_amount_mean', 'denial_rate'], 'denominator': 'all_claims', 'min_group_size': 30}`
- `provider_ranking` params: `{'metric': 'paid_amount_sum', 'top_n': 10, 'min_claims': 30}`
- `write_report` params: `{'caveats': ['synthetic_data', 'sample_preview', 'small_groups', 'descriptive_only'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'sample_preview', 'small_groups', 'descriptive_only'].
