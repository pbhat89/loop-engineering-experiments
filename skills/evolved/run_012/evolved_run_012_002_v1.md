---
skill_id: evolved_run_012_002
name: include_descriptive_analysis_caveat_in_all_reports
version: 1
status: active
kind: evolved
created_after_task: T2
created_after_task_index: 1
source_feedback_ids: [T2-caveat_descriptive]
created_at: "2026-09-09T03:38:40+00:00"
reuse_count: 0
tags: [communication, caveats, methodology, descriptive_analysis, reader_protection]
applicable_task_ids: [T3, T4]
run_id: run_012
condition: skill_learning
---

# Include descriptive analysis caveat in all reports

## Trigger
When writing a report for a descriptive analysis of claims data that examines distributions, financial metrics, trends, or patterns without making causal claims

## Objective
Ensure all descriptive analysis reports include a caveat explicitly stating that the analysis is descriptive only and supports no causal or operational conclusions, protecting readers from misinterpretation of findings

## Procedure
1. When using the write_report component for any descriptive claims analysis, include the 'descriptive_only' caveat in the report component's caveats parameter.
2. Phrase the caveat to clearly state that the analysis is descriptive in nature and that findings, distributions, and patterns should not be interpreted as supporting causal claims or operational decisions without further investigation.
3. Place this caveat early in the Caveats section so readers encounter the limitation before interpreting results.

## Required checks
- Verify that 'descriptive_only' is listed among the report component's caveats or that equivalent descriptive-analysis disclaimer language is present in the report text.
- Confirm that the caveat language clearly identifies the analysis as descriptive and disclaims causal and operational interpretation.

## Expected artifacts
- report.md with Caveats section containing descriptive_only caveat explicitly stated

## Failure modes
- Readers misinterpret observed distributions or trends as supporting causal or operational conclusions without qualification
- Report is published without clear caveat disclaimer, leading to overconfident claims based on descriptive findings
- Caveat language is vague or positioned late in the report, failing to protect reader understanding before results are presented

## Example
When analyzing claims portfolio status distributions and monthly trends to describe the claims book, include the descriptive_only caveat in write_report to ensure readers understand that observed patterns show what occurred but do not establish causation or operational guidance for claims management.

## Provenance
Evolved skill learned in run `run_012` (condition `skill_learning`) after task T2 (task index 1) from feedback ids T2-caveat_descriptive. Evaluation score total at proposal time: 3.87. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T4.
