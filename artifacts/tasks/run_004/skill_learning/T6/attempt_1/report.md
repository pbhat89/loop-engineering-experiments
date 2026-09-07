# T6 — Baseline fraud model

## Summary

Task T6 (Baseline fraud model) for run `run_004` / condition `skill_learning`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### feature_set

- Features (5 categorical, 7 numeric): claim_type, billed_amount, paid_amount, cpt_category, place_of_service, provider_specialty, network_status, allowed_amount, service_units, length_of_stay, er_flag, auth_required_flag
- Identifier fields present: none; label-derived fields present: none

### split

- test_size=0.25, stratify=False, seed=42: train / test rows = 9633 / 3212
- Prevalence in train: 484 / 9633 = 0.050244
- Prevalence in test: 163 / 3212 = 0.050747

### preprocessing

- fit_on=all_data, scaling=none; features after encoding: 53

### models

- logistic_regression: precision / recall / f1 at threshold 0.5 = 0.0000 / 0.0000 / 0.0000
- logistic_regression: ROC-AUC: 0.500496
- logistic_regression: PR-AUC (average precision): 0.051396
- logistic_regression: confusion matrix [[tn, fp], [fn, tp]] = [[3049, 0], [163, 0]] on n_test=3212

## Artifacts

- `artifacts/tasks/run_004/skill_learning/T6/attempt_1/feature_list.json`
- `artifacts/tasks/run_004/skill_learning/T6/attempt_1/model_metrics.json`
- `artifacts/tasks/run_004/skill_learning/T6/attempt_1/confusion_matrices.png`
- `artifacts/tasks/run_004/skill_learning/T6/attempt_1/pr_curves.png`
- `artifacts/tasks/run_004/skill_learning/T6/attempt_1/metrics.json`
- `artifacts/tasks/run_004/skill_learning/T6/attempt_1/report.md`

## Caveats

- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.

## Method

- Seed: 42; plan sha256: `7e58eb4e3841f0fe75478763baf3ba6ab3e216e5b5577143ae79d2b548aa5914`.
- Components (canonical order): load_tables, feature_set, split, preprocessing, models, write_report.
- `load_tables` params: `{}`
- `feature_set` params: `{'features': ['claim_type', 'billed_amount', 'paid_amount', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'allowed_amount', 'service_units', 'length_of_stay', 'er_flag', 'auth_required_flag']}`
- `split` params: `{'test_size': 0.25, 'stratify': False}`
- `preprocessing` params: `{'fit_on': 'all_data', 'scaling': 'none'}`
- `models` params: `{'models': ['logistic_regression'], 'class_weight': 'none'}`
- `write_report` params: `{'caveats': ['class_imbalance', 'no_operational_use', 'small_groups', 'association_not_causation', 'descriptive_only', 'synthetic_data', 'sample_preview'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['class_imbalance', 'no_operational_use', 'small_groups', 'association_not_causation', 'descriptive_only', 'synthetic_data', 'sample_preview'].
