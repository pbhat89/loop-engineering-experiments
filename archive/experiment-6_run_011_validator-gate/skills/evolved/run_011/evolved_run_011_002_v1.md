---
skill_id: evolved_run_011_002
name: adjudicated_claims_denial_rate_computation
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 1
source_feedback_ids: [T2-denial_rate_value, T2-denial_rate_denominator]
created_at: "2026-09-09T03:00:22+00:00"
reuse_count: 0
tags: [rates, denominators, statistical_discipline, denial]
applicable_task_ids: [T3, T4]
run_id: run_011
condition: skill_learning
---

# Adjudicated claims denial rate computation

## Trigger
When calculating denial rate for any claims portfolio analysis, subset analysis, or comparative study.

## Objective
Compute denial rate correctly over adjudicated claims only, excluding pending claims, to avoid understating the rate and conflating adjudication status outcomes with claim volume.

## Procedure
1. Define adjudicated claims explicitly as those with claim_status in the set {Paid, Denied, Adjusted}, and exclude claims with status Pended.
2. Count denied claims as those where claim_status == 'Denied'.
3. Compute the denominator as the total count of adjudicated claims using the definition above.
4. Calculate denial_rate = denied_count / adjudicated_count.
5. Record both the numerator count (denied claims) and denominator count (adjudicated claims) in the output.
6. Document the denominator_option as 'adjudicated_claims' explicitly in all results, reports, and metrics.
7. Include written definitions of both numerator and denominator in any summary or report.

## Required checks
- Pending claims are explicitly excluded from the denominator
- Numerator and denominator counts are both reported alongside the rate
- Denominator definition is recorded in output metadata
- Written definitions of numerator and denominator appear in report text

## Expected artifacts
- denial_rate metric with numerator, denominator, and denominator_option fields
- report section documenting the denial rate calculation basis

## Failure modes
- Including pending claims in the denominator understates the rate by conflating unresolved claims with decided ones
- Reporting only the rate without numerator and denominator hides the calculation basis and prevents verification
- Using adjudication_date instead of claim_status for filtering creates temporal inconsistency

## Example
Given 12,845 total claims in the medical_claims table: 8,200 with status 'Paid', 1,850 with status 'Denied', 1,795 with status 'Adjusted', and 1,000 with status 'Pended'. Adjudicated claims = 8,200 + 1,850 + 1,795 = 11,845 (excluding 1,000 Pended). Denial rate = 1,850 / 11,845 = 0.156 (15.6%). The output records numerator=1,850, denominator=11,845, denominator_option='adjudicated_claims', and the report states: 'Of 11,845 adjudicated claims, 1,850 (15.6%) were denied, excluding 1,000 claims still pending adjudication.'

## Provenance
Evolved skill learned in run `run_011` (condition `skill_learning`) after task T2 (task index 1) from feedback ids T2-denial_rate_value, T2-denial_rate_denominator. Evaluation score total at proposal time: 3.67. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T4.
