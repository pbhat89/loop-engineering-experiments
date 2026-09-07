# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_005` / condition `self_refine`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
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

- Features (6 categorical, 9 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present, billed_amount, allowed_amount
- Identifier fields present: none; target-derived amount fields present: ['billed_amount', 'allowed_amount']

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 105

### models

- logistic_regression: ROC-AUC: 0.996586
- logistic_regression: PR-AUC (average precision): 0.919575
- logistic_regression: precision at top 5% (k=161) of test rows: 0.832298
- logistic_regression: recall at top 5% (k=161) of test rows: 0.893333
- random_forest: ROC-AUC: 0.997229
- random_forest: PR-AUC (average precision): 0.923895
- random_forest: precision at top 5% (k=161) of test rows: 0.857143
- random_forest: recall at top 5% (k=161) of test rows: 0.920000

## Artifacts

- `artifacts/tasks/run_005/self_refine/T7/attempt_1/threshold.json`
- `artifacts/tasks/run_005/self_refine/T7/attempt_1/feature_list.json`
- `artifacts/tasks/run_005/self_refine/T7/attempt_1/model_metrics.json`
- `artifacts/tasks/run_005/self_refine/T7/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_005/self_refine/T7/attempt_1/metrics.json`
- `artifacts/tasks/run_005/self_refine/T7/attempt_1/report.md`

## Caveats

- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `830e2f4cf9f05c1c2ade54915646ab60af1e41a0470912d0666a3bce59d6a486`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'all_data'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present', 'billed_amount', 'allowed_amount']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['association_not_causation', 'class_imbalance', 'model_limitations'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['association_not_causation', 'class_imbalance', 'model_limitations'].
