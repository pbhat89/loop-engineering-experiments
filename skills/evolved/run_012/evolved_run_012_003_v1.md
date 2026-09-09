---
skill_id: evolved_run_012_003
name: use_adjudicated_claims_as_denominator_for_segment_rates
version: 1
status: active
kind: evolved
created_after_task: T4
created_after_task_index: 2
source_feedback_ids: [T4-segment_denominator]
created_at: "2026-09-09T03:44:21+00:00"
reuse_count: 0
tags: [rates, denominators, segment_analysis, statistical_discipline]
applicable_task_ids: [T5]
run_id: run_012
condition: skill_learning
---

# Use adjudicated claims as denominator for segment rates

## Trigger
When calculating denial rates or other rates by claim characteristics and segments

## Objective
Establish the correct statistical denominator (adjudicated claims) when calculating segment-level rates, enabling valid comparisons and sound operational decision-making

## Procedure
1. When calculating denial rates (or other rates) by segment values (claim_type, provider_specialty, network_status, place_of_service, auth_required_flag, etc.), use only adjudicated claims as the denominator
2. Define adjudicated claims as those with claim status in {Paid, Denied, Adjusted}, explicitly excluding unadjudicated or pending statuses
3. Set the denominator_option field to 'adjudicated_claims' and record this choice in all output
4. Calculate the rate as numerator / adjudicated_claims_denominator for each segment value
5. Document that this approach provides the correct basis for segment-level rate comparison and operational decision-making

## Required checks
- Verify denominator_option is set to 'adjudicated_claims' in the output
- Confirm each segment's numerator and denominator are aligned within the adjudicated_claims population
- Check that segment denominators sum to the total adjudicated claims

## Expected artifacts
- Segment rate table with denominators shown
- Segment rate visualization

## Failure modes
- Using all_claims as denominator, which conflates adjudicated and unadjudicated claims and produces inflated rate estimates
- Not recording which denominator definition was used, creating ambiguity for readers
- Misalignment between numerator and denominator scope across segments

## Example
For a dataset with 1000 total claims (800 adjudicated, 200 pending), calculating denial rates by claim_type: using all_claims as denominator produces inaccurate rates that conflate pending claims with adjudicated outcomes (e.g., 80 denials / 1000 total = 8% vs. 80 denials / 800 adjudicated = 10%). Using adjudicated_claims ensures segment rates are comparable and reflect the true denial likelihood among decided claims.

## Provenance
Evolved skill learned in run `run_012` (condition `skill_learning`) after task T4 (task index 2) from feedback ids T4-segment_denominator. Evaluation score total at proposal time: 3.84. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T5.
