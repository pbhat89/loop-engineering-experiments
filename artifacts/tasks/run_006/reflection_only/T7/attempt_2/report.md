# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_006` / condition `reflection_only`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212

### target_definition

- Threshold = p95 of paid_amount on train_only rows: 3198.988000
- Positive rate in train: 0.050036
- Positive rate in test: 0.046700

### feature_set

- Features (6 categorical, 6 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm
- Identifier fields present: none; target-derived amount fields present: none

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 102

### models

- logistic_regression: ROC-AUC: 0.906130
- logistic_regression: PR-AUC (average precision): 0.221920
- logistic_regression: precision at top 5% (k=161) of test rows: 0.236025
- logistic_regression: recall at top 5% (k=161) of test rows: 0.253333
- random_forest: ROC-AUC: 0.892137
- random_forest: PR-AUC (average precision): 0.204438
- random_forest: precision at top 5% (k=161) of test rows: 0.217391
- random_forest: recall at top 5% (k=161) of test rows: 0.233333

## Artifacts

- `artifacts/tasks/run_006/reflection_only/T7/attempt_2/threshold.json`
- `artifacts/tasks/run_006/reflection_only/T7/attempt_2/feature_list.json`
- `artifacts/tasks/run_006/reflection_only/T7/attempt_2/model_metrics.json`
- `artifacts/tasks/run_006/reflection_only/T7/attempt_2/precision_at_k.png`
- `artifacts/tasks/run_006/reflection_only/T7/attempt_2/metrics.json`
- `artifacts/tasks/run_006/reflection_only/T7/attempt_2/report.md`

## Caveats

- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `a00b8981531a9aacf72bc513127405693a173b4c6d687a8bd8ebb0e6ebea1fc2`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['model_limitations'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['model_limitations'].
