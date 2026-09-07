# T4 — Denial analysis

## Summary

Task T4 (Denial analysis) for run `stub_003` / condition `reflection_only`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### denial_code_ranking

- Scope all_claims: claims in scope 12845; distinct denial codes: 10
- Code CO-15: share of claims in scope: 0.018762
- Code CO-4: share of claims in scope: 0.016037
- Code CO-11: share of claims in scope: 0.011444
- Code CO-18: share of claims in scope: 0.010743
- Code PR-1: share of claims in scope: 0.009342
- Code CO-27: share of claims in scope: 0.008953
- Code CO-97: share of claims in scope: 0.007707
- Code CO-50: share of claims in scope: 0.006773
- Code CO-29: share of claims in scope: 0.006384
- Code CO-119: share of claims in scope: 0.003970
- Missing denial code overall: 0.899883
- Missing denial code among denied claims: 0.000000

### denial_rate_by_segment

- claim_type = Institutional-IP: denial rate [all_claims]: 0.090109
- claim_type = Institutional-OP: denial rate [all_claims]: 0.108185
- claim_type = Professional: denial rate [all_claims]: 0.098424

## Artifacts

- `artifacts/tasks/stub_003/reflection_only/T4/attempt_1/denial_code_ranking.csv`
- `artifacts/tasks/stub_003/reflection_only/T4/attempt_1/denial_rates_by_segment.csv`
- `artifacts/tasks/stub_003/reflection_only/T4/attempt_1/denial_rate_by_segment.png`
- `artifacts/tasks/stub_003/reflection_only/T4/attempt_1/metrics.json`
- `artifacts/tasks/stub_003/reflection_only/T4/attempt_1/report.md`

## Method

- Seed: 42; plan sha256: `2d27d0d6af524d55bb07bb2d5d4a0e07b5cc08ba5cf17092c863873565072c42`.
- Components (canonical order): load_tables, denial_code_ranking, denial_rate_by_segment, write_report.
- `load_tables` params: `{}`
- `denial_code_ranking` params: `{'scope': 'all_claims', 'quantify_missing': 'overall'}`
- `denial_rate_by_segment` params: `{'segments': ['claim_type'], 'denominator': 'all_claims', 'min_group_size': 0}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
