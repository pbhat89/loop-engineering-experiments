# T4 — Denial analysis

## Summary

Task T4 (Denial analysis) for run `run_006` / condition `self_refine_memory`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### denial_code_ranking

- Scope all_claims: claims in scope 12845; distinct denial codes: 10
- Code CO-15: share of claims in scope: 241 / 12845 = 0.018762
- Code CO-4: share of claims in scope: 206 / 12845 = 0.016037
- Code CO-11: share of claims in scope: 147 / 12845 = 0.011444
- Code CO-18: share of claims in scope: 138 / 12845 = 0.010743
- Code PR-1: share of claims in scope: 120 / 12845 = 0.009342
- Code CO-27: share of claims in scope: 115 / 12845 = 0.008953
- Code CO-97: share of claims in scope: 99 / 12845 = 0.007707
- Code CO-50: share of claims in scope: 87 / 12845 = 0.006773
- Code CO-29: share of claims in scope: 82 / 12845 = 0.006384
- Code CO-119: share of claims in scope: 51 / 12845 = 0.003970
- Missing denial code overall: 11559 / 12845 = 0.899883
- Missing denial code among denied claims: 0 / 1286 = 0.000000
- Missing denial code among status Adjusted: 542 / 542 = 1.000000
- Missing denial code among status Denied: 0 / 1286 = 0.000000
- Missing denial code among status Paid: 10511 / 10511 = 1.000000
- Missing denial code among status Pended: 506 / 506 = 1.000000

### denial_rate_by_segment

- claim_type = Institutional-IP: denial rate [all_claims]: 174 / 1931 = 0.090109
- claim_type = Institutional-OP: denial rate [all_claims]: 419 / 3873 = 0.108185
- claim_type = Professional: denial rate [all_claims]: 693 / 7041 = 0.098424
- provider_specialty = ASC: denial rate [all_claims]: 93 / 966 = 0.096273
- provider_specialty = Cardiology: denial rate [all_claims]: 20 / 157 = 0.127389
- provider_specialty = Clinical Laboratory: denial rate [all_claims]: 25 / 254 = 0.098425
- provider_specialty = Critical Access Hospital: denial rate [all_claims]: 137 / 1225 = 0.111837
- provider_specialty = DME Supplier: denial rate [all_claims]: 80 / 841 = 0.095125
- provider_specialty = Diagnostic Radiology: denial rate [all_claims]: 4 / 71 = 0.056338
- provider_specialty = Endocrinology: denial rate [all_claims]: 55 / 509 = 0.108055
- provider_specialty = Family Medicine: denial rate [all_claims]: 57 / 586 = 0.097270
- provider_specialty = Gastroenterology: denial rate [all_claims]: 23 / 200 = 0.115000
- provider_specialty = General Acute Care Hospital: denial rate [all_claims]: 53 / 619 = 0.085622
- provider_specialty = Geriatrics: denial rate [all_claims]: 48 / 515 = 0.093204
- provider_specialty = Home Health: denial rate [all_claims]: 29 / 358 = 0.081006
- provider_specialty = Internal Medicine: denial rate [all_claims]: 68 / 636 = 0.106918
- provider_specialty = Nephrology: denial rate [all_claims]: 46 / 493 = 0.093306
- provider_specialty = Neurology: denial rate [all_claims]: 18 / 271 = 0.066421
- provider_specialty = OB/GYN: denial rate [all_claims]: 30 / 363 = 0.082645
- provider_specialty = Oncology: denial rate [all_claims]: 47 / 405 = 0.116049
- provider_specialty = Orthopedic Surgery: denial rate [all_claims]: 79 / 685 = 0.115328
- provider_specialty = Outpatient Clinic: denial rate [all_claims]: 36 / 481 = 0.074844
- provider_specialty = Pediatrics: denial rate [all_claims]: 53 / 499 = 0.106212
- provider_specialty = Physical Therapy: denial rate [all_claims]: 50 / 399 = 0.125313
- provider_specialty = Psychiatry: denial rate [all_claims]: 21 / 191 = 0.109948
- provider_specialty = Pulmonology: denial rate [all_claims]: 47 / 543 = 0.086556
- provider_specialty = SNF: denial rate [all_claims]: 103 / 964 = 0.106846
- provider_specialty = Urology: denial rate [all_claims]: 64 / 614 = 0.104235
- network_status = In-Network: denial rate [all_claims]: 1095 / 10788 = 0.101502
- network_status = Out-of-Network: denial rate [all_claims]: 191 / 2057 = 0.092854
- place_of_service = 11: denial rate [all_claims]: 272 / 2775 = 0.098018
- place_of_service = 12: denial rate [all_claims]: 44 / 311 = 0.141479
- place_of_service = 20: denial rate [all_claims]: 31 / 366 = 0.084699
- place_of_service = 21: denial rate [all_claims]: 227 / 2535 = 0.089546
- place_of_service = 22: denial rate [all_claims]: 545 / 5145 = 0.105928
- place_of_service = 23: denial rate [all_claims]: 57 / 543 = 0.104972
- place_of_service = 31: denial rate [all_claims]: 18 / 213 = 0.084507
- place_of_service = 49: denial rate [all_claims]: 31 / 354 = 0.087571
- place_of_service = 50: denial rate [all_claims]: 22 / 213 = 0.103286
- place_of_service = 65: denial rate [all_claims]: 12 / 125 = 0.096000
- place_of_service = 81: denial rate [all_claims]: 27 / 265 = 0.101887
- auth_required_flag = 0: denial rate [all_claims]: 1112 / 10960 = 0.101460
- auth_required_flag = 1: denial rate [all_claims]: 174 / 1885 = 0.092308

## Artifacts

- `artifacts/tasks/run_006/self_refine_memory/T4/attempt_1/denial_code_ranking.csv`
- `artifacts/tasks/run_006/self_refine_memory/T4/attempt_1/denial_rates_by_segment.csv`
- `artifacts/tasks/run_006/self_refine_memory/T4/attempt_1/denial_rate_by_segment.png`
- `artifacts/tasks/run_006/self_refine_memory/T4/attempt_1/metrics.json`
- `artifacts/tasks/run_006/self_refine_memory/T4/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.

## Method

- Seed: 42; plan sha256: `eb232053f962f38e1e45c099c283645b84ced88e6137cd76b332cdfa73eb2047`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'all_claims', 'quantify_missing': 'by_status'}`
- `denial_rate_by_segment` params: `{'segments': ['claim_type', 'provider_specialty', 'network_status', 'place_of_service', 'auth_required_flag'], 'denominator': 'all_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'small_groups'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'descriptive_only', 'small_groups'].
