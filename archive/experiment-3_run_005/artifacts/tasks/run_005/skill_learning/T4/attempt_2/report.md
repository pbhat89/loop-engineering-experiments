# T4 — Denial analysis

## Summary

Task T4 (Denial analysis) for run `run_005` / condition `skill_learning`, attempt 2: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### denial_code_ranking

- Scope denied_claims: claims in scope 1286; distinct denial codes: 10 [source: metrics.json#denial_code_ranking]
- Code CO-15: share of claims in scope: 241 / 1286 = 0.187403 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-4: share of claims in scope: 206 / 1286 = 0.160187 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-11: share of claims in scope: 147 / 1286 = 0.114308 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-18: share of claims in scope: 138 / 1286 = 0.107309 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code PR-1: share of claims in scope: 120 / 1286 = 0.093313 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-27: share of claims in scope: 115 / 1286 = 0.089425 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-97: share of claims in scope: 99 / 1286 = 0.076983 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-50: share of claims in scope: 87 / 1286 = 0.067652 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-29: share of claims in scope: 82 / 1286 = 0.063764 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Code CO-119: share of claims in scope: 51 / 1286 = 0.039658 [source: artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv]
- Missing denial code overall: 11559 / 12845 = 0.899883 [source: metrics.json#denial_code_ranking.missing_denial_codes]
- Missing denial code among denied claims: 0 / 1286 = 0.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes]
- Missing denial code among status Adjusted: 542 / 542 = 1.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]
- Missing denial code among status Denied: 0 / 1286 = 0.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]
- Missing denial code among status Paid: 10511 / 10511 = 1.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]
- Missing denial code among status Pended: 506 / 506 = 1.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes.by_status]

### denial_rate_by_segment

- claim_type = Institutional-IP: denial rate [adjudicated_claims]: 174 / 1861 = 0.093498 [source: metrics.json#denial_rate_by_segment.segments.claim_type]
- claim_type = Institutional-OP: denial rate [adjudicated_claims]: 419 / 3724 = 0.112513 [source: metrics.json#denial_rate_by_segment.segments.claim_type]
- claim_type = Professional: denial rate [adjudicated_claims]: 693 / 6754 = 0.102606 [source: metrics.json#denial_rate_by_segment.segments.claim_type]
- provider_specialty = ASC: denial rate [adjudicated_claims]: 93 / 929 = 0.100108 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Cardiology: denial rate [adjudicated_claims]: 20 / 151 = 0.132450 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Clinical Laboratory: denial rate [adjudicated_claims]: 25 / 243 = 0.102881 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Critical Access Hospital: denial rate [adjudicated_claims]: 137 / 1172 = 0.116894 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = DME Supplier: denial rate [adjudicated_claims]: 80 / 809 = 0.098888 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Diagnostic Radiology: denial rate [adjudicated_claims]: 4 / 68 = 0.058824 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Endocrinology: denial rate [adjudicated_claims]: 55 / 482 = 0.114108 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Family Medicine: denial rate [adjudicated_claims]: 57 / 572 = 0.099650 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Gastroenterology: denial rate [adjudicated_claims]: 23 / 193 = 0.119171 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = General Acute Care Hospital: denial rate [adjudicated_claims]: 53 / 591 = 0.089679 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Geriatrics: denial rate [adjudicated_claims]: 48 / 492 = 0.097561 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Home Health: denial rate [adjudicated_claims]: 29 / 345 = 0.084058 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Internal Medicine: denial rate [adjudicated_claims]: 68 / 617 = 0.110211 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Nephrology: denial rate [adjudicated_claims]: 46 / 470 = 0.097872 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Neurology: denial rate [adjudicated_claims]: 18 / 265 = 0.067925 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = OB/GYN: denial rate [adjudicated_claims]: 30 / 348 = 0.086207 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Oncology: denial rate [adjudicated_claims]: 47 / 384 = 0.122396 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Orthopedic Surgery: denial rate [adjudicated_claims]: 79 / 663 = 0.119155 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Outpatient Clinic: denial rate [adjudicated_claims]: 36 / 455 = 0.079121 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Pediatrics: denial rate [adjudicated_claims]: 53 / 478 = 0.110879 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Physical Therapy: denial rate [adjudicated_claims]: 50 / 379 = 0.131926 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Psychiatry: denial rate [adjudicated_claims]: 21 / 180 = 0.116667 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Pulmonology: denial rate [adjudicated_claims]: 47 / 523 = 0.089866 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = SNF: denial rate [adjudicated_claims]: 103 / 933 = 0.110397 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- provider_specialty = Urology: denial rate [adjudicated_claims]: 64 / 597 = 0.107203 [source: metrics.json#denial_rate_by_segment.segments.provider_specialty]
- network_status = In-Network: denial rate [adjudicated_claims]: 1095 / 10370 = 0.105593 [source: metrics.json#denial_rate_by_segment.segments.network_status]
- network_status = Out-of-Network: denial rate [adjudicated_claims]: 191 / 1969 = 0.097004 [source: metrics.json#denial_rate_by_segment.segments.network_status]
- place_of_service = 11: denial rate [adjudicated_claims]: 272 / 2655 = 0.102448 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 12: denial rate [adjudicated_claims]: 44 / 299 = 0.147157 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 20: denial rate [adjudicated_claims]: 31 / 349 = 0.088825 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 21: denial rate [adjudicated_claims]: 227 / 2444 = 0.092881 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 22: denial rate [adjudicated_claims]: 545 / 4946 = 0.110190 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 23: denial rate [adjudicated_claims]: 57 / 521 = 0.109405 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 31: denial rate [adjudicated_claims]: 18 / 206 = 0.087379 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 49: denial rate [adjudicated_claims]: 31 / 342 = 0.090643 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 50: denial rate [adjudicated_claims]: 22 / 204 = 0.107843 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 65: denial rate [adjudicated_claims]: 12 / 118 = 0.101695 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- place_of_service = 81: denial rate [adjudicated_claims]: 27 / 255 = 0.105882 [source: metrics.json#denial_rate_by_segment.segments.place_of_service]
- auth_required_flag = 0: denial rate [adjudicated_claims]: 1112 / 10519 = 0.105713 [source: metrics.json#denial_rate_by_segment.segments.auth_required_flag]
- auth_required_flag = 1: denial rate [adjudicated_claims]: 174 / 1820 = 0.095604 [source: metrics.json#denial_rate_by_segment.segments.auth_required_flag]

## Artifacts

- `artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_code_ranking.csv`
- `artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_rates_by_segment.csv`
- `artifacts/tasks/run_005/skill_learning/T4/attempt_2/denial_rate_by_segment.png`
- `artifacts/tasks/run_005/skill_learning/T4/attempt_2/metrics.json`
- `artifacts/tasks/run_005/skill_learning/T4/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.

## Method

- Seed: 42; plan sha256: `186155fd38b8f07d066dae3620a3a54d467808c98f6c7c5b4b19ea9786048135`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'denied_claims', 'quantify_missing': 'by_status'}`
- `denial_rate_by_segment` params: `{'segments': ['claim_type', 'provider_specialty', 'network_status', 'place_of_service', 'auth_required_flag'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'small_groups'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'descriptive_only', 'small_groups'].
