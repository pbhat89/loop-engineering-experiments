# T4 — Denial analysis

## Summary

Task T4 (Denial analysis) for run `run_005` / condition `self_refine`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### denial_code_ranking

- Scope denied_claims: claims in scope 1286; distinct denial codes: 10 [source: metrics.json#denial_code_ranking]
- Code CO-15: share of claims in scope: 241 / 1286 = 0.187403 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-4: share of claims in scope: 206 / 1286 = 0.160187 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-11: share of claims in scope: 147 / 1286 = 0.114308 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-18: share of claims in scope: 138 / 1286 = 0.107309 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code PR-1: share of claims in scope: 120 / 1286 = 0.093313 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-27: share of claims in scope: 115 / 1286 = 0.089425 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-97: share of claims in scope: 99 / 1286 = 0.076983 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-50: share of claims in scope: 87 / 1286 = 0.067652 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-29: share of claims in scope: 82 / 1286 = 0.063764 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Code CO-119: share of claims in scope: 51 / 1286 = 0.039658 [source: artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv]
- Missing denial code overall: 11559 / 12845 = 0.899883 [source: metrics.json#denial_code_ranking.missing_denial_codes]
- Missing denial code among denied claims: 0 / 1286 = 0.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes]
- Missing denial code among status Adjusted: 542 / 542 = 1.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]
- Missing denial code among status Denied: 0 / 1286 = 0.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]
- Missing denial code among status Paid: 10511 / 10511 = 1.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]
- Missing denial code among status Pended: 506 / 506 = 1.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]

### denial_rate_by_segment

- claim_type = Institutional-IP: denial rate [all_claims]: 174 / 1931 = 0.090109 [source: metrics.json#denial_rate_by_segment.segments.claim_type]
- claim_type = Institutional-OP: denial rate [all_claims]: 419 / 3873 = 0.108185 [source: metrics.json#denial_rate_by_segment.segments.claim_type]
- claim_type = Professional: denial rate [all_claims]: 693 / 7041 = 0.098424 [source: metrics.json#denial_rate_by_segment.segments.claim_type]
- provider_specialty = ASC: denial rate [all_claims]: 93 / 966 = 0.096273 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Cardiology: denial rate [all_claims]: 20 / 157 = 0.127389 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Clinical Laboratory: denial rate [all_claims]: 25 / 254 = 0.098425 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Critical Access Hospital: denial rate [all_claims]: 137 / 1225 = 0.111837 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = DME Supplier: denial rate [all_claims]: 80 / 841 = 0.095125 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Diagnostic Radiology: denial rate [all_claims]: 4 / 71 = 0.056338 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Endocrinology: denial rate [all_claims]: 55 / 509 = 0.108055 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Family Medicine: denial rate [all_claims]: 57 / 586 = 0.097270 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Gastroenterology: denial rate [all_claims]: 23 / 200 = 0.115000 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = General Acute Care Hospital: denial rate [all_claims]: 53 / 619 = 0.085622 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Geriatrics: denial rate [all_claims]: 48 / 515 = 0.093204 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Home Health: denial rate [all_claims]: 29 / 358 = 0.081006 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Internal Medicine: denial rate [all_claims]: 68 / 636 = 0.106918 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Nephrology: denial rate [all_claims]: 46 / 493 = 0.093306 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Neurology: denial rate [all_claims]: 18 / 271 = 0.066421 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = OB/GYN: denial rate [all_claims]: 30 / 363 = 0.082645 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Oncology: denial rate [all_claims]: 47 / 405 = 0.116049 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Orthopedic Surgery: denial rate [all_claims]: 79 / 685 = 0.115328 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Outpatient Clinic: denial rate [all_claims]: 36 / 481 = 0.074844 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Pediatrics: denial rate [all_claims]: 53 / 499 = 0.106212 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Physical Therapy: denial rate [all_claims]: 50 / 399 = 0.125313 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Psychiatry: denial rate [all_claims]: 21 / 191 = 0.109948 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Pulmonology: denial rate [all_claims]: 47 / 543 = 0.086556 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = SNF: denial rate [all_claims]: 103 / 964 = 0.106846 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Urology: denial rate [all_claims]: 64 / 614 = 0.104235 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- network_status = In-Network: denial rate [all_claims]: 1095 / 10788 = 0.101502 [source: metrics.json#denial_rate_by_segment.segments.network_status]
- network_status = Out-of-Network: denial rate [all_claims]: 191 / 2057 = 0.092854 [source: metrics.json#denial_rate_by_segment.segments.network_status]
- place_of_service = 11: denial rate [all_claims]: 272 / 2775 = 0.098018 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 12: denial rate [all_claims]: 44 / 311 = 0.141479 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 20: denial rate [all_claims]: 31 / 366 = 0.084699 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 21: denial rate [all_claims]: 227 / 2535 = 0.089546 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 22: denial rate [all_claims]: 545 / 5145 = 0.105928 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 23: denial rate [all_claims]: 57 / 543 = 0.104972 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 31: denial rate [all_claims]: 18 / 213 = 0.084507 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 49: denial rate [all_claims]: 31 / 354 = 0.087571 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 50: denial rate [all_claims]: 22 / 213 = 0.103286 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 65: denial rate [all_claims]: 12 / 125 = 0.096000 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 81: denial rate [all_claims]: 27 / 265 = 0.101887 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- auth_required_flag = 0: denial rate [all_claims]: 1112 / 10960 = 0.101460 [source: metrics.json#denial_rate_by_segment.segments.auth_required_flag]
- auth_required_flag = 1: denial rate [all_claims]: 174 / 1885 = 0.092308 [source: metrics.json#denial_rate_by_segment.segments.auth_required_flag]

## Artifacts

- `artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_code_ranking.csv`
- `artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_rates_by_segment.csv`
- `artifacts/tasks/run_005/self_refine/T4/attempt_1/denial_rate_by_segment.png`
- `artifacts/tasks/run_005/self_refine/T4/attempt_1/metrics.json`
- `artifacts/tasks/run_005/self_refine/T4/attempt_1/report.md`

## Caveats

- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.

## Method

- Seed: 42; plan sha256: `7ee3e55d41820f93ff726af091123ea8a125358734afd2a911cc7e57b8334937`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'denied_claims', 'quantify_missing': 'by_status'}`
- `denial_rate_by_segment` params: `{'segments': ['claim_type', 'provider_specialty', 'network_status', 'place_of_service', 'auth_required_flag'], 'denominator': 'all_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': ['small_groups', 'descriptive_only'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['small_groups', 'descriptive_only'].
