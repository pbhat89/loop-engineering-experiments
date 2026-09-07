# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `run_005` / condition `self_refine`, attempt 2: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- providers: 150 rows, 7 columns

### group_comparison

- provider_specialty+network_status: groups 41, flagged small (n < 0): 0
- provider_specialty+network_status = ASC|In-Network (n=799): denial rate [all_claims]: 73 / 799 = 0.091364
- provider_specialty+network_status = ASC|In-Network: fraud rate: 41 / 799 = 0.051314
- provider_specialty+network_status = ASC|In-Network: paid_amount sum: 644206.180000
- provider_specialty+network_status = ASC|Out-of-Network (n=167): denial rate [all_claims]: 20 / 167 = 0.119760
- provider_specialty+network_status = ASC|Out-of-Network: fraud rate: 10 / 167 = 0.059880
- provider_specialty+network_status = ASC|Out-of-Network: paid_amount sum: 131742.670000
- provider_specialty+network_status = Cardiology|In-Network (n=157): denial rate [all_claims]: 20 / 157 = 0.127389
- provider_specialty+network_status = Cardiology|In-Network: fraud rate: 9 / 157 = 0.057325
- provider_specialty+network_status = Cardiology|In-Network: paid_amount sum: 93897.520000
- provider_specialty+network_status = Clinical Laboratory|In-Network (n=164): denial rate [all_claims]: 17 / 164 = 0.103659
- provider_specialty+network_status = Clinical Laboratory|In-Network: fraud rate: 12 / 164 = 0.073171
- provider_specialty+network_status = Clinical Laboratory|In-Network: paid_amount sum: 105964.550000
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network (n=90): denial rate [all_claims]: 8 / 90 = 0.088889
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network: fraud rate: 4 / 90 = 0.044444
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network: paid_amount sum: 62435.520000
- provider_specialty+network_status = Critical Access Hospital|In-Network (n=944): denial rate [all_claims]: 115 / 944 = 0.121822
- provider_specialty+network_status = Critical Access Hospital|In-Network: fraud rate: 37 / 944 = 0.039195
- provider_specialty+network_status = Critical Access Hospital|In-Network: paid_amount sum: 648344.440000
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network (n=281): denial rate [all_claims]: 22 / 281 = 0.078292
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network: fraud rate: 17 / 281 = 0.060498
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network: paid_amount sum: 249992.920000
- provider_specialty+network_status = DME Supplier|In-Network (n=841): denial rate [all_claims]: 80 / 841 = 0.095125
- provider_specialty+network_status = DME Supplier|In-Network: fraud rate: 38 / 841 = 0.045184
- provider_specialty+network_status = DME Supplier|In-Network: paid_amount sum: 634611.680000
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network (n=71): denial rate [all_claims]: 4 / 71 = 0.056338
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network: fraud rate: 5 / 71 = 0.070423
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network: paid_amount sum: 66168.880000
- provider_specialty+network_status = Endocrinology|In-Network (n=418): denial rate [all_claims]: 49 / 418 = 0.117225
- provider_specialty+network_status = Endocrinology|In-Network: fraud rate: 18 / 418 = 0.043062
- provider_specialty+network_status = Endocrinology|In-Network: paid_amount sum: 343979.670000
- provider_specialty+network_status = Endocrinology|Out-of-Network (n=91): denial rate [all_claims]: 6 / 91 = 0.065934
- provider_specialty+network_status = Endocrinology|Out-of-Network: fraud rate: 4 / 91 = 0.043956
- provider_specialty+network_status = Endocrinology|Out-of-Network: paid_amount sum: 75020.750000
- provider_specialty+network_status = Family Medicine|In-Network (n=421): denial rate [all_claims]: 39 / 421 = 0.092637
- provider_specialty+network_status = Family Medicine|In-Network: fraud rate: 20 / 421 = 0.047506
- provider_specialty+network_status = Family Medicine|In-Network: paid_amount sum: 353444.660000
- provider_specialty+network_status = Family Medicine|Out-of-Network (n=165): denial rate [all_claims]: 18 / 165 = 0.109091
- provider_specialty+network_status = Family Medicine|Out-of-Network: fraud rate: 9 / 165 = 0.054545
- provider_specialty+network_status = Family Medicine|Out-of-Network: paid_amount sum: 136289.710000
- provider_specialty+network_status = Gastroenterology|In-Network (n=200): denial rate [all_claims]: 23 / 200 = 0.115000
- provider_specialty+network_status = Gastroenterology|In-Network: fraud rate: 12 / 200 = 0.060000
- provider_specialty+network_status = Gastroenterology|In-Network: paid_amount sum: 135994.040000
- provider_specialty+network_status = General Acute Care Hospital|In-Network (n=351): denial rate [all_claims]: 30 / 351 = 0.085470
- provider_specialty+network_status = General Acute Care Hospital|In-Network: fraud rate: 14 / 351 = 0.039886
- provider_specialty+network_status = General Acute Care Hospital|In-Network: paid_amount sum: 243620.430000
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network (n=268): denial rate [all_claims]: 23 / 268 = 0.085821
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network: fraud rate: 9 / 268 = 0.033582
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network: paid_amount sum: 220031.840000
- provider_specialty+network_status = Geriatrics|In-Network (n=415): denial rate [all_claims]: 41 / 415 = 0.098795
- provider_specialty+network_status = Geriatrics|In-Network: fraud rate: 31 / 415 = 0.074699
- provider_specialty+network_status = Geriatrics|In-Network: paid_amount sum: 334138.310000
- provider_specialty+network_status = Geriatrics|Out-of-Network (n=100): denial rate [all_claims]: 7 / 100 = 0.070000
- provider_specialty+network_status = Geriatrics|Out-of-Network: fraud rate: 4 / 100 = 0.040000
- provider_specialty+network_status = Geriatrics|Out-of-Network: paid_amount sum: 75009.930000
- provider_specialty+network_status = Home Health|In-Network (n=358): denial rate [all_claims]: 29 / 358 = 0.081006
- provider_specialty+network_status = Home Health|In-Network: fraud rate: 18 / 358 = 0.050279
- provider_specialty+network_status = Home Health|In-Network: paid_amount sum: 265949.330000
- provider_specialty+network_status = Internal Medicine|In-Network (n=559): denial rate [all_claims]: 59 / 559 = 0.105546
- provider_specialty+network_status = Internal Medicine|In-Network: fraud rate: 28 / 559 = 0.050089
- provider_specialty+network_status = Internal Medicine|In-Network: paid_amount sum: 387765.970000
- provider_specialty+network_status = Internal Medicine|Out-of-Network (n=77): denial rate [all_claims]: 9 / 77 = 0.116883
- provider_specialty+network_status = Internal Medicine|Out-of-Network: fraud rate: 5 / 77 = 0.064935
- provider_specialty+network_status = Internal Medicine|Out-of-Network: paid_amount sum: 66075.500000
- provider_specialty+network_status = Nephrology|In-Network (n=413): denial rate [all_claims]: 37 / 413 = 0.089588
- provider_specialty+network_status = Nephrology|In-Network: fraud rate: 18 / 413 = 0.043584
- provider_specialty+network_status = Nephrology|In-Network: paid_amount sum: 274528.220000
- provider_specialty+network_status = Nephrology|Out-of-Network (n=80): denial rate [all_claims]: 9 / 80 = 0.112500
- provider_specialty+network_status = Nephrology|Out-of-Network: fraud rate: 2 / 80 = 0.025000
- provider_specialty+network_status = Nephrology|Out-of-Network: paid_amount sum: 35531.240000
- provider_specialty+network_status = Neurology|In-Network (n=178): denial rate [all_claims]: 12 / 178 = 0.067416
- provider_specialty+network_status = Neurology|In-Network: fraud rate: 10 / 178 = 0.056180
- provider_specialty+network_status = Neurology|In-Network: paid_amount sum: 117851.690000
- provider_specialty+network_status = Neurology|Out-of-Network (n=93): denial rate [all_claims]: 6 / 93 = 0.064516
- provider_specialty+network_status = Neurology|Out-of-Network: fraud rate: 9 / 93 = 0.096774
- provider_specialty+network_status = Neurology|Out-of-Network: paid_amount sum: 95775.570000
- provider_specialty+network_status = OB/GYN|In-Network (n=363): denial rate [all_claims]: 30 / 363 = 0.082645
- provider_specialty+network_status = OB/GYN|In-Network: fraud rate: 18 / 363 = 0.049587
- provider_specialty+network_status = OB/GYN|In-Network: paid_amount sum: 304013.210000
- provider_specialty+network_status = Oncology|In-Network (n=329): denial rate [all_claims]: 38 / 329 = 0.115502
- provider_specialty+network_status = Oncology|In-Network: fraud rate: 19 / 329 = 0.057751
- provider_specialty+network_status = Oncology|In-Network: paid_amount sum: 218319.950000
- provider_specialty+network_status = Oncology|Out-of-Network (n=76): denial rate [all_claims]: 9 / 76 = 0.118421
- provider_specialty+network_status = Oncology|Out-of-Network: fraud rate: 2 / 76 = 0.026316
- provider_specialty+network_status = Oncology|Out-of-Network: paid_amount sum: 69219.840000
- provider_specialty+network_status = Orthopedic Surgery|In-Network (n=685): denial rate [all_claims]: 79 / 685 = 0.115328
- provider_specialty+network_status = Orthopedic Surgery|In-Network: fraud rate: 43 / 685 = 0.062774
- provider_specialty+network_status = Orthopedic Surgery|In-Network: paid_amount sum: 442598.510000
- provider_specialty+network_status = Outpatient Clinic|In-Network (n=410): denial rate [all_claims]: 29 / 410 = 0.070732
- provider_specialty+network_status = Outpatient Clinic|In-Network: fraud rate: 26 / 410 = 0.063415
- provider_specialty+network_status = Outpatient Clinic|In-Network: paid_amount sum: 310473.080000
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network (n=71): denial rate [all_claims]: 7 / 71 = 0.098592
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network: fraud rate: 5 / 71 = 0.070423
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network: paid_amount sum: 55060.970000
- provider_specialty+network_status = Pediatrics|In-Network (n=499): denial rate [all_claims]: 53 / 499 = 0.106212
- provider_specialty+network_status = Pediatrics|In-Network: fraud rate: 29 / 499 = 0.058116
- provider_specialty+network_status = Pediatrics|In-Network: paid_amount sum: 414771.480000
- provider_specialty+network_status = Physical Therapy|In-Network (n=297): denial rate [all_claims]: 38 / 297 = 0.127946
- provider_specialty+network_status = Physical Therapy|In-Network: fraud rate: 16 / 297 = 0.053872
- provider_specialty+network_status = Physical Therapy|In-Network: paid_amount sum: 203136.170000
- provider_specialty+network_status = Physical Therapy|Out-of-Network (n=102): denial rate [all_claims]: 12 / 102 = 0.117647
- provider_specialty+network_status = Physical Therapy|Out-of-Network: fraud rate: 4 / 102 = 0.039216
- provider_specialty+network_status = Physical Therapy|Out-of-Network: paid_amount sum: 95888.540000
- provider_specialty+network_status = Psychiatry|In-Network (n=191): denial rate [all_claims]: 21 / 191 = 0.109948
- provider_specialty+network_status = Psychiatry|In-Network: fraud rate: 9 / 191 = 0.047120
- provider_specialty+network_status = Psychiatry|In-Network: paid_amount sum: 146237.020000
- provider_specialty+network_status = Pulmonology|In-Network (n=453): denial rate [all_claims]: 40 / 453 = 0.088300
- provider_specialty+network_status = Pulmonology|In-Network: fraud rate: 22 / 453 = 0.048565
- provider_specialty+network_status = Pulmonology|In-Network: paid_amount sum: 357491.430000
- provider_specialty+network_status = Pulmonology|Out-of-Network (n=90): denial rate [all_claims]: 7 / 90 = 0.077778
- provider_specialty+network_status = Pulmonology|Out-of-Network: fraud rate: 3 / 90 = 0.033333
- provider_specialty+network_status = Pulmonology|Out-of-Network: paid_amount sum: 50050.240000
- provider_specialty+network_status = SNF|In-Network (n=889): denial rate [all_claims]: 97 / 889 = 0.109111
- provider_specialty+network_status = SNF|In-Network: fraud rate: 29 / 889 = 0.032621
- provider_specialty+network_status = SNF|In-Network: paid_amount sum: 753010.580000
- provider_specialty+network_status = SNF|Out-of-Network (n=75): denial rate [all_claims]: 6 / 75 = 0.080000
- provider_specialty+network_status = SNF|Out-of-Network: fraud rate: 7 / 75 = 0.093333
- provider_specialty+network_status = SNF|Out-of-Network: paid_amount sum: 80662.280000
- provider_specialty+network_status = Urology|In-Network (n=454): denial rate [all_claims]: 46 / 454 = 0.101322
- provider_specialty+network_status = Urology|In-Network: fraud rate: 26 / 454 = 0.057269
- provider_specialty+network_status = Urology|In-Network: paid_amount sum: 339071.800000
- provider_specialty+network_status = Urology|Out-of-Network (n=160): denial rate [all_claims]: 18 / 160 = 0.112500
- provider_specialty+network_status = Urology|Out-of-Network: fraud rate: 5 / 160 = 0.031250
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

- `artifacts/tasks/run_005/self_refine/T3/attempt_2/group_comparison.csv`
- `artifacts/tasks/run_005/self_refine/T3/attempt_2/group_comparison.png`
- `artifacts/tasks/run_005/self_refine/T3/attempt_2/provider_ranking.csv`
- `artifacts/tasks/run_005/self_refine/T3/attempt_2/metrics.json`
- `artifacts/tasks/run_005/self_refine/T3/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `ffbaff5f2e5b93aa1e2be5914b47eb4afc04d12b1d12724bc6da72dd2d8a47aa`.
- Components (canonical order): load_tables, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty+network_status'], 'metrics': ['claim_count', 'paid_amount_sum', 'denial_rate', 'fraud_rate'], 'denominator': 'all_claims', 'min_group_size': 0}`
- `provider_ranking` params: `{'metric': 'claim_count', 'top_n': 10, 'min_claims': 0}`
- `write_report` params: `{'caveats': ['synthetic_data'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data'].
