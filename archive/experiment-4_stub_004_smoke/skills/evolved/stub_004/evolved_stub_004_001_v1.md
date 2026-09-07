---
skill_id: evolved_stub_004_001
name: incomplete_scope_correctness
version: 1
status: active
kind: evolved
created_after_task: T1
created_after_task_index: 0
source_feedback_ids: [T1-candidate_keys]
created_at: "2026-09-07T15:32:07+00:00"
reuse_count: 0
tags: [cardinality, correctness, data_contract, data_quality, dates, duplicates, joins, keys, missingness, schema]
applicable_task_ids: [T3, T7]
run_id: stub_004
condition: skill_learning
---

# Incomplete scope correctness

## Trigger
When a task involves duplicate_check on claims data.

## Objective
Run the duplicate check for every natural key including the composite adherence key (member_id+therapeutic_class) and report n_rows, n_unique and is_candidate_key for each.

## Procedure
1. Run the duplicate check for every natural key including the composite adherence key (member_id+therapeutic_class) and report n_rows, n_unique and is_candidate_key for each.
2. Apply catalogue components: duplicate_check.
3. Set parameters: duplicate_check.keys=['medical_claims.claim_id', 'pharmacy_claims.rx_claim_id', 'members.member_id', 'providers.provider_npi', 'adherence.member_id', 'adherence.member_id+therapeutic_class'].

## Required checks
- Plan includes duplicate_check

## Expected artifacts
- data_contract.json
- missingness.csv
- report.md

## Failure modes
- Applying the convention without stating it in the report.

## Example
Fixture-generated from T1-candidate_keys on T1.

## Provenance
Evolved skill learned in run `stub_004` (condition `skill_learning`) after task T1 (task index 0) from feedback ids T1-candidate_keys. Evaluation score total at proposal time: 3.87. Proposed by operator `deterministic-fixture` via provider mode `stub` (model `deterministic-fixture-v1`). Declared applicable task ids: T3, T7.
