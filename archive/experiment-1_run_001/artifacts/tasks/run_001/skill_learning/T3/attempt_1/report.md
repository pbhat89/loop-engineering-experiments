# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `run_001` / condition `skill_learning`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]
- providers: 150 rows, 7 columns [source: metrics.json#tables]

### join_check

- medical_claims.rendering_npi->providers.provider_npi: many_to_one, unmatched left rows: 0 / 12845 = 0.000000 [source: metrics.json#join_check]

### provider_join

- rendering_npi -> providers.provider_npi (left, validate=many_to_one): rows before -> after 12845 -> 12845; unmatched claims: 0 / 12845 = 0.000000 [source: metrics.json#provider_join]
- Distinct providers matched: 150 [source: metrics.json#provider_join.providers_matched]

### group_comparison

- provider_specialty: groups 25, flagged small (n < 30): 0 [source: metrics.json#group_comparison.groups]
- provider_specialty = ASC (n=966): denial rate [adjudicated_claims]: 93 / 929 = 0.100108 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = ASC: fraud rate: 51 / 966 = 0.052795 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = ASC: paid_amount sum: 775948.850000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Cardiology (n=157): denial rate [adjudicated_claims]: 20 / 151 = 0.132450 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Cardiology: fraud rate: 9 / 157 = 0.057325 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Cardiology: paid_amount sum: 93897.520000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Clinical Laboratory (n=254): denial rate [adjudicated_claims]: 25 / 243 = 0.102881 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Clinical Laboratory: fraud rate: 16 / 254 = 0.062992 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Clinical Laboratory: paid_amount sum: 168400.070000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Critical Access Hospital (n=1225): denial rate [adjudicated_claims]: 137 / 1172 = 0.116894 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Critical Access Hospital: fraud rate: 54 / 1225 = 0.044082 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Critical Access Hospital: paid_amount sum: 898337.360000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = DME Supplier (n=841): denial rate [adjudicated_claims]: 80 / 809 = 0.098888 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = DME Supplier: fraud rate: 38 / 841 = 0.045184 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = DME Supplier: paid_amount sum: 634611.680000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Diagnostic Radiology (n=71): denial rate [adjudicated_claims]: 4 / 68 = 0.058824 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Diagnostic Radiology: fraud rate: 5 / 71 = 0.070423 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Diagnostic Radiology: paid_amount sum: 66168.880000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Endocrinology (n=509): denial rate [adjudicated_claims]: 55 / 482 = 0.114108 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Endocrinology: fraud rate: 22 / 509 = 0.043222 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Endocrinology: paid_amount sum: 419000.420000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Family Medicine (n=586): denial rate [adjudicated_claims]: 57 / 572 = 0.099650 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Family Medicine: fraud rate: 29 / 586 = 0.049488 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Family Medicine: paid_amount sum: 489734.370000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Gastroenterology (n=200): denial rate [adjudicated_claims]: 23 / 193 = 0.119171 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Gastroenterology: fraud rate: 12 / 200 = 0.060000 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Gastroenterology: paid_amount sum: 135994.040000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = General Acute Care Hospital (n=619): denial rate [adjudicated_claims]: 53 / 591 = 0.089679 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = General Acute Care Hospital: fraud rate: 23 / 619 = 0.037157 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = General Acute Care Hospital: paid_amount sum: 463652.270000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Geriatrics (n=515): denial rate [adjudicated_claims]: 48 / 492 = 0.097561 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Geriatrics: fraud rate: 35 / 515 = 0.067961 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Geriatrics: paid_amount sum: 409148.240000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Home Health (n=358): denial rate [adjudicated_claims]: 29 / 345 = 0.084058 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Home Health: fraud rate: 18 / 358 = 0.050279 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Home Health: paid_amount sum: 265949.330000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Internal Medicine (n=636): denial rate [adjudicated_claims]: 68 / 617 = 0.110211 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Internal Medicine: fraud rate: 33 / 636 = 0.051887 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Internal Medicine: paid_amount sum: 453841.470000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Nephrology (n=493): denial rate [adjudicated_claims]: 46 / 470 = 0.097872 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Nephrology: fraud rate: 20 / 493 = 0.040568 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Nephrology: paid_amount sum: 310059.460000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Neurology (n=271): denial rate [adjudicated_claims]: 18 / 265 = 0.067925 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Neurology: fraud rate: 19 / 271 = 0.070111 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Neurology: paid_amount sum: 213627.260000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = OB/GYN (n=363): denial rate [adjudicated_claims]: 30 / 348 = 0.086207 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = OB/GYN: fraud rate: 18 / 363 = 0.049587 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = OB/GYN: paid_amount sum: 304013.210000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Oncology (n=405): denial rate [adjudicated_claims]: 47 / 384 = 0.122396 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Oncology: fraud rate: 21 / 405 = 0.051852 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Oncology: paid_amount sum: 287539.790000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Orthopedic Surgery (n=685): denial rate [adjudicated_claims]: 79 / 663 = 0.119155 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Orthopedic Surgery: fraud rate: 43 / 685 = 0.062774 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Orthopedic Surgery: paid_amount sum: 442598.510000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Outpatient Clinic (n=481): denial rate [adjudicated_claims]: 36 / 455 = 0.079121 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Outpatient Clinic: fraud rate: 31 / 481 = 0.064449 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Outpatient Clinic: paid_amount sum: 365534.050000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Pediatrics (n=499): denial rate [adjudicated_claims]: 53 / 478 = 0.110879 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pediatrics: fraud rate: 29 / 499 = 0.058116 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pediatrics: paid_amount sum: 414771.480000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Physical Therapy (n=399): denial rate [adjudicated_claims]: 50 / 379 = 0.131926 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Physical Therapy: fraud rate: 20 / 399 = 0.050125 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Physical Therapy: paid_amount sum: 299024.710000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Psychiatry (n=191): denial rate [adjudicated_claims]: 21 / 180 = 0.116667 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Psychiatry: fraud rate: 9 / 191 = 0.047120 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Psychiatry: paid_amount sum: 146237.020000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Pulmonology (n=543): denial rate [adjudicated_claims]: 47 / 523 = 0.089866 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pulmonology: fraud rate: 25 / 543 = 0.046041 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Pulmonology: paid_amount sum: 407541.670000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = SNF (n=964): denial rate [adjudicated_claims]: 103 / 933 = 0.110397 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = SNF: fraud rate: 36 / 964 = 0.037344 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = SNF: paid_amount sum: 833672.860000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty = Urology (n=614): denial rate [adjudicated_claims]: 64 / 597 = 0.107203 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Urology: fraud rate: 31 / 614 = 0.050489 [source: metrics.json#group_comparison.groups.provider_specialty]
- provider_specialty = Urology: paid_amount sum: 484111.250000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- network_status: groups 2, flagged small (n < 30): 0 [source: metrics.json#group_comparison.groups]
- network_status = In-Network (n=10788): denial rate [adjudicated_claims]: 1095 / 10370 = 0.105593 [source: metrics.json#group_comparison.groups.network_status]
- network_status = In-Network: fraud rate: 543 / 10788 = 0.050334 [source: metrics.json#group_comparison.groups.network_status]
- network_status = In-Network: paid_amount sum: 8073419.920000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]
- network_status = Out-of-Network (n=2057): denial rate [adjudicated_claims]: 191 / 1969 = 0.097004 [source: metrics.json#group_comparison.groups.network_status]
- network_status = Out-of-Network: fraud rate: 104 / 2057 = 0.050559 [source: metrics.json#group_comparison.groups.network_status]
- network_status = Out-of-Network: paid_amount sum: 1709995.850000 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv]

### provider_ranking

- Top 10 providers by claim_count (min_claims=30); providers ranked: 10 [source: artifacts/tasks/run_001/skill_learning/T3/attempt_1/provider_ranking.csv]
- #1 1186826716 (Physical Therapy, In-Network, n=115): claim_count: 115.000000 [source: metrics.json#provider_ranking.rows]
- #2 1563980627 (Critical Access Hospital, In-Network, n=108): claim_count: 108.000000 [source: metrics.json#provider_ranking.rows]
- #3 1609526529 (Psychiatry, In-Network, n=106): claim_count: 106.000000 [source: metrics.json#provider_ranking.rows]
- #4 1644128543 (Gastroenterology, In-Network, n=106): claim_count: 106.000000 [source: metrics.json#provider_ranking.rows]
- #5 1193493783 (Critical Access Hospital, Out-of-Network, n=105): claim_count: 105.000000 [source: metrics.json#provider_ranking.rows]
- #6 1752470395 (Home Health, In-Network, n=104): claim_count: 104.000000 [source: metrics.json#provider_ranking.rows]
- #7 1103747954 (Urology, In-Network, n=102): claim_count: 102.000000 [source: metrics.json#provider_ranking.rows]
- #8 1125190055 (Nephrology, In-Network, n=102): claim_count: 102.000000 [source: metrics.json#provider_ranking.rows]
- #9 1590915516 (Physical Therapy, Out-of-Network, n=102): claim_count: 102.000000 [source: metrics.json#provider_ranking.rows]
- #10 1531398223 (OB/GYN, In-Network, n=101): claim_count: 101.000000 [source: metrics.json#provider_ranking.rows]

## Artifacts

- `artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.csv`
- `artifacts/tasks/run_001/skill_learning/T3/attempt_1/group_comparison.png`
- `artifacts/tasks/run_001/skill_learning/T3/attempt_1/provider_ranking.csv`
- `artifacts/tasks/run_001/skill_learning/T3/attempt_1/metrics.json`
- `artifacts/tasks/run_001/skill_learning/T3/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.

## Method

- Seed: 42; plan sha256: `271e2b0fc8700b6decbf4c91d5cfc05bee3e90aee6b2cf208dc2da845581e7d0`.
- Components (canonical order): load_tables, join_check, provider_join, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `join_check` params: `{'pairs': ['medical_claims.rendering_npi->providers.provider_npi']}`
- `group_comparison` params: `{'group_by': ['provider_specialty', 'network_status'], 'metrics': ['claim_count', 'paid_amount_sum', 'paid_amount_mean', 'denial_rate', 'fraud_rate'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `provider_join` params: `{'provider_key': 'rendering_npi', 'how': 'left', 'validate': 'many_to_one'}`
- `provider_ranking` params: `{'metric': 'claim_count', 'top_n': 10, 'min_claims': 30}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'association_not_causation', 'small_groups'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'descriptive_only', 'association_not_causation', 'small_groups'].
