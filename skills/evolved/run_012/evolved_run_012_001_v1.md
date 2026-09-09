---
skill_id: evolved_run_012_001
name: document_synthetic_data_limitations_in_all_reports
version: 1
status: active
kind: evolved
created_after_task: T1
created_after_task_index: 0
source_feedback_ids: [T1-caveat_synthetic]
created_at: "2026-09-09T03:31:09+00:00"
reuse_count: 0
tags: [data_quality, communication, compliance, synthetic_data]
applicable_task_ids: [T2, T3, T4, T5, T6, T7, T8]
run_id: run_012
condition: skill_learning
---

# Document synthetic data limitations in all reports

## Trigger
Writing any reconnaissance, analysis, or summary report on synthetic or simulated claims data.

## Objective
Ensure all reports clearly disclose that the data is synthetic and that observed patterns, distributions, and anomalies may not reflect real-world claims characteristics.

## Procedure
1. When writing the report for any task involving synthetic or simulated claims data, include the 'synthetic_data' caveat in the report's Caveats section.
2. Phrase the caveat to clearly state that the dataset is synthetic or simulated, and explicitly note that findings, patterns, and numerical results should not be interpreted as representative of actual claims behavior.
3. Place this caveat early in the Caveats section so readers encounter it before interpreting any results.

## Required checks
- Verify that the report includes the synthetic_data caveat either as a listed caveat item or as explicit phrasing in the report text.
- Check that the caveat language clearly identifies the data as synthetic and disclaims generalizability to real-world claims.

## Expected artifacts
- report.md or equivalent analysis summary with synthetic_data caveat included in Caveats section

## Failure modes
- Report lacks any mention of synthetic data, leaving readers unaware of data limitations.
- Caveat is vague or uses language like 'simulated' without clearly identifying the data as synthetic.
- Caveat is present but buried in narrative text rather than highlighted in a Caveats section, reducing visibility.

## Example
In the Caveats section: 'This analysis is based on synthetic claims data. The patterns, distributions, and numerical findings presented here are artifacts of the simulated dataset and should not be interpreted as representative of real-world claims characteristics or used for operational decisions on actual claims data.'

## Provenance
Evolved skill learned in run `run_012` (condition `skill_learning`) after task T1 (task index 0) from feedback ids T1-caveat_synthetic. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T2, T3, T4, T5, T6, T7, T8.
