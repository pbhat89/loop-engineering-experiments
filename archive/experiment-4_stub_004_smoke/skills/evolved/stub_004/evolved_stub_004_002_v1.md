---
skill_id: evolved_stub_004_002
name: wrong_denominator_correctness
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 1
source_feedback_ids: [T2-denial_rate_value]
created_at: "2026-09-07T15:32:15+00:00"
reuse_count: 0
tags: [correctness, denominators, descriptive, financial, portfolio, rates, status_mix, trends]
applicable_task_ids: [T3, T4]
run_id: stub_004
condition: skill_learning
---

# Wrong denominator correctness

## Trigger
When a task involves denial_rate on claims data.

## Objective
Compute the denial rate over adjudicated claims (Paid, Denied, Adjusted; Pended claims are not yet decided) and state numerator and denominator.

## Procedure
1. Compute the denial rate over adjudicated claims (Paid, Denied, Adjusted; Pended claims are not yet decided) and state numerator and denominator.
2. Apply catalogue components: denial_rate.
3. Set parameters: denial_rate.denominator=adjudicated_claims.

## Required checks
- Plan includes denial_rate

## Expected artifacts
- claims_status_distribution.png
- monthly_claim_volume.png
- financial_summary.csv

## Failure modes
- Applying the convention without stating it in the report.

## Example
Fixture-generated from T2-denial_rate_value on T2.

## Provenance
Evolved skill learned in run `stub_004` (condition `skill_learning`) after task T2 (task index 1) from feedback ids T2-denial_rate_value. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-fixture` via provider mode `stub` (model `deterministic-fixture-v1`). Declared applicable task ids: T3, T4.
