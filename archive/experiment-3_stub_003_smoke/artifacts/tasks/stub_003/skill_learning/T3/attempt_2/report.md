# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `stub_003` / condition `skill_learning`, attempt 2: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- providers: 150 rows, 7 columns

### group_comparison

- provider_specialty: groups 25, flagged small (n < 30): 0
- provider_specialty = ASC (n=966): denial rate [adjudicated_claims]: 0.100108
- provider_specialty = ASC: fraud rate: 0.052795
- provider_specialty = ASC: paid_amount sum: 775948.850000
- provider_specialty = Cardiology (n=157): denial rate [adjudicated_claims]: 0.132450
- provider_specialty = Cardiology: fraud rate: 0.057325
- provider_specialty = Cardiology: paid_amount sum: 93897.520000
- provider_specialty = Clinical Laboratory (n=254): denial rate [adjudicated_claims]: 0.102881
- provider_specialty = Clinical Laboratory: fraud rate: 0.062992
- provider_specialty = Clinical Laboratory: paid_amount sum: 168400.070000
- provider_specialty = Critical Access Hospital (n=1225): denial rate [adjudicated_claims]: 0.116894
- provider_specialty = Critical Access Hospital: fraud rate: 0.044082
- provider_specialty = Critical Access Hospital: paid_amount sum: 898337.360000
- provider_specialty = DME Supplier (n=841): denial rate [adjudicated_claims]: 0.098888
- provider_specialty = DME Supplier: fraud rate: 0.045184
- provider_specialty = DME Supplier: paid_amount sum: 634611.680000
- provider_specialty = Diagnostic Radiology (n=71): denial rate [adjudicated_claims]: 0.058824
- provider_specialty = Diagnostic Radiology: fraud rate: 0.070423
- provider_specialty = Diagnostic Radiology: paid_amount sum: 66168.880000
- provider_specialty = Endocrinology (n=509): denial rate [adjudicated_claims]: 0.114108
- provider_specialty = Endocrinology: fraud rate: 0.043222
- provider_specialty = Endocrinology: paid_amount sum: 419000.420000
- provider_specialty = Family Medicine (n=586): denial rate [adjudicated_claims]: 0.099650
- provider_specialty = Family Medicine: fraud rate: 0.049488
- provider_specialty = Family Medicine: paid_amount sum: 489734.370000
- provider_specialty = Gastroenterology (n=200): denial rate [adjudicated_claims]: 0.119171
- provider_specialty = Gastroenterology: fraud rate: 0.060000
- provider_specialty = Gastroenterology: paid_amount sum: 135994.040000
- provider_specialty = General Acute Care Hospital (n=619): denial rate [adjudicated_claims]: 0.089679
- provider_specialty = General Acute Care Hospital: fraud rate: 0.037157
- provider_specialty = General Acute Care Hospital: paid_amount sum: 463652.270000
- provider_specialty = Geriatrics (n=515): denial rate [adjudicated_claims]: 0.097561
- provider_specialty = Geriatrics: fraud rate: 0.067961
- provider_specialty = Geriatrics: paid_amount sum: 409148.240000
- provider_specialty = Home Health (n=358): denial rate [adjudicated_claims]: 0.084058
- provider_specialty = Home Health: fraud rate: 0.050279
- provider_specialty = Home Health: paid_amount sum: 265949.330000
- provider_specialty = Internal Medicine (n=636): denial rate [adjudicated_claims]: 0.110211
- provider_specialty = Internal Medicine: fraud rate: 0.051887
- provider_specialty = Internal Medicine: paid_amount sum: 453841.470000
- provider_specialty = Nephrology (n=493): denial rate [adjudicated_claims]: 0.097872
- provider_specialty = Nephrology: fraud rate: 0.040568
- provider_specialty = Nephrology: paid_amount sum: 310059.460000
- provider_specialty = Neurology (n=271): denial rate [adjudicated_claims]: 0.067925
- provider_specialty = Neurology: fraud rate: 0.070111
- provider_specialty = Neurology: paid_amount sum: 213627.260000
- provider_specialty = OB/GYN (n=363): denial rate [adjudicated_claims]: 0.086207
- provider_specialty = OB/GYN: fraud rate: 0.049587
- provider_specialty = OB/GYN: paid_amount sum: 304013.210000
- provider_specialty = Oncology (n=405): denial rate [adjudicated_claims]: 0.122396
- provider_specialty = Oncology: fraud rate: 0.051852
- provider_specialty = Oncology: paid_amount sum: 287539.790000
- provider_specialty = Orthopedic Surgery (n=685): denial rate [adjudicated_claims]: 0.119155
- provider_specialty = Orthopedic Surgery: fraud rate: 0.062774
- provider_specialty = Orthopedic Surgery: paid_amount sum: 442598.510000
- provider_specialty = Outpatient Clinic (n=481): denial rate [adjudicated_claims]: 0.079121
- provider_specialty = Outpatient Clinic: fraud rate: 0.064449
- provider_specialty = Outpatient Clinic: paid_amount sum: 365534.050000
- provider_specialty = Pediatrics (n=499): denial rate [adjudicated_claims]: 0.110879
- provider_specialty = Pediatrics: fraud rate: 0.058116
- provider_specialty = Pediatrics: paid_amount sum: 414771.480000
- provider_specialty = Physical Therapy (n=399): denial rate [adjudicated_claims]: 0.131926
- provider_specialty = Physical Therapy: fraud rate: 0.050125
- provider_specialty = Physical Therapy: paid_amount sum: 299024.710000
- provider_specialty = Psychiatry (n=191): denial rate [adjudicated_claims]: 0.116667
- provider_specialty = Psychiatry: fraud rate: 0.047120
- provider_specialty = Psychiatry: paid_amount sum: 146237.020000
- provider_specialty = Pulmonology (n=543): denial rate [adjudicated_claims]: 0.089866
- provider_specialty = Pulmonology: fraud rate: 0.046041
- provider_specialty = Pulmonology: paid_amount sum: 407541.670000
- provider_specialty = SNF (n=964): denial rate [adjudicated_claims]: 0.110397
- provider_specialty = SNF: fraud rate: 0.037344
- provider_specialty = SNF: paid_amount sum: 833672.860000
- provider_specialty = Urology (n=614): denial rate [adjudicated_claims]: 0.107203
- provider_specialty = Urology: fraud rate: 0.050489
- provider_specialty = Urology: paid_amount sum: 484111.250000
- network_status: groups 2, flagged small (n < 30): 0
- network_status = In-Network (n=10788): denial rate [adjudicated_claims]: 0.105593
- network_status = In-Network: fraud rate: 0.050334
- network_status = In-Network: paid_amount sum: 8073419.920000
- network_status = Out-of-Network (n=2057): denial rate [adjudicated_claims]: 0.097004
- network_status = Out-of-Network: fraud rate: 0.050559
- network_status = Out-of-Network: paid_amount sum: 1709995.850000

