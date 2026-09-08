# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_007` / condition `feedback_memory`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### feature_set

- Features (6 categorical, 8 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, billed_amount, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present [source: artifacts/tasks/run_007/feedback_memory/T6/attempt_1/feature_list.json]
- Identifier fields present: none; label-derived fields present: none [source: metrics.json#feature_set]

### split

- test_size=0.25, stratify=True, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]
- Prevalence in train: 485 / 9633 = 0.050348 [source: metrics.json#split.prevalence_train]
- Prevalence in test: 162 / 3212 = 0.050436 [source: metrics.json#split.prevalence_test]

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 104 [source: metrics.json#preprocessing]

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0481 / 0.4136 / 0.0861 [source: artifacts/tasks/run_007/feedback_memory/T6/attempt_1/model_metrics.json]
- logistic_regression: ROC-AUC: 0.499081 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.049119 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[1723, 1327], [95, 67]] on n_test=3212 [source: artifacts/tasks/run_007/feedback_memory/T6/attempt_1/confusion_matrices.png]
- random_forest: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000 [source: artifacts/tasks/run_007/feedback_memory/T6/attempt_1/model_metrics.json]
- random_forest: ROC-AUC: 0.480383 [source: metrics.json#models.random_forest.roc_auc]
- random_forest: PR-AUC (average precision): 0.049313 [source: metrics.json#models.random_forest.pr_auc]
- random_forest: confusion matrix [[tn, fp], [fn, tp]] = [[3032, 18], [162, 0]] on n_test=3212 [source: artifacts/tasks/run_007/feedback_memory/T6/attempt_1/confusion_matrices.png]

## Artifacts

- `artifacts/tasks/run_007/feedback_memory/T6/attempt_1/feature_list.json`
- `artifacts/tasks/run_007/feedback_memory/T6/attempt_1/model_metrics.json`
- `artifacts/tasks/run_007/feedback_memory/T6/attempt_1/confusion_matrices.png`
- `artifacts/tasks/run_007/feedback_memory/T6/attempt_1/pr_curves.png`
- `artifacts/tasks/run_007/feedback_memory/T6/attempt_1/metrics.json`
- `artifacts/tasks/run_007/feedback_memory/T6/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.

## Method

- Seed: 42; plan sha256: `2440be62b9bed2b00d32456a840f465dbc3fa05c5078d6dedfa1dd90c2f8fe11`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest'], 'class_weight': 'balanced'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'no_operational_use', 'class_imbalance'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'no_operational_use', 'class_imbalance'].
