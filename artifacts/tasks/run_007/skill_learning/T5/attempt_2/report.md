# T5 — Fraud-pattern exploration

## Summary

Task T5 (Fraud-pattern exploration) for run `run_007` / condition `skill_learning`, attempt 2: status **ok**; 5 component(s) executed, 0 failed, 0 error(s) recorded.
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
- billed_amount mean (flagged / unflagged) = 1692.484529 / 1652.662020 [source: metrics.json#feature_comparison]
- allowed_amount mean (flagged / unflagged) = 994.537975 / 945.380995 [source: metrics.json#feature_comparison]
- paid_amount mean (flagged / unflagged) = 832.084420 / 757.915818 [source: metrics.json#feature_comparison]
- er_flag: most common value among flagged = 0; share: 0.967543 [source: metrics.json#feature_comparison]
- high_cost_flag: most common value among flagged = 0; share: 0.973725 [source: metrics.json#feature_comparison]

### leakage_assessment

- Label-derived: ['fraud_pattern_type']; protected: ['member_sex', 'member_race_ethnicity', 'member_age_band', 'member_income_band']; flagged features in this plan: none [source: metrics.json#leakage_risks]
- Plan features that are label-derived, protected or identifiers: 0 [source: metrics.json#leakage_risks.flagged_in_plan]

## Artifacts

- `artifacts/tasks/run_007/skill_learning/T5/attempt_2/fraud_prevalence.png`
- `artifacts/tasks/run_007/skill_learning/T5/attempt_2/fraud_comparison.csv`
- `artifacts/tasks/run_007/skill_learning/T5/attempt_2/metrics.json`
- `artifacts/tasks/run_007/skill_learning/T5/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **association_not_causation**: Differences between groups are associations only and must not be read as causal effects.
- **small_groups**: Groups below the minimum group size are flagged; their rates are unstable and should not be compared.
- **class_imbalance**: The positive class is rare; accuracy-style summaries are misleading and precision/recall must be read against the base rate.
- **no_operational_use**: Nothing in this analysis is suitable for operational decisions about claims, members or providers.

## Method

- Seed: 42; plan sha256: `089dcc6cc1b6e567322ed53d39c2c644bee498773e06484e7d6ebf566d14ea07`.
- Components (canonical order): load_tables, class_prevalence, feature_comparison, leakage_assessment, write_report.
- `load_tables` params: `{}`
- `class_prevalence` params: `{}`
- `feature_comparison` params: `{'features': ['claim_type', 'cpt_category', 'place_of_service', 'billed_amount', 'allowed_amount', 'paid_amount', 'er_flag', 'high_cost_flag']}`
- `leakage_assessment` params: `{}`
- `write_report` params: `{'caveats': ['synthetic_data', 'descriptive_only', 'association_not_causation', 'small_groups', 'class_imbalance', 'no_operational_use'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data', 'descriptive_only', 'association_not_causation', 'small_groups', 'class_imbalance', 'no_operational_use'].
