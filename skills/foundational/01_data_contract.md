---
skill_id: foundational_001
name: data_contract
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [data_contract, schema, keys, identifiers, missingness, duplicates, date_ranges, reconnaissance, quality, assumptions]
applicable_task_ids: []
---

# Data contract before analysis

## Trigger
Use at the start of any task that reads a dataset file for the first time, whenever a new table, column, or data snapshot enters an analysis, and before any join, rate, model, or brief is produced from it. Use it again when a later result looks implausible and the inputs need to be re-verified.

## Objective
Establish an explicit, written contract for each input table — what rows it holds, which columns exist with which types, which identifiers are unique, which dates bound the data, how much is missing, and what is assumed — so that every downstream number has a documented, checkable foundation.

## Procedure
1. Load each file separately and record its path, byte size, and content hash from the manifest, plus the row count and column count.
2. For every column record the observed type, the count and share of missing values (with the row count as denominator), the number of distinct values, and a few short sample values.
3. Identify candidate identifier columns: any column whose distinct count equals the row count is a candidate primary key; report duplicate counts for the expected key (for claims usually `claim_id`) and decide whether duplicates are true repeats or legitimate multi-line records.
4. For every date-like column parse it, record the minimum and maximum, the count that failed to parse, and any values outside the plausible service window; note which date column defines "the period" for trend work.
5. Check target availability and type: if a label such as `fraud_label` or a status field exists, record its distinct values, prevalence with denominator, and whether any column is derived from the label (a leakage candidate, e.g. `fraud_pattern_type`).
6. Check cross-file relationships: for each foreign key (member, provider, policy) count matched and unmatched rows on both sides and state the expected cardinality.
7. Write the assumptions list: units of amounts, currency, whether amounts are per line or per claim, which status values count as adjudicated, and anything inferred rather than documented.
8. Save the contract as a machine-readable file plus a short human-readable data-quality report, and cite it from every later artifact that depends on it.

## Required checks
- Row and column counts are stated for every table and match the manifest.
- Every missingness figure is a count and a share with the row count as denominator.
- The chosen key is either proven unique or the duplicate-handling rule is written down.
- Every date column has a parsed min/max and a parse-failure count.
- Label-derived or post-outcome columns are listed explicitly as leakage candidates.
- Every assumption is labelled as documented or inferred.

## Expected artifacts
- A data-contract JSON (tables, columns, types, keys, date ranges, missingness, relationships).
- A data-quality report in Markdown summarising issues, duplicates, and assumptions.
- A missingness table (column, missing count, missing share, denominator).

## Failure modes
- Treating a column as unique because it "looks like an ID" without counting distinct values.
- Reporting missingness as a bare count or a percentage without its denominator.
- Silently coercing unparseable dates to null and then computing trends on the remainder.
- Assuming amount columns share units, or that billed ≥ allowed ≥ paid, without checking.
- Skipping the contract on a "familiar" file after the snapshot changed.

## Example
A synthetic claims table has 12,800 rows and 31 columns. `claim_id` has 12,800 distinct values (unique key); `denial_code` is missing in 9,050 rows (70.7% of 12,800), which is expected because only denied claims carry a code; `service_date_from` parses fully and spans 2021-01-01 to 2023-12-31; `fraud_pattern_type` is populated only when `fraud_label` = 1 and is therefore recorded as a leakage candidate to exclude from any model.

## Provenance
Foundational skill authored by the skill-system engineer from the project brief (dataset reconnaissance: schema, types, row counts, identifiers, date ranges, missingness, duplicates, target availability, assumptions). Not derived from any task run; no feedback ids.
