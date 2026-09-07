# T4 — Denial analysis

## Summary

Task T4 (Denial analysis) for run `run_005` / condition `reflection_only`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### denial_code_ranking

- Scope denied_claims: claims in scope 1286; distinct denial codes: 10
- Code CO-15: share of claims in scope: 0.187403
- Code CO-4: share of claims in scope: 0.160187
- Code CO-11: share of claims in scope: 0.114308
- Code CO-18: share of claims in scope: 0.107309
- Code PR-1: share of claims in scope: 0.093313
- Code CO-27: share of claims in scope: 0.089425
- Code CO-97: share of claims in scope: 0.076983
- Code CO-50: share of claims in scope: 0.067652
- Code CO-29: share of claims in scope: 0.063764
- Code CO-119: share of claims in scope: 0.039658
- Missing denial code overall: 0.899883
- Missing denial code among denied claims: 0.000000

### denial_rate_by_segment

- claim_type = Institutional-IP: denial rate [all_claims]: 0.090109
- claim_type = Institutional-OP: denial rate [all_claims]: 0.108185
- claim_type = Professional: denial rate [all_claims]: 0.098424
- provider_specialty = ASC: denial rate [all_claims]: 0.096273
- provider_specialty = Cardiology: denial rate [all_claims]: 0.127389
- provider_specialty = Clinical Laboratory: denial rate [all_claims]: 0.098425
- provider_specialty = Critical Access Hospital: denial rate [all_claims]: 0.111837
- provider_specialty = DME Supplier: denial rate [all_claims]: 0.095125
- provider_specialty = Diagnostic Radiology: denial rate [all_claims]: 0.056338
- provider_specialty = Endocrinology: denial rate [all_claims]: 0.108055
- provider_specialty = Family Medicine: denial rate [all_claims]: 0.097270
- provider_specialty = Gastroenterology: denial rate [all_claims]: 0.115000
- provider_specialty = General Acute Care Hospital: denial rate [all_claims]: 0.085622
- provider_specialty = Geriatrics: denial rate [all_claims]: 0.093204
- provider_specialty = Home Health: denial rate [all_claims]: 0.081006
- provider_specialty = Internal Medicine: denial rate [all_claims]: 0.106918
- provider_specialty = Nephrology: denial rate [all_claims]: 0.093306
- provider_specialty = Neurology: denial rate [all_claims]: 0.066421
- provider_specialty = OB/GYN: denial rate [all_claims]: 0.082645
- provider_specialty = Oncology: denial rate [all_claims]: 0.116049
- provider_specialty = Orthopedic Surgery: denial rate [all_claims]: 0.115328
- provider_specialty = Outpatient Clinic: denial rate [all_claims]: 0.074844
- provider_specialty = Pediatrics: denial rate [all_claims]: 0.106212
- provider_specialty = Physical Therapy: denial rate [all_claims]: 0.125313
- provider_specialty = Psychiatry: denial rate [all_claims]: 0.109948
- provider_specialty = Pulmonology: denial rate [all_claims]: 0.086556
- provider_specialty = SNF: denial rate [all_claims]: 0.106846
- provider_specialty = Urology: denial rate [all_claims]: 0.104235
- network_status = In-Network: denial rate [all_claims]: 0.101502
- network_status = Out-of-Network: denial rate [all_claims]: 0.092854
- place_of_service = 11: denial rate [all_claims]: 0.098018
- place_of_service = 12: denial rate [all_claims]: 0.141479
- place_of_service = 20: denial rate [all_claims]: 0.084699
- place_of_service = 21: denial rate [all_claims]: 0.089546
- place_of_service = 22: denial rate [all_claims]: 0.105928
- place_of_service = 23: denial rate [all_claims]: 0.104972
- place_of_service = 31: denial rate [all_claims]: 0.084507
- place_of_service = 49: denial rate [all_claims]: 0.087571
- place_of_service = 50: denial rate [all_claims]: 0.103286
- place_of_service = 65: denial rate [all_claims]: 0.096000
- place_of_service = 81: denial rate [all_claims]: 0.101887
- auth_required_flag = 0: denial rate [all_claims]: 0.101460
- auth_required_flag = 1: denial rate [all_claims]: 0.092308

## Artifacts

- `artifacts/tasks/run_005/reflection_only/T4/attempt_1/denial_code_ranking.csv`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_1/denial_rates_by_segment.csv`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_1/denial_rate_by_segment.png`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_1/metrics.json`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_1/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.

## Method

- Seed: 42; plan sha256: `a5383341e4ef19d35fd968d73926ad49560eec5d9f0d54bc6403b9f0d081bae5`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'denied_claims', 'quantify_missing': 'overall'}`
- `denial_rate_by_segment` params: `{'segments': ['claim_type', 'provider_specialty', 'network_status', 'place_of_service', 'auth_required_flag'], 'denominator': 'all_claims', 'min_group_size': 0}`
- `write_report` params: `{'caveats': ['descriptive_only'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['descriptive_only'].
