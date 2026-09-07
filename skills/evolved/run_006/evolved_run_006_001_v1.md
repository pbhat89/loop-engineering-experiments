---
skill_id: evolved_run_006_001
name: include_synthetic_data_caveat_in_reports
version: 1
status: active
kind: evolved
created_after_task: T1
created_after_task_index: 0
source_feedback_ids: [T1-caveat_synthetic]
created_at: "2026-09-07T15:49:34+00:00"
reuse_count: 0
tags: [reporting, caveats, data_governance, communication]
applicable_task_ids: [T2, T3, T4, T7, T8]
run_id: run_006
condition: skill_learning
---

# Include synthetic data caveat in reports

## Trigger
When writing reports based on synthetic or simulated data

## Objective
Ensure all analysis reports clearly communicate that findings are derived from synthetic data rather than production data, enabling stakeholders to properly interpret results and maintain data governance standards across analysis tasks.

## Procedure
1. Before finalizing any report on synthetic data, verify that the write_report component's caveats parameter includes 'synthetic_data'.
2. Confirm that the report text includes language stating the dataset is synthetic or simulated, ensuring stakeholders understand the data source.
3. Review all caveats to confirm synthetic_data is appropriate for the dataset being analyzed.

## Required checks
- Confirm 'synthetic_data' caveat is listed in the write_report component's caveats parameter
- Verify 'synthetic' or 'simulated' language appears in the report Caveats section

## Expected artifacts
- report.md with synthetic_data listed in caveats

## Failure modes
- Report lacks synthetic_data caveat, leaving stakeholders unaware data is synthetic
- Caveats parameter omits synthetic_data despite dataset being synthetic

## Example
For T1 (Dataset reconnaissance), when writing report.md, ensure the write_report component's caveats parameter includes 'synthetic_data', resulting in the report containing language such as 'This analysis uses synthetically generated member and claims data' in the Caveats section.

## Provenance
Evolved skill learned in run `run_006` (condition `skill_learning`) after task T1 (task index 0) from feedback ids T1-caveat_synthetic. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T2, T3, T4, T7, T8.
