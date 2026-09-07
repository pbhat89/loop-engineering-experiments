# T4 — Denial analysis

## Summary

Task T4 (Denial analysis) for run `run_005` / condition `reflection_only`, attempt 2: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
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

- claim_type = Institutional-IP: denial rate [adjudicated_claims]: 0.093498
- claim_type = Institutional-OP: denial rate [adjudicated_claims]: 0.112513
- claim_type = Professional: denial rate [adjudicated_claims]: 0.102606
- provider_specialty = ASC: denial rate [adjudicated_claims]: 0.100108
- provider_specialty = Cardiology: denial rate [adjudicated_claims]: 0.132450
- provider_specialty = Clinical Laboratory: denial rate [adjudicated_claims]: 0.102881
- provider_specialty = Critical Access Hospital: denial rate [adjudicated_claims]: 0.116894
- provider_specialty = DME Supplier: denial rate [adjudicated_claims]: 0.098888
- provider_specialty = Diagnostic Radiology: denial rate [adjudicated_claims]: 0.058824
- provider_specialty = Endocrinology: denial rate [adjudicated_claims]: 0.114108
- provider_specialty = Family Medicine: denial rate [adjudicated_claims]: 0.099650
- provider_specialty = Gastroenterology: denial rate [adjudicated_claims]: 0.119171
- provider_specialty = General Acute Care Hospital: denial rate [adjudicated_claims]: 0.089679
- provider_specialty = Geriatrics: denial rate [adjudicated_claims]: 0.097561
- provider_specialty = Home Health: denial rate [adjudicated_claims]: 0.084058
- provider_specialty = Internal Medicine: denial rate [adjudicated_claims]: 0.110211
- provider_specialty = Nephrology: denial rate [adjudicated_claims]: 0.097872
- provider_specialty = Neurology: denial rate [adjudicated_claims]: 0.067925
- provider_specialty = OB/GYN: denial rate [adjudicated_claims]: 0.086207
- provider_specialty = Oncology: denial rate [adjudicated_claims]: 0.122396
- provider_specialty = Orthopedic Surgery: denial rate [adjudicated_claims]: 0.119155
- provider_specialty = Outpatient Clinic: denial rate [adjudicated_claims]: 0.079121
- provider_specialty = Pediatrics: denial rate [adjudicated_claims]: 0.110879
- provider_specialty = Physical Therapy: denial rate [adjudicated_claims]: 0.131926
- provider_specialty = Psychiatry: denial rate [adjudicated_claims]: 0.116667
- provider_specialty = Pulmonology: denial rate [adjudicated_claims]: 0.089866
- provider_specialty = SNF: denial rate [adjudicated_claims]: 0.110397
- provider_specialty = Urology: denial rate [adjudicated_claims]: 0.107203
- network_status = In-Network: denial rate [adjudicated_claims]: 0.105593
- network_status = Out-of-Network: denial rate [adjudicated_claims]: 0.097004
- place_of_service = 11: denial rate [adjudicated_claims]: 0.102448
- place_of_service = 12: denial rate [adjudicated_claims]: 0.147157
- place_of_service = 20: denial rate [adjudicated_claims]: 0.088825
- place_of_service = 21: denial rate [adjudicated_claims]: 0.092881
- place_of_service = 22: denial rate [adjudicated_claims]: 0.110190
- place_of_service = 23: denial rate [adjudicated_claims]: 0.109405
- place_of_service = 31: denial rate [adjudicated_claims]: 0.087379
- place_of_service = 49: denial rate [adjudicated_claims]: 0.090643
- place_of_service = 50: denial rate [adjudicated_claims]: 0.107843
- place_of_service = 65: denial rate [adjudicated_claims]: 0.101695
- place_of_service = 81: denial rate [adjudicated_claims]: 0.105882
- auth_required_flag = 0: denial rate [adjudicated_claims]: 0.105713
- auth_required_flag = 1: denial rate [adjudicated_claims]: 0.095604

## Artifacts

- `artifacts/tasks/run_005/reflection_only/T4/attempt_2/denial_code_ranking.csv`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_2/denial_rates_by_segment.csv`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_2/denial_rate_by_segment.png`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_2/metrics.json`
- `artifacts/tasks/run_005/reflection_only/T4/attempt_2/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.

## Method

- Seed: 42; plan sha256: `df9ad0930f0ff2c6083ffcfe237c9ae129e4afdd57273590ddf29976b08fd411`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'denied_claims', 'quantify_missing': 'overall'}`
- `denial_rate_by_segment` params: `{'segments': ['claim_type', 'provider_specialty', 'network_status', 'place_of_service', 'auth_required_flag'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': ['descriptive_only'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['descriptive_only'].
