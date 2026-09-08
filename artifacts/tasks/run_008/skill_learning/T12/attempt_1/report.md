# T12 — High-cost model, wider net

## Summary

Task T12 (High-cost model, wider net) for run `run_008` / condition `skill_learning`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]

### target_definition

- Threshold = p90 of paid_amount on train_only rows: 2074.346000 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_1/threshold.json]
- Positive rate in train: 964 / 9633 = 0.100073 [source: metrics.json#target_definition.positive_rate_train]
- Positive rate in test: 293 / 3212 = 0.091220 [source: metrics.json#target_definition.positive_rate_test]

### feature_set

- Features (6 categorical, 9 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present, billed_amount, allowed_amount [source: artifacts/tasks/run_008/skill_learning/T12/attempt_1/feature_list.json]
- Identifier fields present: none; target-derived amount fields present: ['billed_amount', 'allowed_amount'] [source: metrics.json#feature_set]

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 105 [source: metrics.json#preprocessing]

### models

- logistic_regression: ROC-AUC: 0.993367 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.914579 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: precision at top 5% (k=161) of test rows: 0.931677 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_1/model_metrics.json]
- logistic_regression: recall at top 5% (k=161) of test rows: 0.511945 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_1/model_metrics.json]
- gradient_boosting: ROC-AUC: 0.994185 [source: metrics.json#models.gradient_boosting.roc_auc]
- gradient_boosting: PR-AUC (average precision): 0.925271 [source: metrics.json#models.gradient_boosting.pr_auc]
- gradient_boosting: precision at top 5% (k=161) of test rows: 0.919255 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_1/model_metrics.json]
- gradient_boosting: recall at top 5% (k=161) of test rows: 0.505119 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_1/model_metrics.json]

## Artifacts

- `artifacts/tasks/run_008/skill_learning/T12/attempt_1/threshold.json`
- `artifacts/tasks/run_008/skill_learning/T12/attempt_1/feature_list.json`
- `artifacts/tasks/run_008/skill_learning/T12/attempt_1/model_metrics.json`
- `artifacts/tasks/run_008/skill_learning/T12/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_008/skill_learning/T12/attempt_1/metrics.json`
- `artifacts/tasks/run_008/skill_learning/T12/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `49a8242c41dfd64a16afbd97e7382de1472339fb3aae0940fbc524443bc78de3`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 90, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present', 'billed_amount', 'allowed_amount']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression', 'gradient_boosting']}`
- `write_report` params: `{'caveats': ['synthetic_data'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data'].
