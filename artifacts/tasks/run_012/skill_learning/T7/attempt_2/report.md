# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_012` / condition `skill_learning`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]

### target_definition

- Threshold = p95 of paid_amount on train_only rows: 3198.988000 [source: artifacts/tasks/run_012/skill_learning/T7/attempt_2/threshold.json]
- Positive rate in train: 482 / 9633 = 0.050036 [source: metrics.json#target_definition.positive_rate_train]
- Positive rate in test: 150 / 3212 = 0.046700 [source: metrics.json#target_definition.positive_rate_test]

### feature_set

- Features (6 categorical, 7 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present [source: artifacts/tasks/run_012/skill_learning/T7/attempt_2/feature_list.json]
- Identifier fields present: none; target-derived amount fields present: none [source: metrics.json#feature_set]

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 103 [source: metrics.json#preprocessing]

### models

- logistic_regression: ROC-AUC: 0.906023 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.221486 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: precision at top 5% (k=161) of test rows: 0.229814 [source: artifacts/tasks/run_012/skill_learning/T7/attempt_2/model_metrics.json]
- logistic_regression: recall at top 5% (k=161) of test rows: 0.246667 [source: artifacts/tasks/run_012/skill_learning/T7/attempt_2/model_metrics.json]
- random_forest: ROC-AUC: 0.887457 [source: metrics.json#models.random_forest.roc_auc]
- random_forest: PR-AUC (average precision): 0.197256 [source: metrics.json#models.random_forest.pr_auc]
- random_forest: precision at top 5% (k=161) of test rows: 0.223602 [source: artifacts/tasks/run_012/skill_learning/T7/attempt_2/model_metrics.json]
- random_forest: recall at top 5% (k=161) of test rows: 0.240000 [source: artifacts/tasks/run_012/skill_learning/T7/attempt_2/model_metrics.json]

## Artifacts

- `artifacts/tasks/run_012/skill_learning/T7/attempt_2/threshold.json`
- `artifacts/tasks/run_012/skill_learning/T7/attempt_2/feature_list.json`
- `artifacts/tasks/run_012/skill_learning/T7/attempt_2/model_metrics.json`
- `artifacts/tasks/run_012/skill_learning/T7/attempt_2/precision_at_k.png`
- `artifacts/tasks/run_012/skill_learning/T7/attempt_2/metrics.json`
- `artifacts/tasks/run_012/skill_learning/T7/attempt_2/report.md`

## Caveats

- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `316079c12db1e12a12dca0933fb7d6ea0201d04c413abe718a7a2ba9c360f79e`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['model_limitations'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['model_limitations'].
