# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_003` / condition `skill_learning`, attempt 2: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### feature_set

- Features (5 categorical, 7 numeric): claim_type, billed_amount, paid_amount, cpt_category, place_of_service, provider_specialty, network_status, allowed_amount, service_units, length_of_stay, er_flag, auth_required_flag
- Identifier fields present: none; label-derived fields present: none

### split

- test_size=0.25, stratify=True, seed=42: train / test rows = 9633 / 3212
- Prevalence in train: 485 / 9633 = 0.050348
- Prevalence in test: 162 / 3212 = 0.050436

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 53

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000
- logistic_regression: ROC-AUC: 0.502095
- logistic_regression: PR-AUC (average precision): 0.058046
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[3050, 0], [162, 0]] on n_test=3212
- random_forest: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000
- random_forest: ROC-AUC: 0.474016
- random_forest: PR-AUC (average precision): 0.047737
- random_forest: confusion matrix [[tn, fp], [fn, tp]] = [[3049, 1], [162, 0]] on n_test=3212

## Artifacts

- `artifacts/tasks/run_003/skill_learning/T6/attempt_2/feature_list.json`
- `artifacts/tasks/run_003/skill_learning/T6/attempt_2/model_metrics.json`
- `artifacts/tasks/run_003/skill_learning/T6/attempt_2/confusion_matrices.png`
- `artifacts/tasks/run_003/skill_learning/T6/attempt_2/pr_curves.png`
- `artifacts/tasks/run_003/skill_learning/T6/attempt_2/metrics.json`
- `artifacts/tasks/run_003/skill_learning/T6/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `9a917be69d8f19091e0e6058163b77ea0bfb517472c147ecdac5fc4a766d132e`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'billed_amount', 'paid_amount', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'allowed_amount', 'service_units', 'length_of_stay', 'er_flag', 'auth_required_flag']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest'], 'class_weight': 'none'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'].
