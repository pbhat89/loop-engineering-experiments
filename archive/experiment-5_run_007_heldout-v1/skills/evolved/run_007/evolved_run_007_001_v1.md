---
skill_id: evolved_run_007_001
name: min_group_size_threshold_for_segmented_rates
version: 1
status: active
kind: evolved
created_after_task: T9
created_after_task_index: 6
source_feedback_ids: [T9-min_group_size]
created_at: "2026-09-08T07:41:06+00:00"
reuse_count: 0
tags: [statistical_discipline, rates, small_groups, segmentation]
applicable_task_ids: [T10, T5]
run_id: run_007
condition: skill_learning
---

# Min group size threshold for segmented rates

## Trigger
When computing rates (denial, spend, error, or other metrics) by segmented groups or dimensions in any analysis task.

## Objective
Flag segments with fewer than 30 claims as statistically unreliable to prevent overinterpreting rates from small sample sizes and maintain statistical discipline across rate analyses.

## Procedure
1. Identify all rate-by-segment components in your analysis plan (such as denial_rate_by_segment or spend_by_segment).
2. Set the min_group_size parameter to 30 to automatically flag any segment value with fewer than 30 claims as potentially unreliable.
3. Review flagged segments in the output and document their small-group status in the report's caveats section.
4. Avoid drawing substantive conclusions from rates computed on flagged segments without explicit caveat language warning stakeholders of statistical limitations.

## Required checks
- The min_group_size parameter is set to 30 in all rate-by-segment components
- Segments flagged as small are clearly marked in the output with a small_group_flag or equivalent indicator
- The report includes a small_groups caveat when flagged segments are present

## Expected artifacts
- Rate output table (e.g., denial_rates_by_segment.csv) with small_group_flag column
- report.md with small_groups caveat included

## Failure modes
- Setting min_group_size too high (e.g., 50) fails to identify unstable segments, leading to false confidence in small-sample rates.
- Omitting the small_groups caveat in the report leaves stakeholders unaware of statistical limitations and risks misinterpretation.
- Not including a small_group_flag in output makes it impossible to distinguish reliable from unreliable segment estimates.

## Example
When analyzing denial rates by place_of_service with min_group_size=30, the ambulatory_surgery_center segment (25 claims) is flagged as unreliable. The report caveat warns that this segment's 56% denial rate lacks stability, preventing misinterpretation of small-sample outliers.

## Provenance
Evolved skill learned in run `run_007` (condition `skill_learning`) after task T9 (task index 6) from feedback ids T9-min_group_size. Evaluation score total at proposal time: 3.77. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T10, T5.
