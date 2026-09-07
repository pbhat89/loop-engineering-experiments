# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_004` / condition `baseline`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### feature_set

- Features (2 categorical, 2 numeric): claim_type, billed_amount, paid_amount, fraud_pattern_type
- Identifier fields present: none; label-derived fields present: ['fraud_pattern_type']

### split

- test_size=0.25, stratify=False, seed=42: train / test rows = 9633 / 3212
- Prevalence in train: 0.050244
- Prevalence in test: 0.050747

### preprocessing

- fit_on=all_data, scaling=none; features after encoding: 11

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 1.0000 / 1.0000 / 1.0000
- logistic_regression: ROC-AUC: 1.000000
- logistic_regression: PR-AUC (average precision): 1.000000
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[3049, 0], [0, 163]] on n_test=3212

## Artifacts

- `artifacts/tasks/run_004/baseline/T6/attempt_1/feature_list.json`
- `artifacts/tasks/run_004/baseline/T6/attempt_1/model_metrics.json`
- `artifacts/tasks/run_004/baseline/T6/attempt_1/confusion_matrices.png`
- `artifacts/tasks/run_004/baseline/T6/attempt_1/pr_curves.png`
- `artifacts/tasks/run_004/baseline/T6/attempt_1/metrics.json`
- `artifacts/tasks/run_004/baseline/T6/attempt_1/report.md`

## Method

- Seed: 42; plan sha256: `a088c92ef92a045db28eb4f689d3c25986934d9f938a70275fce8deb863f8058`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'billed_amount', 'paid_amount', 'fraud_pattern_type']}`
- `split` params: `{'test_size': 0.25, 'stratify': False}`
- `preprocessing` params: `{'fit_on': 'all_data', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression'], 'class_weight': 'none'}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
