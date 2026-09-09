---
skill_id: evolved_run_011_001
name: comprehensive_candidate_key_validation
version: 1
status: active
kind: evolved
created_after_task: T1
created_after_task_index: 0
source_feedback_ids: [T1-candidate_keys]
created_at: "2026-09-09T02:55:32+00:00"
reuse_count: 0
tags: [data_quality, keys, duplicates, identifier_integrity, data_contract]
applicable_task_ids: [T3, T7]
run_id: run_011
condition: skill_learning
---

# Comprehensive Candidate Key Validation

## Trigger
When performing data reconnaissance or quality checks on any dataset containing candidate keys, especially composite keys defined in the schema.

## Objective
Ensure complete and rigorous validation of all candidate keys (simple and composite) to verify identifier uniqueness and data integrity before downstream analysis.

## Procedure
1. Review the schema documentation and identify all candidate keys marked for each table, including both simple keys and composite keys.
2. For simple candidate keys, note each table.column (e.g., members.member_id).
3. For composite candidate keys, document the full composition using '+' notation (e.g., adherence.member_id+therapeutic_class).
4. Configure a duplicate_check component (or equivalent uniqueness validation) to test all identified candidate keys in a single pass.
5. Execute the validation and collect metrics for each key: n_rows, n_unique, duplicate_rows count, and is_candidate_key boolean flag.
6. Verify that is_candidate_key returns true for all keys declared as candidate in the schema.
7. Document any keys where is_candidate_key is false as data quality findings requiring investigation.
8. Include all results (not a subset) in the final data quality report or data contract.

## Required checks
- Every candidate key from the schema is tested (no omissions)
- Composite keys are tested alongside simple keys
- Results report n_unique versus n_rows for each key
- The is_candidate_key validation flag is present for every key tested

## Expected artifacts
- data_contract.json documenting all candidate keys
- Duplicate check results or uniqueness validation output covering all keys
- Data quality report section listing all candidate keys and their validation status

## Failure modes
- Composite keys omitted from validation, yielding incomplete confidence in identifier integrity
- Subset of keys tested but not all, creating false confidence in data quality
- Validation results not reported for all keys, obscuring data quality issues

## Example
For a dataset with members (key: member_id), claims (key: claim_id), and adherence records (composite key: member_id+therapeutic_class), test all three keys in one validation run and report n_unique for each to confirm uniqueness.

## Provenance
Evolved skill learned in run `run_011` (condition `skill_learning`) after task T1 (task index 0) from feedback ids T1-candidate_keys. Evaluation score total at proposal time: 4.0. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T7.
