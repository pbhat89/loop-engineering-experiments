---
skill_id: evolved_run_004_005
name: conventions_feature_comparison_features_leakage_assessment_c
version: 1
status: active
kind: evolved
created_after_task: T5
created_after_task_index: 4
source_feedback_ids: [T5-no_leaking_features, T5-permitted_feature_coverage, T5-leakage_assessment_executed, T5-leakage_lists_pattern_type, T5-caveat_class_imbalance, T5-caveat_no_operational_use]
created_at: "2026-09-07T00:34:43+00:00"
reuse_count: 0
tags: [fraud, exploration, class_imbalance, leakage, protected_attributes, comparison, prevalence, modeling, classification, high_cost, communication, caveats, descriptive, rates, denials, providers]
applicable_task_ids: [T6, T7, T8]
run_id: run_004
condition: skill_learning
---

# Conventions feature comparison features leakage assessment c

## Trigger
The task catalogue offers caveats, feature_comparison, features, leakage_assessment.

## Objective
House conventions learned from evaluator feedback: component:feature_comparison; list:features+=cpt_category; list:features+=place_of_service; list:features+=provider_specialty; list:features+=network_status; list:features+=allowed_amount; list:features+=paid_amount; list:features+=service_units; list:features+=length_of_stay; list:features+=er_flag; list:features+=auth_required_flag; list:features-=fraud_pattern_type; component:leakage_assessment; list:caveats+=class_imbalance; list:caveats+=no_operational_use

## Procedure
1. Include the `feature_comparison` component.
2. Add `cpt_category` to any `features` list.
3. Add `place_of_service` to any `features` list.
4. Add `provider_specialty` to any `features` list.
5. Add `network_status` to any `features` list.
6. Add `allowed_amount` to any `features` list.
7. Add `paid_amount` to any `features` list.
8. Add `service_units` to any `features` list.
9. Add `length_of_stay` to any `features` list.
10. Add `er_flag` to any `features` list.
11. Add `auth_required_flag` to any `features` list.
12. Remove `fraud_pattern_type` from any `features` list.
13. Include the `leakage_assessment` component.
14. Add `class_imbalance` to any `caveats` list.
15. Add `no_operational_use` to any `caveats` list.

## Required checks
- component:feature_comparison
- list:features+=cpt_category
- list:features+=place_of_service
- list:features+=provider_specialty
- list:features+=network_status
- list:features+=allowed_amount
- list:features+=paid_amount
- list:features+=service_units
- list:features+=length_of_stay
- list:features+=er_flag
- list:features+=auth_required_flag
- list:features-=fraud_pattern_type
- component:leakage_assessment
- list:caveats+=class_imbalance
- list:caveats+=no_operational_use

## Expected artifacts
- fraud_comparison.csv
- fraud_prevalence.png
- report.md

## Failure modes
- A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.
- List additions may name fields or pairs a later task does not load.

## Example
Include the `feature_comparison` component.

## Provenance
Evolved skill learned in run `run_004` (condition `skill_learning`) after task T5 (task index 4) from feedback ids T5-no_leaking_features, T5-permitted_feature_coverage, T5-leakage_assessment_executed, T5-leakage_lists_pattern_type, T5-caveat_class_imbalance, T5-caveat_no_operational_use. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-rule-learner` via provider mode `rule_learner` (model `rule-learner-v1`). Declared applicable task ids: T6, T7, T8.
