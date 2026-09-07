---
skill_id: evolved_stub_001_003
name: missing_denominators_communication
version: 1
status: active
kind: evolved
created_after_task: T3
created_after_task_index: 2
source_feedback_ids: [T3-show_denominators]
created_at: "2026-09-06T17:12:40+00:00"
reuse_count: 0
tags: [cardinality, communication, denominators, group_comparison, joins, network, providers, rates, small_groups, specialty]
applicable_task_ids: [T4, T5]
run_id: stub_001
condition: skill_learning
---

# Missing denominators communication

## Trigger
When a task involves write_report on claims data.

## Objective
Print every rate as numerator / denominator = rate in the report (write_report show_denominators true).

## Procedure
1. Print every rate as numerator / denominator = rate in the report (write_report show_denominators true).
2. Apply catalogue components: write_report.
3. Set parameters: write_report.show_denominators=True.

## Required checks
- Plan includes write_report

## Expected artifacts
- group_comparison.csv
- group_comparison.png
- provider_ranking.csv

## Failure modes
- Applying the convention without stating it in the report.

## Example
Fixture-generated from T3-show_denominators on T3.

## Provenance
Evolved skill learned in run `stub_001` (condition `skill_learning`) after task T3 (task index 2) from feedback ids T3-show_denominators. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-fixture` via provider mode `stub` (model `deterministic-fixture-v1`). Declared applicable task ids: T4, T5.
