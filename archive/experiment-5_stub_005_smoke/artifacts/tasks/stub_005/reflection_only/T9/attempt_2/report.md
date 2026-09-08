# T9 — Denial hotspots

## Summary

Task T9 (Denial hotspots) for run `stub_005` / condition `reflection_only`, attempt 2: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
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
- network_status = In-Network: denial rate [adjudicated_claims]: 0.105593
- network_status = Out-of-Network: denial rate [adjudicated_claims]: 0.097004

## Artifacts

- `artifacts/tasks/stub_005/reflection_only/T9/attempt_2/denial_code_ranking.csv`
- `artifacts/tasks/stub_005/reflection_only/T9/attempt_2/denial_rates_by_segment.csv`
- `artifacts/tasks/stub_005/reflection_only/T9/attempt_2/denial_rate_by_segment.png`
- `artifacts/tasks/stub_005/reflection_only/T9/attempt_2/metrics.json`
- `artifacts/tasks/stub_005/reflection_only/T9/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `d9eb95d7d83fe2ce820e0b8695d8169b8eecf72ed49a6f3e475715d93e504969`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'denied_claims', 'quantify_missing': 'overall'}`
- `denial_rate_by_segment` params: `{'segments': ['place_of_service', 'auth_required_flag', 'network_status'], 'denominator': 'adjudicated_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
