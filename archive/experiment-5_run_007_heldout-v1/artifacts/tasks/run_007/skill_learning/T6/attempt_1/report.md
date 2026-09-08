# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_007` / condition `skill_learning`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### feature_set

- Features (4 categorical, 10 numeric): claim_type, place_of_service, provider_specialty, network_status, billed_amount, allowed_amount, paid_amount, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, high_cost_flag
- Identifier fields present: none; label-derived fields present: none

### split

- test_size=0.25, stratify=True, seed=42: train / test rows = 9633 / 3212
- Prevalence in train: 0.050348
- Prevalence in test: 0.050436

### preprocessing

- fit_on=train_only, scaling=standard; features after encoding: 51

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0467 / 0.4259 / 0.0841
- logistic_regression: ROC-AUC: 0.484198
- logistic_regression: PR-AUC (average precision): 0.051186
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[1640, 1410], [93, 69]] on n_test=3212
- random_forest: precision / recall / f1 at threshold 0.5 = 0.0435 / 0.0062 / 0.0108
- random_forest: ROC-AUC: 0.513539
- random_forest: PR-AUC (average precision): 0.051308
- random_forest: confusion matrix [[tn, fp], [fn, tp]] = [[3028, 22], [161, 1]] on n_test=3212

## Artifacts

- `artifacts/tasks/run_007/skill_learning/T6/attempt_1/feature_list.json`
- `artifacts/tasks/run_007/skill_learning/T6/attempt_1/model_metrics.json`
- `artifacts/tasks/run_007/skill_learning/T6/attempt_1/confusion_matrices.png`
- `artifacts/tasks/run_007/skill_learning/T6/attempt_1/pr_curves.png`
- `artifacts/tasks/run_007/skill_learning/T6/attempt_1/metrics.json`
- `artifacts/tasks/run_007/skill_learning/T6/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.

## Method

- Seed: 42; plan sha256: `596aacda0cb3bb3005ab53f713bbb143c7d34031c887a5906ae912d4a5850bd1`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'high_cost_flag']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'standard'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest'], 'class_weight': 'balanced'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'class_imbalance', 'model_limitations'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data', 'class_imbalance', 'model_limitations'].
