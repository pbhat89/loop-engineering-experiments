---
skill_id: evolved_run_005_001
name: correct_denial_rate_denominator_selection
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 0
source_feedback_ids: [T2-denial_rate_denominator, T2-denial_rate_value]
created_at: "2026-09-07T09:28:57+00:00"
reuse_count: 0
tags: [rates, denominators, claims_analysis, correctness]
applicable_task_ids: [T4, T3]
run_id: run_005
condition: skill_learning
---

# Correct denial-rate denominator selection

## Trigger
When computing denial rates, authorization-rate, or other claim-status-based metrics where pending claims must be excluded from the calculation base

## Objective
Ensure denial rates and similar status-based metrics are computed over adjudicated claims only (final statuses), excluding Pended claims, to avoid artificially understating the rate

## Procedure
1. Identify all claim statuses in the dataset and determine which ones represent final adjudication decisions versus pending decisions
2. When computing a denial rate or similar metric, use only claims with final adjudication status (Paid, Denied, or Adjusted) as the denominator
3. Explicitly exclude Pended claims from the denominator calculation, as these represent claims not yet decided and their inclusion reduces the apparent rate
4. Record and report both the numerator definition (e.g., count of Denied claims) and the denominator definition with status filter applied
5. Set the appropriate parameter choice (e.g., denominator_option: 'adjudicated_claims') and verify this is documented in the output schema

## Required checks
- Numerator is calculated correctly (e.g., count of claim_status == 'Denied' for denial rate)
- Denominator filter excludes Pended status and includes only {Paid, Denied, Adjusted}
- Parameter denominator_option is set to 'adjudicated_claims' (not 'all_claims')
- Both numerator and denominator definitions are explicitly stated in output and report

## Expected artifacts
- Denial-rate metrics with numerator count, denominator count, and their status definitions
- Report sections documenting the denominator strategy and justifying the exclusion of Pended claims
- Summary tables showing claim counts by adjudication status (Paid, Denied, Adjusted, Pended)

## Failure modes
- Including Pended claims in the denominator understates the denial rate and creates a false impression of performance
- Misclassifying claim statuses (e.g., treating Pended as a type of approval) distorts the calculation
- Failing to document and record the denominator choice makes the metric uninterpretable to stakeholders
- Inconsistent application across tasks leads to non-comparable rates when multiple denial analyses are performed

## Example
In a denial analysis task, ensure that when the denial-rate component executes, the denominator parameter is set to 'adjudicated_claims' rather than 'all_claims'. This ensures that only claims with final statuses contribute to the denominator, and pending claims are excluded. The output must include numerator and denominator counts and their status definitions.

## Provenance
Evolved skill learned in run `run_005` (condition `skill_learning`) after task T2 (task index 0) from feedback ids T2-denial_rate_denominator, T2-denial_rate_value. Evaluation score total at proposal time: 3.8. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T4, T3.
