# T3 — Provider and network patterns

## Summary

Task T3 (Provider and network patterns) for run `run_005` / condition `skill_learning`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), providers (150 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]
- providers: 150 rows, 7 columns [source: metrics.json#tables]

### group_comparison

- provider_specialty+network_status: groups 41, flagged small (n < 0): 0 [source: metrics.json#group_comparison.groups]
- provider_specialty+network_status = ASC|In-Network (n=799): denial rate [adjudicated_claims]: 73 / 768 = 0.095052 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = ASC|In-Network: fraud rate: 41 / 799 = 0.051314 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = ASC|In-Network: paid_amount sum: 644206.180000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = ASC|Out-of-Network (n=167): denial rate [adjudicated_claims]: 20 / 161 = 0.124224 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = ASC|Out-of-Network: fraud rate: 10 / 167 = 0.059880 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = ASC|Out-of-Network: paid_amount sum: 131742.670000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Cardiology|In-Network (n=157): denial rate [adjudicated_claims]: 20 / 151 = 0.132450 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Cardiology|In-Network: fraud rate: 9 / 157 = 0.057325 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Cardiology|In-Network: paid_amount sum: 93897.520000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Clinical Laboratory|In-Network (n=164): denial rate [adjudicated_claims]: 17 / 158 = 0.107595 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Clinical Laboratory|In-Network: fraud rate: 12 / 164 = 0.073171 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Clinical Laboratory|In-Network: paid_amount sum: 105964.550000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network (n=90): denial rate [adjudicated_claims]: 8 / 85 = 0.094118 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network: fraud rate: 4 / 90 = 0.044444 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Clinical Laboratory|Out-of-Network: paid_amount sum: 62435.520000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Critical Access Hospital|In-Network (n=944): denial rate [adjudicated_claims]: 115 / 908 = 0.126652 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Critical Access Hospital|In-Network: fraud rate: 37 / 944 = 0.039195 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Critical Access Hospital|In-Network: paid_amount sum: 648344.440000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network (n=281): denial rate [adjudicated_claims]: 22 / 264 = 0.083333 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network: fraud rate: 17 / 281 = 0.060498 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Critical Access Hospital|Out-of-Network: paid_amount sum: 249992.920000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = DME Supplier|In-Network (n=841): denial rate [adjudicated_claims]: 80 / 809 = 0.098888 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = DME Supplier|In-Network: fraud rate: 38 / 841 = 0.045184 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = DME Supplier|In-Network: paid_amount sum: 634611.680000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network (n=71): denial rate [adjudicated_claims]: 4 / 68 = 0.058824 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network: fraud rate: 5 / 71 = 0.070423 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Diagnostic Radiology|Out-of-Network: paid_amount sum: 66168.880000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Endocrinology|In-Network (n=418): denial rate [adjudicated_claims]: 49 / 399 = 0.122807 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Endocrinology|In-Network: fraud rate: 18 / 418 = 0.043062 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Endocrinology|In-Network: paid_amount sum: 343979.670000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Endocrinology|Out-of-Network (n=91): denial rate [adjudicated_claims]: 6 / 83 = 0.072289 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Endocrinology|Out-of-Network: fraud rate: 4 / 91 = 0.043956 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Endocrinology|Out-of-Network: paid_amount sum: 75020.750000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Family Medicine|In-Network (n=421): denial rate [adjudicated_claims]: 39 / 410 = 0.095122 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Family Medicine|In-Network: fraud rate: 20 / 421 = 0.047506 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Family Medicine|In-Network: paid_amount sum: 353444.660000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Family Medicine|Out-of-Network (n=165): denial rate [adjudicated_claims]: 18 / 162 = 0.111111 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Family Medicine|Out-of-Network: fraud rate: 9 / 165 = 0.054545 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Family Medicine|Out-of-Network: paid_amount sum: 136289.710000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Gastroenterology|In-Network (n=200): denial rate [adjudicated_claims]: 23 / 193 = 0.119171 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Gastroenterology|In-Network: fraud rate: 12 / 200 = 0.060000 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Gastroenterology|In-Network: paid_amount sum: 135994.040000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = General Acute Care Hospital|In-Network (n=351): denial rate [adjudicated_claims]: 30 / 332 = 0.090361 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = General Acute Care Hospital|In-Network: fraud rate: 14 / 351 = 0.039886 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = General Acute Care Hospital|In-Network: paid_amount sum: 243620.430000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network (n=268): denial rate [adjudicated_claims]: 23 / 259 = 0.088803 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network: fraud rate: 9 / 268 = 0.033582 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = General Acute Care Hospital|Out-of-Network: paid_amount sum: 220031.840000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Geriatrics|In-Network (n=415): denial rate [adjudicated_claims]: 41 / 398 = 0.103015 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Geriatrics|In-Network: fraud rate: 31 / 415 = 0.074699 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Geriatrics|In-Network: paid_amount sum: 334138.310000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Geriatrics|Out-of-Network (n=100): denial rate [adjudicated_claims]: 7 / 94 = 0.074468 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Geriatrics|Out-of-Network: fraud rate: 4 / 100 = 0.040000 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Geriatrics|Out-of-Network: paid_amount sum: 75009.930000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Home Health|In-Network (n=358): denial rate [adjudicated_claims]: 29 / 345 = 0.084058 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Home Health|In-Network: fraud rate: 18 / 358 = 0.050279 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Home Health|In-Network: paid_amount sum: 265949.330000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Internal Medicine|In-Network (n=559): denial rate [adjudicated_claims]: 59 / 541 = 0.109057 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Internal Medicine|In-Network: fraud rate: 28 / 559 = 0.050089 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Internal Medicine|In-Network: paid_amount sum: 387765.970000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Internal Medicine|Out-of-Network (n=77): denial rate [adjudicated_claims]: 9 / 76 = 0.118421 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Internal Medicine|Out-of-Network: fraud rate: 5 / 77 = 0.064935 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Internal Medicine|Out-of-Network: paid_amount sum: 66075.500000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Nephrology|In-Network (n=413): denial rate [adjudicated_claims]: 37 / 393 = 0.094148 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Nephrology|In-Network: fraud rate: 18 / 413 = 0.043584 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Nephrology|In-Network: paid_amount sum: 274528.220000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Nephrology|Out-of-Network (n=80): denial rate [adjudicated_claims]: 9 / 77 = 0.116883 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Nephrology|Out-of-Network: fraud rate: 2 / 80 = 0.025000 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Nephrology|Out-of-Network: paid_amount sum: 35531.240000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Neurology|In-Network (n=178): denial rate [adjudicated_claims]: 12 / 173 = 0.069364 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Neurology|In-Network: fraud rate: 10 / 178 = 0.056180 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Neurology|In-Network: paid_amount sum: 117851.690000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Neurology|Out-of-Network (n=93): denial rate [adjudicated_claims]: 6 / 92 = 0.065217 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Neurology|Out-of-Network: fraud rate: 9 / 93 = 0.096774 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Neurology|Out-of-Network: paid_amount sum: 95775.570000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = OB/GYN|In-Network (n=363): denial rate [adjudicated_claims]: 30 / 348 = 0.086207 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = OB/GYN|In-Network: fraud rate: 18 / 363 = 0.049587 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = OB/GYN|In-Network: paid_amount sum: 304013.210000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Oncology|In-Network (n=329): denial rate [adjudicated_claims]: 38 / 314 = 0.121019 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Oncology|In-Network: fraud rate: 19 / 329 = 0.057751 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Oncology|In-Network: paid_amount sum: 218319.950000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Oncology|Out-of-Network (n=76): denial rate [adjudicated_claims]: 9 / 70 = 0.128571 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Oncology|Out-of-Network: fraud rate: 2 / 76 = 0.026316 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Oncology|Out-of-Network: paid_amount sum: 69219.840000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Orthopedic Surgery|In-Network (n=685): denial rate [adjudicated_claims]: 79 / 663 = 0.119155 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Orthopedic Surgery|In-Network: fraud rate: 43 / 685 = 0.062774 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Orthopedic Surgery|In-Network: paid_amount sum: 442598.510000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Outpatient Clinic|In-Network (n=410): denial rate [adjudicated_claims]: 29 / 386 = 0.075130 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Outpatient Clinic|In-Network: fraud rate: 26 / 410 = 0.063415 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Outpatient Clinic|In-Network: paid_amount sum: 310473.080000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network (n=71): denial rate [adjudicated_claims]: 7 / 69 = 0.101449 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network: fraud rate: 5 / 71 = 0.070423 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Outpatient Clinic|Out-of-Network: paid_amount sum: 55060.970000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Pediatrics|In-Network (n=499): denial rate [adjudicated_claims]: 53 / 478 = 0.110879 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Pediatrics|In-Network: fraud rate: 29 / 499 = 0.058116 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Pediatrics|In-Network: paid_amount sum: 414771.480000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Physical Therapy|In-Network (n=297): denial rate [adjudicated_claims]: 38 / 285 = 0.133333 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Physical Therapy|In-Network: fraud rate: 16 / 297 = 0.053872 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Physical Therapy|In-Network: paid_amount sum: 203136.170000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Physical Therapy|Out-of-Network (n=102): denial rate [adjudicated_claims]: 12 / 94 = 0.127660 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Physical Therapy|Out-of-Network: fraud rate: 4 / 102 = 0.039216 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Physical Therapy|Out-of-Network: paid_amount sum: 95888.540000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Psychiatry|In-Network (n=191): denial rate [adjudicated_claims]: 21 / 180 = 0.116667 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Psychiatry|In-Network: fraud rate: 9 / 191 = 0.047120 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Psychiatry|In-Network: paid_amount sum: 146237.020000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Pulmonology|In-Network (n=453): denial rate [adjudicated_claims]: 40 / 437 = 0.091533 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Pulmonology|In-Network: fraud rate: 22 / 453 = 0.048565 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Pulmonology|In-Network: paid_amount sum: 357491.430000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Pulmonology|Out-of-Network (n=90): denial rate [adjudicated_claims]: 7 / 86 = 0.081395 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Pulmonology|Out-of-Network: fraud rate: 3 / 90 = 0.033333 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Pulmonology|Out-of-Network: paid_amount sum: 50050.240000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = SNF|In-Network (n=889): denial rate [adjudicated_claims]: 97 / 860 = 0.112791 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = SNF|In-Network: fraud rate: 29 / 889 = 0.032621 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = SNF|In-Network: paid_amount sum: 753010.580000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = SNF|Out-of-Network (n=75): denial rate [adjudicated_claims]: 6 / 73 = 0.082192 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = SNF|Out-of-Network: fraud rate: 7 / 75 = 0.093333 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = SNF|Out-of-Network: paid_amount sum: 80662.280000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Urology|In-Network (n=454): denial rate [adjudicated_claims]: 46 / 441 = 0.104308 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Urology|In-Network: fraud rate: 26 / 454 = 0.057269 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Urology|In-Network: paid_amount sum: 339071.800000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]
- provider_specialty+network_status = Urology|Out-of-Network (n=160): denial rate [adjudicated_claims]: 18 / 156 = 0.115385 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Urology|Out-of-Network: fraud rate: 5 / 160 = 0.031250 [source: metrics.json#group_comparison.groups.provider_specialty+network_status]
- provider_specialty+network_status = Urology|Out-of-Network: paid_amount sum: 145039.450000 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv]

### provider_ranking

- Top 10 providers by claim_count (min_claims=0); providers ranked: 10 [source: artifacts/tasks/run_005/skill_learning/T3/attempt_1/provider_ranking.csv]
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

- `artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.csv`
- `artifacts/tasks/run_005/skill_learning/T3/attempt_1/group_comparison.png`
- `artifacts/tasks/run_005/skill_learning/T3/attempt_1/provider_ranking.csv`
- `artifacts/tasks/run_005/skill_learning/T3/attempt_1/metrics.json`
- `artifacts/tasks/run_005/skill_learning/T3/attempt_1/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.

## Method

- Seed: 42; plan sha256: `a5a4b68fde30e60882c9753eb14767f30661f2d31809bc050ff7c59b9ba839fa`.
- Components (canonical order): load_tables, group_comparison, provider_ranking, write_report.
- `load_tables` params: `{}`
- `group_comparison` params: `{'group_by': ['provider_specialty+network_status'], 'metrics': ['claim_count', 'paid_amount_sum', 'denial_rate', 'fraud_rate'], 'denominator': 'adjudicated_claims', 'min_group_size': 0}`
- `provider_ranking` params: `{'metric': 'claim_count', 'top_n': 10, 'min_claims': 0}`
- `write_report` params: `{'caveats': ['descriptive_only', 'small_groups'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['descriptive_only', 'small_groups'].
