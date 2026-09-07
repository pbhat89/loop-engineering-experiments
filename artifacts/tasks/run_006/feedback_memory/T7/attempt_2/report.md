# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_006` / condition `feedback_memory`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
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

- fit_on=train_only, scaling=standard; features after encoding: 103

### models

- logistic_regression: ROC-AUC: 0.906045
- logistic_regression: PR-AUC (average precision): 0.223296
- logistic_regression: precision at top 5% (k=161) of test rows: 0.229814
- logistic_regression: recall at top 5% (k=161) of test rows: 0.246667
- gradient_boosting: ROC-AUC: 0.902542
- gradient_boosting: PR-AUC (average precision): 0.217373
- gradient_boosting: precision at top 5% (k=161) of test rows: 0.217391
- gradient_boosting: recall at top 5% (k=161) of test rows: 0.233333

## Artifacts

- `artifacts/tasks/run_006/feedback_memory/T7/attempt_2/threshold.json`
- `artifacts/tasks/run_006/feedback_memory/T7/attempt_2/feature_list.json`
- `artifacts/tasks/run_006/feedback_memory/T7/attempt_2/model_metrics.json`
- `artifacts/tasks/run_006/feedback_memory/T7/attempt_2/precision_at_k.png`
- `artifacts/tasks/run_006/feedback_memory/T7/attempt_2/metrics.json`
- `artifacts/tasks/run_006/feedback_memory/T7/attempt_2/report.md`

## Caveats

- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `0e0465b9ee01f65ee2923d6433c19ed38974b4027515bc9c5bea3a8f6f262406`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'gradient_boosting']}`
- `write_report` params: `{'caveats': ['class_imbalance', 'model_limitations', 'synthetic_data'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['class_imbalance', 'model_limitations', 'synthetic_data'].
