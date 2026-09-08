# T9 — Denial hotspots

## Summary

Task T9 (Denial hotspots) for run `run_007` / condition `reflection_only`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### denial_code_ranking

- Scope denied_claims: claims in scope 1286; distinct denial codes: 10 [source: metrics.json#denial_code_ranking]
- Code CO-15: share of claims in scope: 241 / 1286 = 0.187403 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-4: share of claims in scope: 206 / 1286 = 0.160187 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-11: share of claims in scope: 147 / 1286 = 0.114308 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-18: share of claims in scope: 138 / 1286 = 0.107309 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code PR-1: share of claims in scope: 120 / 1286 = 0.093313 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-27: share of claims in scope: 115 / 1286 = 0.089425 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-97: share of claims in scope: 99 / 1286 = 0.076983 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-50: share of claims in scope: 87 / 1286 = 0.067652 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-29: share of claims in scope: 82 / 1286 = 0.063764 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Code CO-119: share of claims in scope: 51 / 1286 = 0.039658 [source: artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv]
- Missing denial code overall: 11559 / 12845 = 0.899883 [source: metrics.json#denial_code_ranking.missing_denial_codes]
- Missing denial code among denied claims: 0 / 1286 = 0.000000 [source: metrics.json#denial_code_ranking.missing_denial_codes]

### denial_rate_by_segment

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
- network_status = In-Network: denial rate [all_claims]: 1095 / 10788 = 0.101502 [source: metrics.json#denial_rate_by_segment.segments.network_status]
- network_status = Out-of-Network: denial rate [all_claims]: 191 / 2057 = 0.092854 [source: metrics.json#denial_rate_by_segment.segments.network_status]

## Artifacts

- `artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_code_ranking.csv`
- `artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_rates_by_segment.csv`
- `artifacts/tasks/run_007/reflection_only/T9/attempt_1/denial_rate_by_segment.png`
- `artifacts/tasks/run_007/reflection_only/T9/attempt_1/metrics.json`
- `artifacts/tasks/run_007/reflection_only/T9/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.

## Method

- Seed: 42; plan sha256: `798b217b87897518beca45d03ab6440fa9ec4977bafac1193b8b175aed9e9614`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'denied_claims', 'quantify_missing': 'overall'}`
- `denial_rate_by_segment` params: `{'segments': ['place_of_service', 'auth_required_flag', 'network_status'], 'denominator': 'all_claims', 'min_group_size': 30}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'small_groups'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'descriptive_only', 'small_groups'].
