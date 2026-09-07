# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_006` / condition `skill_learning`, attempt 3: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
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
- random_forest: ROC-AUC: 0.887324
- random_forest: PR-AUC (average precision): 0.197095
- random_forest: precision at top 5% (k=161) of test rows: 0.223602
- random_forest: recall at top 5% (k=161) of test rows: 0.240000

## Artifacts

- `artifacts/tasks/run_006/skill_learning/T7/attempt_3/threshold.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_3/feature_list.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_3/model_metrics.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_3/precision_at_k.png`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_3/metrics.json`
- `artifacts/tasks/run_006/skill_learning/T7/attempt_3/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `908ec6efff896d22d252d0a5f4a8f619d77a8436826042ebc9795e68905f44c0`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['synthetic_data', 'model_limitations', 'no_operational_use'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data', 'model_limitations', 'no_operational_use'].
