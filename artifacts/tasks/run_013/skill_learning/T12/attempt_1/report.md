# T12 — High-cost model, wider net

## Summary

Task T12 (High-cost model, wider net) for run `run_013` / condition `skill_learning`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]

### target_definition

- Threshold = p90 of paid_amount on train_only rows: 2074.346000 [source: artifacts/tasks/run_013/skill_learning/T12/attempt_1/threshold.json]
- Positive rate in train: 0.100073 [source: metrics.json#target_definition.positive_rate_train]
- Positive rate in test: 0.091220 [source: metrics.json#target_definition.positive_rate_test]

### feature_set

- Features (6 categorical, 9 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present, billed_amount, allowed_amount [source: artifacts/tasks/run_013/skill_learning/T12/attempt_1/feature_list.json]
- Identifier fields present: none; target-derived amount fields present: ['billed_amount', 'allowed_amount'] [source: metrics.json#feature_set]

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 105 [source: metrics.json#preprocessing]

### models

- logistic_regression: ROC-AUC: 0.993188 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.913833 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: precision at top 5% (k=161) of test rows: 0.931677 [source: artifacts/tasks/run_013/skill_learning/T12/attempt_1/model_metrics.json]
- logistic_regression: recall at top 5% (k=161) of test rows: 0.511945 [source: artifacts/tasks/run_013/skill_learning/T12/attempt_1/model_metrics.json]
- random_forest: ROC-AUC: 0.994313 [source: metrics.json#models.random_forest.roc_auc]
- random_forest: PR-AUC (average precision): 0.912755 [source: metrics.json#models.random_forest.pr_auc]
- random_forest: precision at top 5% (k=161) of test rows: 0.913043 [source: artifacts/tasks/run_013/skill_learning/T12/attempt_1/model_metrics.json]
- random_forest: recall at top 5% (k=161) of test rows: 0.501706 [source: artifacts/tasks/run_013/skill_learning/T12/attempt_1/model_metrics.json]

## Artifacts

- `artifacts/tasks/run_013/skill_learning/T12/attempt_1/threshold.json`
- `artifacts/tasks/run_013/skill_learning/T12/attempt_1/feature_list.json`
- `artifacts/tasks/run_013/skill_learning/T12/attempt_1/model_metrics.json`
- `artifacts/tasks/run_013/skill_learning/T12/attempt_1/precision_at_k.png`
- `artifacts/tasks/run_013/skill_learning/T12/attempt_1/metrics.json`
- `artifacts/tasks/run_013/skill_learning/T12/attempt_1/report.md`

## Caveats

- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `a6c5a342d1ec07249475a1ed2a67af0ed9c29d268cfa358d82472fff173e2600`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 90, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present', 'billed_amount', 'allowed_amount']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest']}`
- `write_report` params: `{'caveats': ['no_operational_use'], 'show_denominators': False, 'cite_artifacts': True}`
- Report options: show_denominators=False, cite_artifacts=True, caveats=['no_operational_use'].
