# T5 — Fraud-pattern exploration

## Summary

Task T5 (Fraud-pattern exploration) for run `run_007` / condition `reflection_only`, attempt 1: status **ok**; 5 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows), members (500 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]
- members: 500 rows, 44 columns [source: metrics.json#tables]

### class_prevalence

- Fraud prevalence: 647 / 12845 = 0.050370 [source: metrics.json#class_prevalence]
- Imbalance ratio (negatives per positive): 18.853168 [source: metrics.json#class_prevalence.imbalance_ratio]

### feature_comparison

- claim_type: most common value among flagged = Professional; share: 0.522411 [source: metrics.json#feature_comparison]
- cpt_category: most common value among flagged = E&M; share: 0.287481 [source: metrics.json#feature_comparison]
- place_of_service: most common value among flagged = 22; share: 0.432767 [source: metrics.json#feature_comparison]
- provider_specialty: most common value among flagged = Critical Access Hospital; share: 0.083462 [source: metrics.json#feature_comparison]
- network_status: most common value among flagged = In-Network; share: 0.839258 [source: metrics.json#feature_comparison]
- billed_amount mean (flagged / unflagged) = 1692.484529 / 1652.662020 [source: metrics.json#feature_comparison]
- allowed_amount mean (flagged / unflagged) = 994.537975 / 945.380995 [source: metrics.json#feature_comparison]
- paid_amount mean (flagged / unflagged) = 832.084420 / 757.915818 [source: metrics.json#feature_comparison]
- service_units mean (flagged / unflagged) = 1.987635 / 2.005493 [source: metrics.json#feature_comparison]
- length_of_stay mean (flagged / unflagged) = 0.712519 / 0.750041 [source: metrics.json#feature_comparison]
- er_flag: most common value among flagged = 0; share: 0.967543 [source: metrics.json#feature_comparison]
- auth_required_flag: most common value among flagged = 0; share: 0.828439 [source: metrics.json#feature_comparison]
- fraud_pattern_type: most common value among flagged = Upcoding; share: 0.298300 [source: metrics.json#feature_comparison]
- high_cost_flag: most common value among flagged = 0; share: 0.973725 [source: metrics.json#feature_comparison]
- member_age_band: most common value among flagged = 50-64; share: 0.313756 [source: metrics.json#feature_comparison]
- member_sex: most common value among flagged = F; share: 0.508501 [source: metrics.json#feature_comparison]
- member_race_ethnicity: most common value among flagged = White; share: 0.616692 [source: metrics.json#feature_comparison]
- member_payer_type: most common value among flagged = commercial; share: 0.489954 [source: metrics.json#feature_comparison]

### leakage_assessment

- Label-derived: ['fraud_pattern_type']; protected: ['member_sex', 'member_race_ethnicity', 'member_age_band', 'member_income_band']; flagged features in this plan: ['fraud_pattern_type', 'member_age_band', 'member_sex', 'member_race_ethnicity'] [source: metrics.json#leakage_risks]
- Plan features that are label-derived, protected or identifiers: 4 [source: metrics.json#leakage_risks.flagged_in_plan]

## Artifacts

- `artifacts/tasks/run_007/reflection_only/T5/attempt_1/fraud_prevalence.png`
- `artifacts/tasks/run_007/reflection_only/T5/attempt_1/fraud_comparison.csv`
- `artifacts/tasks/run_007/reflection_only/T5/attempt_1/metrics.json`
- `artifacts/tasks/run_007/reflection_only/T5/attempt_1/report.md`

## Caveats

- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.

## Method

- Seed: 42; plan sha256: `713f3972b7411be3fdb0f31a03cbc6d927275964dbf98eb1fcc6ceb869231de9`.
- Components (canonical order): load_tables, class_prevalence, feature_comparison, leakage_assessment, write_report.
- `load_tables` params: `{}`
- `class_prevalence` params: `{}`
- `feature_comparison` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'auth_required_flag', 'fraud_pattern_type', 'high_cost_flag', 'member_age_band', 'member_sex', 'member_race_ethnicity', 'member_payer_type']}`
- `leakage_assessment` params: `{}`
- `write_report` params: `{'caveats': ['class_imbalance', 'association_not_causation', 'descriptive_only'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['class_imbalance', 'association_not_causation', 'descriptive_only'].
