---
skill_id: evolved_run_011_004
name: complete_source_citation_in_executive_communication
version: 1
status: active
kind: evolved
created_after_task: T8
created_after_task_index: 5
source_feedback_ids: [T8-cite_artifacts, T8-all_numbers_cited]
created_at: "2026-09-09T03:23:02+00:00"
reuse_count: 0
tags: [executive_communication, reproducibility, traceability, citations]
applicable_task_ids: []
run_id: run_011
condition: skill_learning
---

# Complete source citation in executive communication

## Trigger
When writing an executive brief or stakeholder communication that presents numeric findings from claims analysis, ensure all numeric statements are traced to their sources.

## Objective
Establish complete source traceability in executive communications by requiring that every numeric statement carries a source citation, supporting reproducibility, stakeholder confidence, and findings credibility.

## Procedure
1. Before generating the executive communication, identify all components and parameters that control citation behavior (e.g., cite_artifacts in brief_sections).
2. Enable the citation mechanism in the relevant communication component to automatically attach source references to numeric statements.
3. Generate the executive communication and collect all numeric statements (percentages, rates, counts, costs, aggregated metrics).
4. Verify that each numeric statement includes a [source: <path>] citation pointing to the originating artifact or metrics key.
5. Validate that the communication output metadata shows cited_statements equals total_numeric_statements (100% citation coverage).
6. Document the citation coverage in accompanying reports or metadata so stakeholders understand all figures are sourced and independently verifiable.

## Required checks
- Every numeric statement in the executive communication carries a source citation
- Citation count equals the total count of numeric statements in the output
- All cited source paths reference valid artifacts or metrics keys from upstream tasks
- Citation-enabling parameter is explicitly configured in the communication component

## Expected artifacts
- executive_brief.md or equivalent stakeholder communication
- findings.json or metrics artifact with source_path for each extracted metric

## Failure modes
- Numeric statements appear without source citations, reducing transparency and stakeholder confidence
- Partial citation coverage creates inconsistency between cited and uncited statements
- Missing source information prevents leadership from independently verifying findings or drilling into methodology

## Example
When composing an executive brief that synthesizes findings from multiple upstream analyses, enable cite_artifacts=true in the brief_sections and write_report components. This ensures that numeric statements (e.g., 'denial rate X% [source: denial_analysis/metrics.json]', 'model accuracy Y% [source: model_evaluation/metrics.json]') automatically carry their source citations, achieving 100% traceability and enabling stakeholders to independently verify every figure in the communication.

## Provenance
Evolved skill learned in run `run_011` (condition `skill_learning`) after task T8 (task index 5) from feedback ids T8-cite_artifacts, T8-all_numbers_cited. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: none.
