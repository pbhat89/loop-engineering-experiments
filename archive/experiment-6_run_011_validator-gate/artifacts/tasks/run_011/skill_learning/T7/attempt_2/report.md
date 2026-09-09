# T7 — High-cost claim identification

## Summary

Task T7 (High-cost claim identification) for run `run_011` / condition `skill_learning`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### split

- Plain random split test_size=0.25, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]

### target_definition

- Threshold = p95 of paid_amount on train_only rows: 3198.988000 [source: artifacts/tasks/run_011/skill_learning/T7/attempt_2/threshold.json]
- Positive rate in train: 0.050036 [source: metrics.json#target_definition.positive_rate_train]
- Positive rate in test: 0.046700 [source: metrics.json#target_definition.positive_rate_test]

### feature_set

- Features (4 categorical, 2 numeric): claim_type, cpt_category, place_of_service, provider_specialty, service_units, length_of_stay [source: artifacts/tasks/run_011/skill_learning/T7/attempt_2/feature_list.json]
- Identifier fields present: none; target-derived amount fields present: none [source: metrics.json#feature_set]

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 46 [source: metrics.json#preprocessing]

### models

- logistic_regression: ROC-AUC: 0.887925 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.193382 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: precision at top 5% (k=161) of test rows: 0.192547 [source: artifacts/tasks/run_011/skill_learning/T7/attempt_2/model_metrics.json]
- logistic_regression: recall at top 5% (k=161) of test rows: 0.206667 [source: artifacts/tasks/run_011/skill_learning/T7/attempt_2/model_metrics.json]
- gradient_boosting: ROC-AUC: 0.883242 [source: metrics.json#models.gradient_boosting.roc_auc]
- gradient_boosting: PR-AUC (average precision): 0.206725 [source: metrics.json#models.gradient_boosting.pr_auc]
- gradient_boosting: precision at top 5% (k=161) of test rows: 0.198758 [source: artifacts/tasks/run_011/skill_learning/T7/attempt_2/model_metrics.json]
- gradient_boosting: recall at top 5% (k=161) of test rows: 0.213333 [source: artifacts/tasks/run_011/skill_learning/T7/attempt_2/model_metrics.json]

## Artifacts

- `artifacts/tasks/run_011/skill_learning/T7/attempt_2/threshold.json`
- `artifacts/tasks/run_011/skill_learning/T7/attempt_2/feature_list.json`
- `artifacts/tasks/run_011/skill_learning/T7/attempt_2/model_metrics.json`
- `artifacts/tasks/run_011/skill_learning/T7/attempt_2/precision_at_k.png`
- `artifacts/tasks/run_011/skill_learning/T7/attempt_2/metrics.json`
- `artifacts/tasks/run_011/skill_learning/T7/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `bc54b73aa7524a7ef48ca7a0e3221c4d7133f70b815cdcf6bec1d4335a2131bd`.
- Components (canonical order): load_tables, split, target_definition, feature_set, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `split` params: `{'test_size': 0.25}`
- `target_definition` params: `{'amount_column': 'paid_amount', 'percentile': 95, 'threshold_source': 'train_only'}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'service_units', 'length_of_stay']}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'gradient_boosting']}`
- `write_report` params: `{'caveats': ['synthetic_data', 'model_limitations', 'no_operational_use'], 'show_denominators': False, 'cite_artifacts': True}`
- Report options: show_denominators=False, cite_artifacts=True, caveats=['synthetic_data', 'model_limitations', 'no_operational_use'].
