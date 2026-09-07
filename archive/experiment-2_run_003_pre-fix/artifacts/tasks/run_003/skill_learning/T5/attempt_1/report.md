# T5 — Fraud-pattern exploration

## Summary

Task T5 (Fraud-pattern exploration) for run `run_003` / condition `skill_learning`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), members (500 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- members: 500 rows, 44 columns

### class_prevalence

- Fraud prevalence: 647 / 12845 = 0.050370
- Imbalance ratio (negatives per positive): 18.853168

### feature_comparison

- claim_type: most common value among flagged = Professional; share: 0.522411
- billed_amount mean (flagged / unflagged) = 1692.484529 / 1652.662020
- fraud_pattern_type: most common value among flagged = Upcoding; share: 0.298300

## Artifacts

- `artifacts/tasks/run_003/skill_learning/T5/attempt_1/fraud_prevalence.png`
- `artifacts/tasks/run_003/skill_learning/T5/attempt_1/fraud_comparison.csv`
- `artifacts/tasks/run_003/skill_learning/T5/attempt_1/metrics.json`
- `artifacts/tasks/run_003/skill_learning/T5/attempt_1/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.

## Method

- Seed: 42; plan sha256: `12a0f149da5ef48b6b5e9115ce3341e9af9542b699946462a69c579b718f447c`.
- Components (canonical order): load_tables, class_prevalence, feature_comparison, write_report.
- `load_tables` params: `{}`
- `class_prevalence` params: `{}`
- `feature_comparison` params: `{'features': ['claim_type', 'billed_amount', 'fraud_pattern_type']}`
- `write_report` params: `{'caveats': ['descriptive_only', 'synthetic_data', 'sample_preview', 'small_groups', 'association_not_causation'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['descriptive_only', 'synthetic_data', 'sample_preview', 'small_groups', 'association_not_causation'].
