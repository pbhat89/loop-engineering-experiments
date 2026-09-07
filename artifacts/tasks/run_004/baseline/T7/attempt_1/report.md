# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_004` / condition `baseline`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212

### target_definition

- Threshold = p95 of paid_amount on all_data rows: 3161.934000
- Positive rate in train: 0.051178
- Positive rate in test: 0.046700

### feature_set

- Features (1 categorical, 2 numeric): claim_type, billed_amount, allowed_amount
- Identifier fields present: none; target-derived amount fields present: ['billed_amount', 'allowed_amount']

### preprocessing

- fit_on=all_data, scaling=none; features after encoding: 5

### models

- logistic_regression: ROC-AUC: 0.997287
- logistic_regression: PR-AUC (average precision): 0.928305
- logistic_regression: precision at top 5% (k=161) of test rows: 0.869565
- logistic_regression: recall at top 5% (k=161) of test rows: 0.933333

## Artifacts

- `artifacts/tasks/run_004/baseline/T7/attempt_1/threshold.json`
- `artifacts/tasks/run_004/baseline/T7/attempt_1/feature_list.json`
- `artifacts/tasks/run_004/baseline/T7/attempt_1/model_metrics.json`
- `artifacts/tasks/run_004/baseline/T7/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_004/baseline/T7/attempt_1/metrics.json`
- `artifacts/tasks/run_004/baseline/T7/attempt_1/report.md`

## Method

- Seed: 42; plan sha256: `0b4b871369515f88302d69978c4efff63fa12b4b74afe9ff0e28be318b529535`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'all_data'}`
- `feature_set` params: `{'features': ['claim_type', 'billed_amount', 'allowed_amount']}`
- `preprocessing` params: `{'fit_on': 'all_data', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
