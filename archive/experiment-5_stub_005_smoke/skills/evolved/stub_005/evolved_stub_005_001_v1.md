---
skill_id: evolved_stub_005_001
name: wrong_denominator_statistical_discipline
version: 1
status: active
kind: evolved
created_after_task: T10
created_after_task_index: 7
source_feedback_ids: [T10-group_denominator]
created_at: "2026-09-08T07:25:47+00:00"
reuse_count: 0
tags: [denominators, financial, group_comparison, joins, providers, rates, small_groups, specialty, spend, statistical_discipline]
applicable_task_ids: [T5, T6]
run_id: stub_005
condition: skill_learning
---

# Wrong denominator statistical discipline

## Trigger
When a task involves group_comparison on claims data.

## Objective
Use adjudicated claims as the per-specialty denial-rate denominator and record the choice.

## Procedure
1. Use adjudicated claims as the per-specialty denial-rate denominator and record the choice.
2. Apply catalogue components: group_comparison.
3. Set parameters: group_comparison.denominator=adjudicated_claims.

## Required checks
- Plan includes group_comparison

## Expected artifacts
- group_comparison.csv
- group_comparison.png
- provider_ranking.csv

## Failure modes
- Applying the convention without stating it in the report.

## Example
Fixture-generated from T10-group_denominator on T10.

## Provenance
Evolved skill learned in run `stub_005` (condition `skill_learning`) after task T10 (task index 7) from feedback ids T10-group_denominator. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-fixture` via provider mode `stub` (model `deterministic-fixture-v1`). Declared applicable task ids: T5, T6.
