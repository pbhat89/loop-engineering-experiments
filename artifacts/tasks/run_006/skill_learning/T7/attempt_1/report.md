# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_006` / condition `skill_learning`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
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

- fit_on=all_data, scaling=standard; features after encoding: 105

### models

- logistic_regression: ROC-AUC: 0.996597
- logistic_regression: PR-AUC (average precision): 0.919520
- logistic_regression: precision at top 5% (k=161) of test rows: 0.838509
- logistic_regression: recall at top 5% (k=161) of test rows: 0.900000
- random_forest: ROC-AUC: 0.997229
- random_forest: PR-AUC (average precision): 0.923895
- random_forest: precision at top 5% (k=161) of test rows: 0.857143
- random_forest: recall at top 5% (k=161) of test rows: 0.920000

## Artifacts

- `artifacts/tasks/run_006/skill_learning/T7/attempt_1/threshold.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_1/feature_list.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_1/model_metrics.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_1/metrics.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `937969aa7877d59af66d625a65c40d6ea542e0d2719e7f51393d93e346262ff5`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'all_data'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present', 'billed_amount', 'allowed_amount']}`
- `preprocessing` params: `{'fit_on': 'all_data', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['synthetic_data'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data'].
