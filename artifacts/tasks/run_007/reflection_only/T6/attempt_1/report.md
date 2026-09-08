# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_007` / condition `reflection_only`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### feature_set

- Features (5 categorical, 7 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, billed_amount, allowed_amount, paid_amount, service_units, er_flag, high_cost_flag, auth_required_flag
- Identifier fields present: none; label-derived fields present: none

### split

- test_size=0.25, stratify=True, seed=42: train / test rows = 9633 / 3212
- Prevalence in train: 0.050348
- Prevalence in test: 0.050436

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 53

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0490 / 0.4321 / 0.0879
- logistic_regression: ROC-AUC: 0.494013
- logistic_regression: PR-AUC (average precision): 0.052675
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[1690, 1360], [92, 70]] on n_test=3212
- random_forest: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000
- random_forest: ROC-AUC: 0.493596
- random_forest: PR-AUC (average precision): 0.048826
- random_forest: confusion matrix [[tn, fp], [fn, tp]] = [[3027, 23], [162, 0]] on n_test=3212

## Artifacts

- `artifacts/tasks/run_007/reflection_only/T6/attempt_1/feature_list.json`
- `artifacts/tasks/run_007/reflection_only/T6/attempt_1/model_metrics.json`
- `artifacts/tasks/run_007/reflection_only/T6/attempt_1/confusion_matrices.png`
- `artifacts/tasks/run_007/reflection_only/T6/attempt_1/pr_curves.png`
- `artifacts/tasks/run_007/reflection_only/T6/attempt_1/metrics.json`
- `artifacts/tasks/run_007/reflection_only/T6/attempt_1/report.md`

## Caveats

- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `0b0306b81878c8b1f41f95424ae3566098ea1aa502da1adb33c329b5698ad0db`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'er_flag', 'high_cost_flag', 'auth_required_flag']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest'], 'class_weight': 'balanced'}`
- `write_report` params: `{'caveats': ['class_imbalance', 'model_limitations'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['class_imbalance', 'model_limitations'].