### provider_ranking

- Top 10 providers by claim_count (min_claims=0); providers ranked: 10
- #1 1186826716 (Physical Therapy, In-Network, n=115): claim_count: 115.000000
- #2 1563980627 (Critical Access Hospital, In-Network, n=108): claim_count: 108.000000
- #3 1609526529 (Psychiatry, In-Network, n=106): claim_count: 106.000000
- #4 1644128543 (Gastroenterology, In-Network, n=106): claim_count: 106.000000
- #5 1193493783 (Critical Access Hospital, Out-of-Network, n=105): claim_count: 105.000000
- #6 1752470395 (Home Health, In-Network, n=104): claim_count: 104.000000
- #7 1103747954 (Urology, In-Network, n=102): claim_count: 102.000000
- #8 1125190055 (Nephrology, In-Network, n=102): claim_count: 102.000000
- #9 1590915516 (Physical Therapy, Out-of-Network, n=102): claim_count: 102.000000
- #10 1531398223 (OB/GYN, In-Network, n=101): claim_count: 101.000000

## Artifacts

- `artifacts/tasks/stub_003/skill_learning/T3/attempt_2/group_comparison.csv`
- `artifacts/tasks/stub_003/skill_learning/T3/attempt_2/group_comparison.png`
- `artifacts/tasks/stub_003/skill_learning/T3/attempt_2/provider_ranking.csv`
- `artifacts/tasks/stub_003/skill_learning/T3/attempt_2/metrics.json`
- `artifacts/tasks/stub_003/skill_learning/T3/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `1c2f79c3220642ed33342187d6348d7cc2df3f38a8918c2a426f514a1925633c`.
- Components (canonical order): load_tables, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty', 'network_status'], 'metrics': ['claim_count', 'paid_amount_sum', 'paid_amount_mean', 'denial_rate', 'fraud_rate'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- `provider_ranking` params: `{'metric': 'claim_count', 'top_n': 10, 'min_claims': 0}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
