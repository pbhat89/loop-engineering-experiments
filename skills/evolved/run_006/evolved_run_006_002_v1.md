---
skill_id: evolved_run_006_002
name: denial_rate_denominator_standardization
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 1
source_feedback_ids: [T2-denial_rate_value, T2-denial_rate_denominator]
created_at: "2026-09-07T16:03:45+00:00"
reuse_count: 0
tags: [rates, denial_analysis, statistical_discipline, denominator_selection]
applicable_task_ids: [T3, T4]
run_id: run_006
condition: skill_learning
---

# Denial rate denominator standardization

## Trigger
When computing denial rates for claims analysis or denial assessment tasks involving claim status breakdowns

## Objective
Ensure denial rates are computed consistently using adjudicated claims (Paid, Denied, Adjusted) as the denominator, excluding Pended claims to avoid understating the rate and to meet reproducibility standards required by stakeholders.

## Procedure
1. Identify and separate claims into two groups: adjudicated_claims (status in {Paid, Denied, Adjusted}) and Pended claims.
2. Compute denial_rate numerator as the count of claims with status == 'Denied' within the adjudicated_claims group only.
3. Compute denial_rate denominator as the total count of all adjudicated_claims (sum of Paid + Denied + Adjusted status counts).
4. Record and report both the numerator count and denominator count explicitly with their definitions to ensure transparency and reproducibility.
5. Verify the denominator_option parameter is set to 'adjudicated_claims' in the analysis pipeline and confirm Pended claims are excluded from the calculation.

## Required checks
- denial_rate.denominator_option is set to 'adjudicated_claims' (not 'all_claims')
- Both numerator count (Denied) and denominator count (adjudicated_claims total) are explicitly reported in the output
- The analysis method section documents the exclusion of Pended claims from the denial rate denominator

## Expected artifacts
- metrics.json or summary table containing denial_rate with numerator_value and denominator_value fields

## Failure modes
- Using all_claims as denominator (including Pended status) — understates the true denial rate and misrepresents claim adjudication outcomes
- Not recording numerator and denominator separately — obscures the rate calculation and prevents stakeholders from verifying the metric
- Inconsistent denominator choice across tasks — different definitions used for the same metric across T3, T4, and related tasks undermines comparability

## Example
When analyzing claims with mixed statuses, if 12,000 total claims contain 8,000 adjudicated (6,500 Paid + 1,300 Denied + 200 Adjusted) and 4,000 Pended, set denial_rate denominator='adjudicated_claims' to compute 1,300 / 8,000 = 16.25% instead of 1,300 / 12,000 = 10.83%, and explicitly record both counts and the denominator_option choice in the output.

## Provenance
Evolved skill learned in run `run_006` (condition `skill_learning`) after task T2 (task index 1) from feedback ids T2-denial_rate_value, T2-denial_rate_denominator. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T4.
