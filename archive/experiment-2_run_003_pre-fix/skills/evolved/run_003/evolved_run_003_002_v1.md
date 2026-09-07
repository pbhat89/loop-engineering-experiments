---
skill_id: evolved_run_003_002
name: conventions_denial_rate_denominator_fraud_prevalence_financi
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 1
source_feedback_ids: [T2-denial_rate_value, T2-denial_rate_denominator, T2-fraud_prevalence_value, T2-fraud_prevalence_executed, T2-financial_columns, T2-paid_amount_quantiles, T2-monthly_date_column, T2-monthly_counts, T2-show_denominators, T2-denominator_format, T2-caveat_descriptive]
created_at: "2026-09-07T00:29:53+00:00"
reuse_count: 0
tags: [descriptive, portfolio, rates, denominators, financial, trends, status_mix, denials, fraud, prevalence, communication, providers, caveats, modeling]
applicable_task_ids: [T3, T4, T5, T6, T7, T8]
run_id: run_003
condition: skill_learning
---

# Conventions denial rate denominator fraud prevalence financi

## Trigger
The task catalogue offers amount_columns, caveats, date_column, denial_rate, denominator, financial_summary, fraud_prevalence, monthly_trend, show_denominators, statistics.

## Objective
House conventions learned from evaluator feedback: component:denial_rate; param:denominator=adjudicated_claims; component:fraud_prevalence; param:denominator=all_claims; component:financial_summary; param:statistics=sum_mean_quantiles; list:amount_columns+=billed_amount; list:amount_columns+=allowed_amount; component:monthly_trend; param:date_column=service_date_from; param:show_denominators=true; list:caveats+=descriptive_only

## Procedure
1. Include the `denial_rate` component.
2. `denominator` = `adjudicated_claims` on any component that has it.
3. Include the `fraud_prevalence` component.
4. `denominator` = `all_claims` on any component that has it.
5. Include the `financial_summary` component.
6. `statistics` = `sum_mean_quantiles` on any component that has it.
7. Add `billed_amount` to any `amount_columns` list.
8. Add `allowed_amount` to any `amount_columns` list.
9. Include the `monthly_trend` component.
10. `date_column` = `service_date_from` on any component that has it.
11. `show_denominators` = `true` on any component that has it.
12. Add `descriptive_only` to any `caveats` list.

## Required checks
- component:denial_rate
- param:denominator=adjudicated_claims
- component:fraud_prevalence
- param:denominator=all_claims
- component:financial_summary
- param:statistics=sum_mean_quantiles
- list:amount_columns+=billed_amount
- list:amount_columns+=allowed_amount
- component:monthly_trend
- param:date_column=service_date_from
- param:show_denominators=true
- list:caveats+=descriptive_only

## Expected artifacts
- claims_status_distribution.png
- monthly_claim_volume.png
- financial_summary.csv

## Failure modes
- A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.
- List additions may name fields or pairs a later task does not load.

## Example
Include the `denial_rate` component.

## Provenance
Evolved skill learned in run `run_003` (condition `skill_learning`) after task T2 (task index 1) from feedback ids T2-denial_rate_value, T2-denial_rate_denominator, T2-fraud_prevalence_value, T2-fraud_prevalence_executed, T2-financial_columns, T2-paid_amount_quantiles, T2-monthly_date_column, T2-monthly_counts, T2-show_denominators, T2-denominator_format, T2-caveat_descriptive. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-rule-learner` via provider mode `rule_learner` (model `rule-learner-v1`). Declared applicable task ids: T3, T4, T5, T6, T7, T8.
