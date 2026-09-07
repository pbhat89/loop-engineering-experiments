---
skill_id: evolved_run_004_004
name: conventions_denial_code_ranking_scope_quantify_missing_denia
version: 1
status: active
kind: evolved
created_after_task: T4
created_after_task_index: 3
source_feedback_ids: [T4-code_ranking, T4-code_scope, T4-missing_codes_by_status, T4-segment_coverage, T4-segment_rates, T4-professional_denial_rate, T4-segment_denominator]
created_at: "2026-09-07T00:34:39+00:00"
reuse_count: 0
tags: [denials, denial_codes, rates, denominators, segments, small_groups, missingness]
applicable_task_ids: [T5, T6, T7, T8]
run_id: run_004
condition: skill_learning
---

# Conventions denial code ranking scope quantify missing denia

## Trigger
The task catalogue offers denial_code_ranking, denial_rate_by_segment, quantify_missing, scope, segments.

## Objective
House conventions learned from evaluator feedback: component:denial_code_ranking; param:scope=denied_claims; param:quantify_missing=by_status; component:denial_rate_by_segment; list:segments+=provider_specialty; list:segments+=network_status; list:segments+=place_of_service; list:segments+=auth_required_flag

## Procedure
1. Include the `denial_code_ranking` component.
2. `scope` = `denied_claims` on any component that has it.
3. `quantify_missing` = `by_status` on any component that has it.
4. Include the `denial_rate_by_segment` component.
5. Add `provider_specialty` to any `segments` list.
6. Add `network_status` to any `segments` list.
7. Add `place_of_service` to any `segments` list.
8. Add `auth_required_flag` to any `segments` list.

## Required checks
- component:denial_code_ranking
- param:scope=denied_claims
- param:quantify_missing=by_status
- component:denial_rate_by_segment
- list:segments+=provider_specialty
- list:segments+=network_status
- list:segments+=place_of_service
- list:segments+=auth_required_flag

## Expected artifacts
- denial_code_ranking.csv
- denial_rates_by_segment.csv
- denial_rate_by_segment.png

## Failure modes
- A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.
- List additions may name fields or pairs a later task does not load.

## Example
Include the `denial_code_ranking` component.

## Provenance
Evolved skill learned in run `run_004` (condition `skill_learning`) after task T4 (task index 3) from feedback ids T4-code_ranking, T4-code_scope, T4-missing_codes_by_status, T4-segment_coverage, T4-segment_rates, T4-professional_denial_rate, T4-segment_denominator. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-rule-learner` via provider mode `rule_learner` (model `rule-learner-v1`). Declared applicable task ids: T5, T6, T7, T8.
