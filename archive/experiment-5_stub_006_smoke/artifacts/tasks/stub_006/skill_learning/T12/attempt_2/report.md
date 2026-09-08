# T12 — High-cost model, wider net

## Summary

Task T12 (High-cost model, wider net) for run `stub_006` / condition `skill_learning`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212

### target_definition

- Threshold = p90 of paid_amount on train_only rows: 2074.346000
- Positive rate in train: 0.100073
- Positive rate in test: 0.091220

### feature_set

- Features (6 categorical, 7 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present
- Identifier fields present: none; target-derived amount fields present: none

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 103

### models

- logistic_regression: ROC-AUC: 0.917521
- logistic_regression: PR-AUC (average precision): 0.393770
- logistic_regression: precision at top 5% (k=161) of test rows: 0.416149
- logistic_regression: recall at top 5% (k=161) of test rows: 0.228669

## Artifacts

- `artifacts/tasks/stub_006/skill_learning/T12/attempt_2/threshold.json`
- `artifacts/tasks/stub_006/skill_learning/T12/attempt_2/feature_list.json`
- `artifacts/tasks/stub_006/skill_learning/T12/attempt_2/model_metrics.json`
- `artifacts/tasks/stub_006/skill_learning/T12/attempt_2/precision_at_k.png`
- `artifacts/tasks/stub_006/skill_learning/T12/attempt_2/metrics.json`
- `artifacts/tasks/stub_006/skill_learning/T12/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `ccda3e2691c2600107c4c2eeab6fcd781146d23fea049eb1a22bb8d6b43544d9`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 90, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
