---
skill_id: foundational_002
name: safe_claims_joins
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [joins, cardinality, keys, unmatched, duplicates, relationships, data_contract, providers, members]
applicable_task_ids: []
---

# Safe joins across claims tables

## Trigger
Use whenever two or more tables are combined — claims to members, providers, policies, or denial-code lookups — or whenever a metric is computed on a joined frame rather than a single source table. Use it also when row counts change unexpectedly between analysis steps.

## Objective
Guarantee that a join neither multiplies nor drops claims silently: the join key is understood, the cardinality is stated, row counts are compared before and after, and unmatched records are counted and handled by a written rule.

## Procedure
1. Name the join key(s) on each side and confirm, from the data contract, whether each side is unique on that key; write the expected cardinality (one-to-one, many-to-one, many-to-many).
2. Count rows on both sides before the join, and count distinct key values on both sides.
3. Count keys present on the left but not the right and vice versa; report each as a count and a share of the respective side's rows.
4. Choose the join type deliberately (left join to keep every claim; inner join only when losing unmatched rows is intended) and state why.
5. Perform the join and count rows after it; for a many-to-one join the row count must equal the left row count, otherwise the lookup side has duplicate keys.
6. If duplicates exist on the lookup side, resolve them with a written rule (deduplicate on a documented column, take the latest effective date, or aggregate) before joining — never after.
7. Re-check duplicate `claim_id` values after the join and confirm that amount totals (billed, allowed, paid) are unchanged by the join.
8. Record the join audit (keys, cardinality, counts before and after, unmatched counts, rule applied) in the artifacts and cite it wherever the joined data is used.

## Required checks
- Expected cardinality is stated and verified by distinct-key counts, not assumed.
- Row count after a many-to-one join equals the left row count.
- Unmatched counts are reported on both sides with denominators.
- Any deduplication rule is written down and applied before the join.
- Financial totals are identical before and after the join.

## Expected artifacts
- A join audit table (left table, right table, key, cardinality, rows before, rows after, unmatched left, unmatched right, rule).
- A note in the report on how unmatched records were handled.

## Failure modes
- Joining claims to a provider table whose provider key repeats across effective-date rows, doubling claim counts and paid amounts.
- Using an inner join by default and losing denied claims whose provider record is missing.
- Reporting an unmatched count without saying which side and which denominator.
- Joining on a formatted string key (leading zeros, letter case) that differs between files.

## Example
Claims (12,800 rows, unique on `claim_id`) are joined to providers (1,200 rows) on `provider_id`. Distinct providers: 1,200 on the right, 1,180 referenced on the left; 0 claims lack a provider row (0.0% of 12,800). The left join preserves 12,800 rows and the total paid amount is unchanged, so the join is accepted as many-to-one.

## Provenance
Foundational skill authored by the skill-system engineer from the project brief (join cardinality, unique keys, row counts before/after joins, unmatched records, duplicate claim ids). Not derived from any task run; no feedback ids.
