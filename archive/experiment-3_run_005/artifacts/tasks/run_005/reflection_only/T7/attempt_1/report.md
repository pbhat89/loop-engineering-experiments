# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_005` / condition `reflection_only`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]

### target_definition

- Threshold = p95 of paid_amount on train_only rows: 3198.988000 [source: artifacts/tasks/run_005/reflection_only/T7/attempt_1/threshold.json]
- Positive rate in train: 482 / 9633 = 0.050036 [source: metrics.json#target_definition.positive_rate_train]
- Positive rate in test: 150 / 3212 = 0.046700 [source: metrics.json#target_definition.positive_rate_test]

### feature_set

- Features (6 categorical, 9 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present, billed_amount, allowed_amount [source: artifacts/tasks/run_005/reflection_only/T7/attempt_1/feature_list.json]
- Identifier fields present: none; target-derived amount fields present: ['billed_amount', 'allowed_amount'] [source: metrics.json#feature_set]

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 105 [source: metrics.json#preprocessing]

### models

- logistic_regression: ROC-AUC: 0.996695 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.921166 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: precision at top 5% (k=161) of test rows: 0.832298 [source: artifacts/tasks/run_005/reflection_only/T7/attempt_1/model_metrics.json]
- logistic_regression: recall at top 5% (k=161) of test rows: 0.893333 [source: artifacts/tasks/run_005/reflection_only/T7/attempt_1/model_metrics.json]
- random_forest: ROC-AUC: 0.997245 [source: metrics.json#models.random_forest.roc_auc]
- random_forest: PR-AUC (average precision): 0.922546 [source: metrics.json#models.random_forest.pr_auc]
- random_forest: precision at top 5% (k=161) of test rows: 0.857143 [source: artifacts/tasks/run_005/reflection_only/T7/attempt_1/model_metrics.json]
- random_forest: recall at top 5% (k=161) of test rows: 0.920000 [source: artifacts/tasks/run_005/reflection_only/T7/attempt_1/model_metrics.json]

## Artifacts

- `artifacts/tasks/run_005/reflection_only/T7/attempt_1/threshold.json`
- `artifacts/tasks/run_005/reflection_only/T7/attempt_1/feature_list.json`
- `artifacts/tasks/run_005/reflection_only/T7/attempt_1/model_metrics.json`
- `artifacts/tasks/run_005/reflection_only/T7/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_005/reflection_only/T7/attempt_1/metrics.json`
- `artifacts/tasks/run_005/reflection_only/T7/attempt_1/report.md`

## Caveats

- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.

## Method

- Seed: 42; plan sha256: `177bb41923695294746a373c5349b30a9da2676c600d824e85cce2f78fa5cae7`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present', 'billed_amount', 'allowed_amount']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['small_groups', 'class_imbalance'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['small_groups', 'class_imbalance'].
