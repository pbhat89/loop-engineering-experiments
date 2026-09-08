# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `stub_005` / condition `feedback_memory`, attempt 3: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### feature_set

- Features (6 categorical, 10 numeric): claim_type, cpt_category, place_of_service, provider_specialty, network_status, billed_amount, allowed_amount, paid_amount, service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present
- Identifier fields present: none; label-derived fields present: none

### split

- test_size=0.25, stratify=True, seed=42: train / test rows = 9633 / 3212
- Prevalence in train: 0.050348
- Prevalence in test: 0.050436

### preprocessing

- fit_on=train_only, scaling=none; features after encoding: 106

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000
- logistic_regression: ROC-AUC: 0.497990
- logistic_regression: PR-AUC (average precision): 0.051919
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[3050, 0], [162, 0]] on n_test=3212
- random_forest: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000
- random_forest: ROC-AUC: 0.491846
- random_forest: PR-AUC (average precision): 0.050792
- random_forest: confusion matrix [[tn, fp], [fn, tp]] = [[3050, 0], [162, 0]] on n_test=3212

## Artifacts

- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_3/feature_list.json`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_3/model_metrics.json`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_3/confusion_matrices.png`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_3/pr_curves.png`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_3/metrics.json`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_3/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **model_limitations**: The models are untuned baselines fitted on a single random split; performance is not validated out of time or out of sample.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `e5c661a91a045b234c29862dd3ea46bcedf9fa32a8d419545b8bfcba6420bf26`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression', 'random_forest'], 'class_weight': 'none'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data', 'class_imbalance', 'model_limitations', 'no_operational_use'].
