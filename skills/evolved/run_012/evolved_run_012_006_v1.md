---
skill_id: evolved_run_012_006
name: enforce_citation_discipline_in_executive_communication
version: 1
status: active
kind: evolved
created_after_task: T8
created_after_task_index: 5
source_feedback_ids: [T8-cite_artifacts, T8-all_numbers_cited]
created_at: "2026-09-09T04:01:16+00:00"
reuse_count: 0
tags: [communication, executive_brief, reproducibility, traceability, citations]
applicable_task_ids: []
run_id: run_012
condition: skill_learning
---

# Enforce citation discipline in executive communication

## Trigger
When composing an executive brief, executive summary, or stakeholder communication that includes numeric findings, metrics, or comparative statements.

## Objective
Ensure every numeric statement in executive-level communication carries a source citation to the artifact or metrics key from which it derives, establishing reproducibility and protecting the credibility of analytical findings.

## Procedure
1. Before finalizing the communication, conduct a complete review to identify all numeric statements, including percentages, rates, counts, averages, comparisons, and ranking statements.
2. For each numeric statement identified, append a source citation in the format [source: <artifact_path_or_metrics_key>] to link the claim to the underlying data or calculation basis.
3. Verify that every cited source is accessible, accurate, and contains the exact value or calculation supporting the statement.
4. In the output metrics, ensure that n_cited_statements equals n_numeric_statements, confirming complete citation coverage across all numeric claims.

## Required checks
- Every numeric statement in the communication has an associated [source: ...] citation.
- The n_cited_statements metric equals n_numeric_statements.
- Each cited source is accessible and supports the numeric claim.

## Expected artifacts
- executive_brief.md (with citations)
- findings.json or metrics.json

## Failure modes
- Uncited numeric statements undermine credibility and make verification difficult.
- Incomplete citation coverage masks evidentiary gaps and reduces decision-maker confidence.
- Citations pointing to inaccessible or incorrect sources create confusion and erode trust.

## Example
Before: 'Denial rates for out-of-network ED claims were 8.5%, compared to 4.2% for in-network.' After: 'Denial rates for out-of-network ED claims were 8.5% [source: T2/metrics.json:denial_rate_oon_ed], compared to 4.2% for in-network [source: T2/metrics.json:denial_rate_in_ed].' Each numeric claim is now verifiable; stakeholders can inspect the source without ambiguity.

## Provenance
Evolved skill learned in run `run_012` (condition `skill_learning`) after task T8 (task index 5) from feedback ids T8-cite_artifacts, T8-all_numbers_cited. Evaluation score total at proposal time: 3.64. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: none.
