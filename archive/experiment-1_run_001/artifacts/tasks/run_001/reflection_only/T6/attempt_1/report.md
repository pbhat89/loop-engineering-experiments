# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_001` / condition `reflection_only`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### feature_set

- Features (6 categorical, 11 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, billed_amount, allowed_amount, paid_amount, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present, high_cost_flag [source: artifacts/tasks/run_001/reflection_only/T6/attempt_1/feature_list.json]
- Identifier fields present: none; label-derived fields present: none [source: metrics.json#feature_set]

### split

- test_size=0.25, stratify=True, seed=42: train / test rows = 9633 / 3212 [source: metrics.json#split]
- Prevalence in train: 485 / 9633 = 0.050348 [source: metrics.json#split.prevalence_train]
- Prevalence in test: 162 / 3212 = 0.050436 [source: metrics.json#split.prevalence_test]

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 107 [source: metrics.json#preprocessing]

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0481 / 0.4074 / 0.0860 [source: artifacts/tasks/run_001/reflection_only/T6/attempt_1/model_metrics.json]
- logistic_regression: ROC-AUC: 0.498832 [source: metrics.json#models.logistic_regression.roc_auc]
- logistic_regression: PR-AUC (average precision): 0.052135 [source: metrics.json#models.logistic_regression.pr_auc]
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[1743, 1307], [96, 66]] on n_test=3212 [source: artifacts/tasks/run_001/reflection_only/T6/attempt_1/confusion_matrices.png]
- random_forest: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000 [source: artifacts/tasks/run_001/reflection_only/T6/attempt_1/model_metrics.json]
- random_forest: ROC-AUC: 0.498478 [source: metrics.json#models.random_forest.roc_auc]
- random_forest: PR-AUC (average precision): 0.050952 [source: metrics.json#models.random_forest.pr_auc]
- random_forest: confusion matrix [[tn, fp], [fn, tp]] = [[3046, 4], [162, 0]] on n_test=3212 [source: artifacts/tasks/run_001/reflection_only/T6/attempt_1/confusion_matrices.png]

## Artifacts

- `artifacts/tasks/run_001/reflection_only/T6/attempt_1/feature_list.json`
- `artifacts/tasks/run_001/reflection_only/T6/attempt_1/model_metrics.json`
- `artifacts/tasks/run_001/reflection_only/T6/attempt_1/confusion_matrices.png`
- `artifacts/tasks/run_001/reflection_only/T6/attempt_1/pr_curves.png`
- `artifacts/tasks/run_001/reflection_only/T6/attempt_1/metrics.json`
- `artifacts/tasks/run_001/reflection_only/T6/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `b86c1b641eb461a0f71e54e8b6858c0d451a5051de011c52da9ccae50b7c5ade`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present', 'high_cost_flag']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest'], 'class_weight': 'balanced'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'].
