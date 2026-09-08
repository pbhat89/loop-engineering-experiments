# T5 — Fraud-pattern exploration

## Summary

Task T5 (Fraud-pattern exploration) for run `stub_005` / condition `feedback_memory`, attempt 1: status **ok**; 4 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), members (500 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns
- members: 500 rows, 44 columns

### class_prevalence

- Fraud prevalence: 0.050370
- Imbalance ratio (negatives per positive): 18.853168

### feature_comparison

- claim_type: most common value among flagged = Professional; share: 0.522411
- billed_amount mean (flagged / unflagged) = 1692.484529 / 1652.662020
- fraud_pattern_type: most common value among flagged = Upcoding; share: 0.298300

## Artifacts

- `artifacts/tasks/stub_005/feedback_memory/T5/attempt_1/fraud_prevalence.png`
- `artifacts/tasks/stub_005/feedback_memory/T5/attempt_1/fraud_comparison.csv`
- `artifacts/tasks/stub_005/feedback_memory/T5/attempt_1/metrics.json`
- `artifacts/tasks/stub_005/feedback_memory/T5/attempt_1/report.md`

## Method

- Seed: 42; plan sha256: `70baf9618abb1ca8322991971ac1ba7701f5f95128d19cee495c1276e6f0411a`.
- Components (canonical order): load_tables, class_prevalence, feature_comparison, write_report.
- `load_tables` params: `{}`
- `class_prevalence` params: `{}`
- `feature_comparison` params: `{'features': ['claim_type', 'billed_amount', 'fraud_pattern_type']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
