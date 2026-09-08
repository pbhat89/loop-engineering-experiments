# T5 — Fraud-pattern exploration

## Summary

Task T5 (Fraud-pattern exploration) for run `stub_005` / condition `reflection_only`, attempt 2: status **ok**; 5 component(s) executed, 0 failed, 0 error(s) recorded.
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
- cpt_category: most common value among flagged = E&M; share: 0.287481
- place_of_service: most common value among flagged = 22; share: 0.432767
- provider_specialty: most common value among flagged = Critical Access Hospital; share: 0.083462
- network_status: most common value among flagged = In-Network; share: 0.839258
- billed_amount mean (flagged / unflagged) = 1692.484529 / 1652.662020
- allowed_amount mean (flagged / unflagged) = 994.537975 / 945.380995
- paid_amount mean (flagged / unflagged) = 832.084420 / 757.915818
- service_units mean (flagged / unflagged) = 1.987635 / 2.005493
- length_of_stay mean (flagged / unflagged) = 0.712519 / 0.750041
- er_flag: most common value among flagged = 0; share: 0.967543
- auth_required_flag: most common value among flagged = 0; share: 0.828439

### leakage_assessment

- Label-derived: ['fraud_pattern_type']; protected: ['member_sex', 'member_race_ethnicity', 'member_age_band', 'member_income_band']; flagged features in this plan: none
- Plan features that are label-derived, protected or identifiers: 0

## Artifacts

- `artifacts/tasks/stub_005/reflection_only/T5/attempt_2/fraud_prevalence.png`
- `artifacts/tasks/stub_005/reflection_only/T5/attempt_2/fraud_comparison.csv`
- `artifacts/tasks/stub_005/reflection_only/T5/attempt_2/metrics.json`
- `artifacts/tasks/stub_005/reflection_only/T5/attempt_2/report.md`

## Method

- Seed: 42; plan sha256: `201cb6a5d57ff8d164d72dba5caf99e3a458a5778f618defa02b0831166bab57`.
- Components (canonical order): load_tables, class_prevalence, feature_comparison, leakage_assessment, write_report.
- `load_tables` params: `{}`
- `class_prevalence` params: `{}`
- `feature_comparison` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'auth_required_flag']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- `leakage_assessment` params: `{}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
