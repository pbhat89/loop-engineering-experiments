# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_001` / condition `baseline`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]

### target_definition

- Threshold = p95 of paid_amount on train_only rows: 3198.988000 [source: artifacts/tasks/run_001/baseline/T7/attempt_1/threshold.json]
- Positive rate in train: 482 / 9633 = 0.050036 [source: metrics.json#target_definition.positive_rate_train]
- Positive rate in test: 150 / 3212 = 0.046700 [source: metrics.json#target_definition.positive_rate_test]

### feature_set

- Features (6 categorical, 7 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present [source: artifacts/tasks/run_001/baseline/T7/attempt_1/feature_list.json]
- Identifier fields present: none; target-derived amount fields present: none [source: metrics.json#feature_set]

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 103 [source: metrics.json#preprocessing]

### models

- logistic_regression: ROC-AUC: 0.906045 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.223296 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: precision at top 5% (k=161) of test rows: 0.229814 [source: artifacts/tasks/run_001/baseline/T7/attempt_1/model_metrics.json]
- logistic_regression: recall at top 5% (k=161) of test rows: 0.246667 [source: artifacts/tasks/run_001/baseline/T7/attempt_1/model_metrics.json]
- gradient_boosting: ROC-AUC: 0.902542 [source: metrics.json#models.gradient_boosting.roc_auc]
- gradient_boosting: PR-AUC (average precision): 0.217373 [source: metrics.json#models.gradient_boosting.pr_auc]
- gradient_boosting: precision at top 5% (k=161) of test rows: 0.217391 [source: artifacts/tasks/run_001/baseline/T7/attempt_1/model_metrics.json]
- gradient_boosting: recall at top 5% (k=161) of test rows: 0.233333 [source: artifacts/tasks/run_001/baseline/T7/attempt_1/model_metrics.json]

## Artifacts

- `artifacts/tasks/run_001/baseline/T7/attempt_1/threshold.json`
- `artifacts/tasks/run_001/baseline/T7/attempt_1/feature_list.json`
- `artifacts/tasks/run_001/baseline/T7/attempt_1/model_metrics.json`
- `artifacts/tasks/run_001/baseline/T7/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_001/baseline/T7/attempt_1/metrics.json`
- `artifacts/tasks/run_001/baseline/T7/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `4aa0284bfc8ac8f59898206c9e3883d7f0548a5d73f510d93486e4f9a58fad64`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'gradient_boosting']}`
- `write_report` params: `{'caveats': ['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'].
