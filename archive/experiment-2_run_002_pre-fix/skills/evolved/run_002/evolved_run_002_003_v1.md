---
skill_id: evolved_run_002_003
name: conventions_group_comparison_min_group_size_group_by_metrics
version: 1
status: active
kind: evolved
created_after_task: T3
created_after_task_index: 2
source_feedback_ids: [T3-groups_network_status, T3-groups_specialty, T3-in_network_denial_rate, T3-out_of_network_denial_rate, T3-group_denominator, T3-min_group_size, T3-group_by_coverage, T3-metric_coverage, T3-provider_ranking_rows, T3-provider_ranking_executed, T3-provider_ranking_csv, T3-caveat_small_groups, T3-caveat_association]
created_at: "2026-09-07T00:24:17+00:00"
reuse_count: 0
tags: [providers, network, specialty, group_comparison, small_groups, rates, denominators, joins, cardinality, segments, metrics, communication, caveats, descriptive, modeling, fraud, denials]
applicable_task_ids: [T4, T5, T6, T7, T8]
run_id: run_002
condition: skill_learning
---

# Conventions group comparison min group size group by metrics

## Trigger
The task catalogue offers caveats, group_by, group_comparison, metric, metrics, min_claims, min_group_size, provider_ranking, top_n.

## Objective
House conventions learned from evaluator feedback: component:group_comparison; param:min_group_size=30; list:group_by+=network_status; list:metrics+=paid_amount_mean; list:metrics+=denial_rate; list:metrics+=fraud_rate; component:provider_ranking; param:metric=claim_count; param:top_n=10; param:min_claims=0; list:caveats+=small_groups; list:caveats+=association_not_causation; list:caveats-=descriptive_only

## Procedure
1. Include the `group_comparison` component.
2. `min_group_size` = `30` on any component that has it.
3. Add `network_status` to any `group_by` list.
4. Add `paid_amount_mean` to any `metrics` list.
5. Add `denial_rate` to any `metrics` list.
6. Add `fraud_rate` to any `metrics` list.
7. Include the `provider_ranking` component.
8. `metric` = `claim_count` on any component that has it.
9. `top_n` = `10` on any component that has it.
10. `min_claims` = `0` on any component that has it.
11. Add `small_groups` to any `caveats` list.
12. Add `association_not_causation` to any `caveats` list.
13. Remove `descriptive_only` from any `caveats` list.

## Required checks
- component:group_comparison
- param:min_group_size=30
- list:group_by+=network_status
- list:metrics+=paid_amount_mean
- list:metrics+=denial_rate
- list:metrics+=fraud_rate
- component:provider_ranking
- param:metric=claim_count
- param:top_n=10
- param:min_claims=0
- list:caveats+=small_groups
- list:caveats+=association_not_causation
- list:caveats-=descriptive_only

## Expected artifacts
- group_comparison.csv
- group_comparison.png
- provider_ranking.csv

## Failure modes
- A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.
- List additions may name fields or pairs a later task does not load.

## Example
Include the `group_comparison` component.

## Provenance
Evolved skill learned in run `run_002` (condition `skill_learning`) after task T3 (task index 2) from feedback ids T3-groups_network_status, T3-groups_specialty, T3-in_network_denial_rate, T3-out_of_network_denial_rate, T3-group_denominator, T3-min_group_size, T3-group_by_coverage, T3-metric_coverage, T3-provider_ranking_rows, T3-provider_ranking_executed, T3-provider_ranking_csv, T3-caveat_small_groups, T3-caveat_association. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-rule-learner` via provider mode `rule_learner` (model `rule-learner-v1`). Declared applicable task ids: T4, T5, T6, T7, T8.
