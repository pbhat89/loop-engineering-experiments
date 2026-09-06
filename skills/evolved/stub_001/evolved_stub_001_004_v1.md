---
skill_id: evolved_stub_001_004
name: missing_caveat_communication
version: 1
status: active
kind: evolved
created_after_task: T4
created_after_task_index: 3
source_feedback_ids: [T4-caveat_synthetic]
created_at: "2026-09-06T17:12:44+00:00"
reuse_count: 0
tags: [communication, denial_codes, denials, denominators, missingness, rates, segments, small_groups]
applicable_task_ids: [T5, T6, T7, T8]
run_id: stub_001
condition: skill_learning
---

# Missing caveat communication

## Trigger
When a task involves write_report on claims data.

## Objective
State in the report that the data is synthetic (add the synthetic_data caveat).

## Procedure
1. State in the report that the data is synthetic (add the synthetic_data caveat).
2. Apply catalogue components: write_report.
3. Set parameters: write_report.caveats=['synthetic_data', 'small_groups'].

## Required checks
- Plan includes write_report

## Expected artifacts
- denial_code_ranking.csv
- denial_rates_by_segment.csv
- denial_rate_by_segment.png

## Failure modes
- Applying the convention without stating it in the report.

## Example
Fixture-generated from T4-caveat_synthetic on T4.

## Provenance
Evolved skill learned in run `stub_001` (condition `skill_learning`) after task T4 (task index 3) from feedback ids T4-caveat_synthetic. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-fixture` via provider mode `stub` (model `deterministic-fixture-v1`). Declared applicable task ids: T5, T6, T7, T8.
