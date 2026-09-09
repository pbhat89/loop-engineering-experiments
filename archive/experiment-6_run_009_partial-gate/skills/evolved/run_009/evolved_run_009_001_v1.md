---
skill_id: evolved_run_009_001
name: test_composite_and_single_column_candidate_keys_for_uniquene
version: 1
status: active
kind: evolved
created_after_task: T1
created_after_task_index: 0
source_feedback_ids: [T1-candidate_keys]
created_at: "2026-09-09T02:24:15+00:00"
reuse_count: 0
tags: [data_quality, keys, uniqueness, cardinality]
applicable_task_ids: [T3, T7]
run_id: run_009
condition: skill_learning
---

# Test Composite and Single-Column Candidate Keys for Uniqueness

## Trigger
When validating natural keys in a table where the true key might be either a single column or a composite of multiple columns.

## Objective
Systematically test both single-column and composite-key candidates to determine which is the actual natural key for a table, ensuring data integrity and trustworthy relationships for joins.

## Procedure
1. Identify all candidate keys for the table under analysis—both single-column keys (e.g., member_id) and plausible composite keys (e.g., member_id + therapeutic_class).
2. Run a uniqueness check for each candidate key: calculate the row count and the count of distinct values for the key column(s).
3. Record n_rows, n_unique, duplicate_rows, and is_candidate_key (true if n_unique equals n_rows) for each candidate.
4. Compare results across all candidates to determine which key or keys qualify as true natural keys.
5. Document all candidate key results in metrics—not just the one that passed—to support downstream join validation and identify potential data quality issues.

## Required checks
- All candidate keys are tested, including both single-column and composite combinations.
- For each key tested, n_rows, n_unique, duplicate_rows, and is_candidate_key are recorded.
- Comparison across candidate keys is documented to explain which is the true natural key.

## Expected artifacts
- Metrics documenting the uniqueness status and cardinality of each candidate key.

## Failure modes
- Testing only single-column keys while overlooking composite-key candidates, missing the true natural key.
- Assuming a key is unique without running the test, leading to undetected duplicates.
- Testing all candidates but reporting only the passing key, hiding evidence about the table structure.

## Example
In a claims adherence table with columns (member_id, therapeutic_class, pdc, mpr, adherence_flag), both member_id alone and the composite (member_id + therapeutic_class) are plausible keys. Testing both reveals whether each member-class pair is unique or whether member_id alone serves as the true natural key.

## Provenance
Evolved skill learned in run `run_009` (condition `skill_learning`) after task T1 (task index 0) from feedback ids T1-candidate_keys. Evaluation score total at proposal time: 3.69. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T3, T7.
