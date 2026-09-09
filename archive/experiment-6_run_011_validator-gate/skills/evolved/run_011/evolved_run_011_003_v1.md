---
skill_id: evolved_run_011_003
name: synthetic_data_transparency_in_reports
version: 1
status: active
kind: evolved
created_after_task: T4
created_after_task_index: 2
source_feedback_ids: [T4-caveat_synthetic]
created_at: "2026-09-09T03:04:58+00:00"
reuse_count: 0
tags: [reporting, data_quality, communication, synthetic_data]
applicable_task_ids: [T5, T6, T7, T8]
run_id: run_011
condition: skill_learning
---

# Synthetic data transparency in reports

## Trigger
When preparing a report for any claims-analysis task involving synthetic data.

## Objective
Ensure stakeholder transparency about data provenance by explicitly disclosing that the analysis rests on synthetic rather than operational data, so stakeholders understand the findings' limitations and applicability.

## Procedure
1. Before finalizing a report, confirm from the data manifest that the input tables are synthetic rather than operational.
2. Add the 'synthetic_data' caveat to the write_report component's caveats parameter if not already included.
3. Verify that the report text explicitly mentions the synthetic nature of the data using language such as 'synthetic data', 'simulated', or 'synthetic dataset'.
4. Document how synthetic data affects the interpretation and operational use of findings (e.g., results should not be directly applied operationally without validation on real data).
5. Confirm the caveat appears in the finalized report and is visible to stakeholders.

## Required checks
- 'synthetic_data' caveat is present in the report's caveats section
- Report text explicitly names the data as synthetic or simulated
- Limitations or applicability guidance for synthetic data findings is stated

## Expected artifacts
- report.md with synthetic_data caveat in the Caveats section
- metrics.json documenting data provenance awareness

## Failure modes
- Caveat section exists but 'synthetic_data' caveat is omitted from the caveats parameter, leaving stakeholders unaware of data provenance
- Report text fails to explicitly name the synthetic nature of the data, creating false perception of operational data
- Synthetic data limitations are mentioned but not linked to actionable guidance on validation or real-data testing before operational deployment
- Manifest check is skipped; caveat is added without confirming the data source is actually synthetic

## Example
In Task T4 denial analysis, confirm from manifest_summary that medical_claims is synthetic. Add 'synthetic_data' to write_report's caveats parameter. Ensure report includes explicit language: 'This analysis uses synthetic claims data designed to reflect real-world patterns. All denial rates and findings should be validated against operational data before deployment.' Verify the caveat statement appears prominently in the finalized report.md before stakeholder delivery.

## Provenance
Evolved skill learned in run `run_011` (condition `skill_learning`) after task T4 (task index 2) from feedback ids T4-caveat_synthetic. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T5, T6, T7, T8.
