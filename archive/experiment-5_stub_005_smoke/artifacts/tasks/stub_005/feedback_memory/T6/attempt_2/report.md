# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `stub_005` / condition `feedback_memory`, attempt 2: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
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

## Artifacts

- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_2/feature_list.json`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_2/model_metrics.json`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_2/confusion_matrices.png`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_2/pr_curves.png`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_2/metrics.json`
- `artifacts/tasks/stub_005/feedback_memory/T6/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `6264dbbdbb5101aa7007cb9f25d45bf98655fd9bffd03bad684da5ff7b4d34f3`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'elective_flag', 'preventive_flag', 'auth_required_flag', 'primary_icd10_cm', 'drg_present']}`
- `split` params: `{'test_size': 0.25, 'stratify': True}`
- `preprocessing` params: `{'fit_on': 'train_only', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression'], 'class_weight': 'none'}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
