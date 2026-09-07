---
skill_id: evolved_stub_001_005
name: leakage_statistical_discipline
version: 1
status: active
kind: evolved
created_after_task: T5
created_after_task_index: 4
source_feedback_ids: [T5-no_leaking_features]
created_at: "2026-09-06T17:12:46+00:00"
reuse_count: 0
tags: [class_imbalance, comparison, exploration, fraud, leakage, prevalence, protected_attributes, statistical_discipline]
applicable_task_ids: [T6, T7]
run_id: stub_001
condition: skill_learning
---

# Leakage statistical discipline

## Trigger
When a task involves feature_comparison on claims data.

## Objective
Remove fraud_pattern_type (populated only when fraud_label is 1) and the protected attributes member_sex, member_race_ethnicity and member_age_band from the comparison; compare permitted claim-level features only.

## Procedure
1. Remove fraud_pattern_type (populated only when fraud_label is 1) and the protected attributes member_sex, member_race_ethnicity and member_age_band from the comparison; compare permitted claim-level features only.
2. Apply catalogue components: feature_comparison.
3. Set parameters: feature_comparison.features=['claim_type', 'cpt_category', 'place_of_service', 'provider_specialty', 'network_status', 'billed_amount', 'allowed_amount', 'paid_amount', 'service_units', 'length_of_stay', 'er_flag', 'auth_required_flag'].

## Required checks
- Plan includes feature_comparison

## Expected artifacts
- fraud_comparison.csv
- fraud_prevalence.png
- report.md

## Failure modes
- Applying the convention without stating it in the report.

## Example
Fixture-generated from T5-no_leaking_features on T5.

## Provenance
Evolved skill learned in run `stub_001` (condition `skill_learning`) after task T5 (task index 4) from feedback ids T5-no_leaking_features. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-fixture` via provider mode `stub` (model `deterministic-fixture-v1`). Declared applicable task ids: T6, T7.
