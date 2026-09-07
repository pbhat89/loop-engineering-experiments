# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `run_006` / condition `reflection_only`, attempt 2: status **ok**; 5 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- providers: 150 rows, 7 columns

### provider_join

- rendering_npi -> providers.provider_npi (inner, validate=many_to_one): rows before -> after 12845 -> 12845; unmatched claims: 0.000000
- Distinct providers matched: 150

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
- provider_specialty+network_status: groups 41, flagged small (n < 30): 0
- provider_specialty+network_status = ASC|In-Network (n=799): denial rate [adjudicated_claims]: 0.095052
- provider_specialty+network_status = ASC|In-Network: fraud rate: 0.051314
- provider_specialty+network_status = ASC|In-Network: paid_amount sum: 644206.180000
- provider_specialty+network_status = ASC|Out-of-Network (n=167): denial rate [adjudicated_claims]: 0.124224
- provider_specialty+network_status = ASC|Out-of-Network: fraud rate: 0.059880
- provider_specialty+network_status = ASC|Out-of-Network: paid_amount sum: 131742.670000
- provider_specialty+network_status = Cardiology|In-Network (n=157): denial rate [adjudicated_claims]: 0.132450
- provider_specialty+network_status = Cardiology|In-Network: fraud rate: 0.057325
- provider_specialty+network_status = Cardiology|In-Network: paid_amount sum: 93897.520000
- provider_specialty+network_status = Clinical Laboratory|In-Network (n=164): denial rate [adjudicated_claims]: 0.107595
- provider_specialty+network_status = Clinical Laboratory|In-Network: fraud rate: 0.073171
- provider_specialty+network_status = Clinical Laboratory|In-Network: paid_amount sum: 105964.550000
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network (n=90): denial rate [adjudicated_claims]: 0.094118
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network: fraud rate: 0.044444
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network: paid_amount sum: 62435.520000
- provider_specialty+network_status = Critical Access Hospital|In-Network (n=944): denial rate [adjudicated_claims]: 0.126652
- provider_specialty+network_status = Critical Access Hospital|In-Network: fraud rate: 0.039195
- provider_specialty+network_status = Critical Access Hospital|In-Network: paid_amount sum: 648344.440000
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network (n=281): denial rate [adjudicated_claims]: 0.083333
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network: fraud rate: 0.060498
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network: paid_amount sum: 249992.920000
- provider_specialty+network_status = DME Supplier|In-Network (n=841): denial rate [adjudicated_claims]: 0.098888
- provider_specialty+network_status = DME Supplier|In-Network: fraud rate: 0.045184
- provider_specialty+network_status = DME Supplier|In-Network: paid_amount sum: 634611.680000
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network (n=71): denial rate [adjudicated_claims]: 0.058824
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network: fraud rate: 0.070423
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network: paid_amount sum: 66168.880000
- provider_specialty+network_status = Endocrinology|In-Network (n=418): denial rate [adjudicated_claims]: 0.122807
- provider_specialty+network_status = Endocrinology|In-Network: fraud rate: 0.043062
- provider_specialty+network_status = Endocrinology|In-Network: paid_amount sum: 343979.670000
- provider_specialty+network_status = Endocrinology|Out-of-Network (n=91): denial rate [adjudicated_claims]: 0.072289
- provider_specialty+network_status = Endocrinology|Out-of-Network: fraud rate: 0.043956
- provider_specialty+network_status = Endocrinology|Out-of-Network: paid_amount sum: 75020.750000
- provider_specialty+network_status = Family Medicine|In-Network (n=421): denial rate [adjudicated_claims]: 0.095122
- provider_specialty+network_status = Family Medicine|In-Network: fraud rate: 0.047506
- provider_specialty+network_status = Family Medicine|In-Network: paid_amount sum: 353444.660000
- provider_specialty+network_status = Family Medicine|Out-of-Network (n=165): denial rate [adjudicated_claims]: 0.111111
- provider_specialty+network_status = Family Medicine|Out-of-Network: fraud rate: 0.054545
- provider_specialty+network_status = Family Medicine|Out-of-Network: paid_amount sum: 136289.710000
- provider_specialty+network_status = Gastroenterology|In-Network (n=200): denial rate [adjudicated_claims]: 0.119171
- provider_specialty+network_status = Gastroenterology|In-Network: fraud rate: 0.060000
- provider_specialty+network_status = Gastroenterology|In-Network: paid_amount sum: 135994.040000
- provider_specialty+network_status = General Acute Care Hospital|In-Network (n=351): denial rate [adjudicated_claims]: 0.090361
- provider_specialty+network_status = General Acute Care Hospital|In-Network: fraud rate: 0.039886
- provider_specialty+network_status = General Acute Care Hospital|In-Network: paid_amount sum: 243620.430000
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network (n=268): denial rate [adjudicated_claims]: 0.088803
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network: fraud rate: 0.033582
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network: paid_amount sum: 220031.840000
- provider_specialty+network_status = Geriatrics|In-Network (n=415): denial rate [adjudicated_claims]: 0.103015
- provider_specialty+network_status = Geriatrics|In-Network: fraud rate: 0.074699
- provider_specialty+network_status = Geriatrics|In-Network: paid_amount sum: 334138.310000
- provider_specialty+network_status = Geriatrics|Out-of-Network (n=100): denial rate [adjudicated_claims]: 0.074468
- provider_specialty+network_status = Geriatrics|Out-of-Network: fraud rate: 0.040000
- provider_specialty+network_status = Geriatrics|Out-of-Network: paid_amount sum: 75009.930000
- provider_specialty+network_status = Home Health|In-Network (n=358): denial rate [adjudicated_claims]: 0.084058
- provider_specialty+network_status = Home Health|In-Network: fraud rate: 0.050279
- provider_specialty+network_status = Home Health|In-Network: paid_amount sum: 265949.330000
- provider_specialty+network_status = Internal Medicine|In-Network (n=559): denial rate [adjudicated_claims]: 0.109057
- provider_specialty+network_status = Internal Medicine|In-Network: fraud rate: 0.050089
- provider_specialty+network_status = Internal Medicine|In-Network: paid_amount sum: 387765.970000
- provider_specialty+network_status = Internal Medicine|Out-of-Network (n=77): denial rate [adjudicated_claims]: 0.118421
- provider_specialty+network_status = Internal Medicine|Out-of-Network: fraud rate: 0.064935
- provider_specialty+network_status = Internal Medicine|Out-of-Network: paid_amount sum: 66075.500000
- provider_specialty+network_status = Nephrology|In-Network (n=413): denial rate [adjudicated_claims]: 0.094148
- provider_specialty+network_status = Nephrology|In-Network: fraud rate: 0.043584
- provider_specialty+network_status = Nephrology|In-Network: paid_amount sum: 274528.220000
- provider_specialty+network_status = Nephrology|Out-of-Network (n=80): denial rate [adjudicated_claims]: 0.116883
- provider_specialty+network_status = Nephrology|Out-of-Network: fraud rate: 0.025000
- provider_specialty+network_status = Nephrology|Out-of-Network: paid_amount sum: 35531.240000
- provider_specialty+network_status = Neurology|In-Network (n=178): denial rate [adjudicated_claims]: 0.069364
- provider_specialty+network_status = Neurology|In-Network: fraud rate: 0.056180
- provider_specialty+network_status = Neurology|In-Network: paid_amount sum: 117851.690000
- provider_specialty+network_status = Neurology|Out-of-Network (n=93): denial rate [adjudicated_claims]: 0.065217
- provider_specialty+network_status = Neurology|Out-of-Network: fraud rate: 0.096774
- provider_specialty+network_status = Neurology|Out-of-Network: paid_amount sum: 95775.570000
- provider_specialty+network_status = OB/GYN|In-Network (n=363): denial rate [adjudicated_claims]: 0.086207
- provider_specialty+network_status = OB/GYN|In-Network: fraud rate: 0.049587
- provider_specialty+network_status = OB/GYN|In-Network: paid_amount sum: 304013.210000
- provider_specialty+network_status = Oncology|In-Network (n=329): denial rate [adjudicated_claims]: 0.121019
- provider_specialty+network_status = Oncology|In-Network: fraud rate: 0.057751
- provider_specialty+network_status = Oncology|In-Network: paid_amount sum: 218319.950000
- provider_specialty+network_status = Oncology|Out-of-Network (n=76): denial rate [adjudicated_claims]: 0.128571
- provider_specialty+network_status = Oncology|Out-of-Network: fraud rate: 0.026316
- provider_specialty+network_status = Oncology|Out-of-Network: paid_amount sum: 69219.840000
- provider_specialty+network_status = Orthopedic Surgery|In-Network (n=685): denial rate [adjudicated_claims]: 0.119155
- provider_specialty+network_status = Orthopedic Surgery|In-Network: fraud rate: 0.062774
- provider_specialty+network_status = Orthopedic Surgery|In-Network: paid_amount sum: 442598.510000
- provider_specialty+network_status = Outpatient Clinic|In-Network (n=410): denial rate [adjudicated_claims]: 0.075130
- provider_specialty+network_status = Outpatient Clinic|In-Network: fraud rate: 0.063415
- provider_specialty+network_status = Outpatient Clinic|In-Network: paid_amount sum: 310473.080000
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network (n=71): denial rate [adjudicated_claims]: 0.101449
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network: fraud rate: 0.070423
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network: paid_amount sum: 55060.970000
- provider_specialty+network_status = Pediatrics|In-Network (n=499): denial rate [adjudicated_claims]: 0.110879
- provider_specialty+network_status = Pediatrics|In-Network: fraud rate: 0.058116
- provider_specialty+network_status = Pediatrics|In-Network: paid_amount sum: 414771.480000
- provider_specialty+network_status = Physical Therapy|In-Network (n=297): denial rate [adjudicated_claims]: 0.133333
- provider_specialty+network_status = Physical Therapy|In-Network: fraud rate: 0.053872
- provider_specialty+network_status = Physical Therapy|In-Network: paid_amount sum: 203136.170000
- provider_specialty+network_status = Physical Therapy|Out-of-Network (n=102): denial rate [adjudicated_claims]: 0.127660
- provider_specialty+network_status = Physical Therapy|Out-of-Network: fraud rate: 0.039216
- provider_specialty+network_status = Physical Therapy|Out-of-Network: paid_amount sum: 95888.540000
- provider_specialty+network_status = Psychiatry|In-Network (n=191): denial rate [adjudicated_claims]: 0.116667
- provider_specialty+network_status = Psychiatry|In-Network: fraud rate: 0.047120
- provider_specialty+network_status = Psychiatry|In-Network: paid_amount sum: 146237.020000
- provider_specialty+network_status = Pulmonology|In-Network (n=453): denial rate [adjudicated_claims]: 0.091533
- provider_specialty+network_status = Pulmonology|In-Network: fraud rate: 0.048565
- provider_specialty+network_status = Pulmonology|In-Network: paid_amount sum: 357491.430000
- provider_specialty+network_status = Pulmonology|Out-of-Network (n=90): denial rate [adjudicated_claims]: 0.081395
- provider_specialty+network_status = Pulmonology|Out-of-Network: fraud rate: 0.033333
- provider_specialty+network_status = Pulmonology|Out-of-Network: paid_amount sum: 50050.240000
- provider_specialty+network_status = SNF|In-Network (n=889): denial rate [adjudicated_claims]: 0.112791
- provider_specialty+network_status = SNF|In-Network: fraud rate: 0.032621
- provider_specialty+network_status = SNF|In-Network: paid_amount sum: 753010.580000
- provider_specialty+network_status = SNF|Out-of-Network (n=75): denial rate [adjudicated_claims]: 0.082192
- provider_specialty+network_status = SNF|Out-of-Network: fraud rate: 0.093333
- provider_specialty+network_status = SNF|Out-of-Network: paid_amount sum: 80662.280000
- provider_specialty+network_status = Urology|In-Network (n=454): denial rate [adjudicated_claims]: 0.104308
- provider_specialty+network_status = Urology|In-Network: fraud rate: 0.057269
- provider_specialty+network_status = Urology|In-Network: paid_amount sum: 339071.800000
- provider_specialty+network_status = Urology|Out-of-Network (n=160): denial rate [adjudicated_claims]: 0.115385
- provider_specialty+network_status = Urology|Out-of-Network: fraud rate: 0.031250
- provider_specialty+network_status = Urology|Out-of-Network: paid_amount sum: 145039.450000

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

- `artifacts/tasks/run_006/reflection_only/T3/attempt_2/group_comparison.csv`
- `artifacts/tasks/run_006/reflection_only/T3/attempt_2/group_comparison.png`
- `artifacts/tasks/run_006/reflection_only/T3/attempt_2/provider_ranking.csv`
- `artifacts/tasks/run_006/reflection_only/T3/attempt_2/metrics.json`
- `artifacts/tasks/run_006/reflection_only/T3/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `ff4777f42b897a2b4a3afb3681f31c0594fd59304ff22926fdff7966fdaf62d5`.
- Components (canonical order): load_tables, provider_join, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `provider_join` params: `{'provider_key': 'rendering_npi', 'how': 'inner', 'validate': 'many_to_one'}`
- `group_comparison` params: `{'group_by': ['provider_specialty', 'network_status', 'provider_specialty+network_status'], 'metrics': ['claim_count', 'paid_amount_sum', 'denial_rate', 'fraud_rate'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `provider_ranking` params: `{'metric': 'claim_count', 'top_n': 10, 'min_claims': 0}`
- `write_report` params: `{'caveats': ['synthetic_data'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data'].
