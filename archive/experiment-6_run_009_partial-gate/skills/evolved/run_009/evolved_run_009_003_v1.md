---
skill_id: evolved_run_009_003
name: include_synthetic_data_caveat_in_analysis_reports
version: 1
status: active
kind: evolved
created_after_task: T4
created_after_task_index: 2
source_feedback_ids: [T4-caveat_synthetic]
created_at: "2026-09-09T02:34:41+00:00"
reuse_count: 0
tags: [communication, transparency, synthetic_data, reporting, caveats]
applicable_task_ids: [T3, T7, T8]
run_id: run_009
condition: skill_learning
---

# Include synthetic data caveat in analysis reports

## Trigger
When preparing analysis reports on synthetic or simulated claims datasets

## Objective
Ensure analysis reports transparently communicate that findings are based on synthetic or simulated data, enabling stakeholders to appropriately interpret results and avoid misattributing analysis findings to production systems.

## Procedure
1. Before finalizing the analysis report, confirm the data source is synthetic or simulated rather than production data.
2. Add the 'synthetic_data' caveat to the write_report component's caveats parameter list (if not already present).
3. Verify that the report's Caveats section explicitly states the data is synthetic or simulated, using keywords such as 'synthetic' or 'simulated' in plain language.
4. Ensure the synthetic data caveat appears prominently in the Caveats section, positioned before results sections so stakeholders encounter it early.
5. Review the final report to confirm that the synthetic nature of the data is clear to readers and would not be misinterpreted as production data findings.

## Required checks
- Data source confirmed to be synthetic or simulated
- Report includes 'synthetic_data' caveat in caveats list
- Report text contains language explicitly identifying data as synthetic or simulated
- Caveat statement appears in the Caveats section of the report
- Final report would not mislead stakeholders into interpreting results as production-data findings

## Expected artifacts
- report.md (with Caveats section including synthetic_data statement)

## Failure modes
- Synthetic data caveat omitted from report, causing stakeholders to misinterpret simulated findings as production data results
- Caveat language too vague or technical, failing to clearly communicate that data is synthetic
- Caveat buried in appendix or fine print, reducing visibility and recall by stakeholders

## Example
For a denial analysis task on synthetic claims data, include the caveat 'Note: This analysis is based on synthetic, simulated claims data and does not represent actual production system findings. Results are illustrative only.' in the Caveats section before the Results section to ensure stakeholders understand the data source and limitations.

## Provenance
Evolved skill learned in run `run_009` (condition `skill_learning`) after task T4 (task index 2) from feedback ids T4-caveat_synthetic. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T7, T8.
