---
skill_id: evolved_run_009_002
name: compute_denial_rates_over_adjudicated_claims
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 1
source_feedback_ids: [T2-denial_rate_value, T2-denial_rate_denominator]
created_at: "2026-09-09T02:29:29+00:00"
reuse_count: 0
tags: [rates, denominators, correctness, statistical_discipline]
applicable_task_ids: [T3, T4]
run_id: run_009
condition: skill_learning
---

# Compute denial rates over adjudicated claims

## Trigger
When measuring denial rate from claims data, ensure the denominator is statistically correct by using only claims that have completed adjudication.

## Objective
Ensure denial rates are computed over adjudicated claims (Paid, Denied, Adjusted) to exclude pending claims and yield statistically correct rates that demonstrate statistical discipline and reproducibility.

## Procedure
1. Identify the claim_status column and enumerate its distinct values to confirm the presence of Paid, Denied, Adjusted, and Pended statuses.
2. Define adjudicated claims as those with claim_status in {Paid, Denied, Adjusted}, excluding Pended and other interim statuses.
3. Filter the claims dataset to only adjudicated claims using this status criterion.
4. Count denied claims (claim_status == 'Denied') as the numerator of the denial rate.
5. Count the total adjudicated claims (filtered set) as the denominator.
6. Compute denial rate as numerator / denominator.
7. Record in the metric output: numerator (count of Denied), denominator (count of adjudicated claims), numerator_definition (string describing Denied filter), denominator_definition (string describing Adjudicated definition), and denominator_option ('adjudicated_claims') to ensure clarity and reproducibility.

## Required checks
- Denominator includes only claims with status in {Paid, Denied, Adjusted} and excludes Pended.
- Numerator is count of claims with claim_status == 'Denied'.
- Denominator count in metric is total of filtered adjudicated claims.
- denominator_option in metric is recorded as 'adjudicated_claims'.
- numerator_definition and denominator_definition are present and descriptive.

## Expected artifacts
- metrics.json

## Failure modes
- Using all_claims as denominator, which includes Pended claims not yet decided and understates the true denial rate.
- Using only Paid and Denied statuses in denominator, which excludes Adjusted claims and biases the rate.
- Failing to record the denominator_option field, preventing clarity and downstream use of the metric.

## Example
For a dataset with claim_status values: Paid (8000), Denied (1200), Adjusted (200), Pended (500); adjudicated claims = 9400; denial rate = 1200/9400 = 12.77%.

## Provenance
Evolved skill learned in run `run_009` (condition `skill_learning`) after task T2 (task index 1) from feedback ids T2-denial_rate_value, T2-denial_rate_denominator. Evaluation score total at proposal time: 3.67. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T4.
