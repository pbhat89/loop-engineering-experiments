# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `stub_003` / condition `reflection_only`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
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

- Features (6 categorical, 7 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present
- Identifier fields present: none; target-derived amount fields present: none

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 103

### models

- logistic_regression: ROC-AUC: 0.906023
- logistic_regression: PR-AUC (average precision): 0.221486
- logistic_regression: precision at top 5% (k=161) of test rows: 0.229814
- logistic_regression: recall at top 5% (k=161) of test rows: 0.246667

## Artifacts

- `artifacts/tasks/stub_003/reflection_only/T7/attempt_2/threshold.json`
- `artifacts/tasks/stub_003/reflection_only/T7/attempt_2/feature_list.json`
- `artifacts/tasks/stub_003/reflection_only/T7/attempt_2/model_metrics.json`
- `artifacts/tasks/stub_003/reflection_only/T7/attempt_2/precision_at_k.png`
- `artifacts/tasks/stub_003/reflection_only/T7/attempt_2/metrics.json`
- `artifacts/tasks/stub_003/reflection_only/T7/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `8355913a9f7a6833d1cad386694c8ac80d2ae810d5e9e599bb4c0a4ba7c1a2b4`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
