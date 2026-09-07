---
skill_id: evolved_run_002_001
name: conventions_missingness_scope_duplicate_check_keys_date_rang
version: 1
status: active
kind: evolved
created_after_task: T1
created_after_task_index: 0
source_feedback_ids: [T1-missingness_scope, T1-candidate_keys, T1-duplicate_check_executed, T1-date_ranges, T1-date_consistency, T1-join_cardinality, T1-join_check_executed, T1-caveat_synthetic, T1-caveat_sample_preview]
created_at: "2026-09-07T00:24:08+00:00"
reuse_count: 0
tags: [data_contract, schema, keys, missingness, duplicates, dates, joins, cardinality, data_quality, denials, denial_codes, communication, caveats, descriptive, rates, modeling, fraud, providers]
applicable_task_ids: [T2, T3, T4, T5, T6, T7, T8]
run_id: run_002
condition: skill_learning
---

# Conventions missingness scope duplicate check keys date rang

## Trigger
The task catalogue offers caveats, columns, consistency_checks, date_ranges, duplicate_check, join_check, keys, missingness, pairs, scope, write_report.

## Objective
House conventions learned from evaluator feedback: component:missingness; param:scope=all_columns; component:duplicate_check; list:keys+=medical_claims.claim_id; list:keys+=pharmacy_claims.rx_claim_id; list:keys+=members.member_id; list:keys+=providers.provider_npi; list:keys+=adherence.member_id; list:keys+=adherence.member_id+therapeutic_class; component:date_ranges; param:consistency_checks=true; list:columns+=medical_claims.service_date_from; list:columns+=medical_claims.service_date_to; list:columns+=medical_claims.adjudication_date; component:join_check; list:pairs+=medical_claims.member_id->members.member_id; list:pairs+=medical_claims.rendering_npi->providers.provider_npi; list:pairs+=medical_claims.billing_npi->providers.provider_npi; list:pairs+=pharmacy_claims.member_id->members.member_id; list:pairs+=pharmacy_claims.pharmacy_npi->providers.provider_npi; list:pairs+=adherence.member_id->members.member_id; component:write_report; list:caveats+=synthetic_data; list:caveats+=sample_preview

## Procedure
1. Include the `missingness` component.
2. `scope` = `all_columns` on any component that has it.
3. Include the `duplicate_check` component.
4. Add `medical_claims.claim_id` to any `keys` list.
5. Add `pharmacy_claims.rx_claim_id` to any `keys` list.
6. Add `members.member_id` to any `keys` list.
7. Add `providers.provider_npi` to any `keys` list.
8. Add `adherence.member_id` to any `keys` list.
9. Add `adherence.member_id+therapeutic_class` to any `keys` list.
10. Include the `date_ranges` component.
11. `consistency_checks` = `true` on any component that has it.
12. Add `medical_claims.service_date_from` to any `columns` list.
13. Add `medical_claims.service_date_to` to any `columns` list.
14. Add `medical_claims.adjudication_date` to any `columns` list.
15. Include the `join_check` component.
16. Add `medical_claims.member_id->members.member_id` to any `pairs` list.
17. Add `medical_claims.rendering_npi->providers.provider_npi` to any `pairs` list.
18. Add `medical_claims.billing_npi->providers.provider_npi` to any `pairs` list.
19. Add `pharmacy_claims.member_id->members.member_id` to any `pairs` list.
20. Add `pharmacy_claims.pharmacy_npi->providers.provider_npi` to any `pairs` list.
21. Add `adherence.member_id->members.member_id` to any `pairs` list.
22. Include the `write_report` component.
23. Add `synthetic_data` to any `caveats` list.
24. Add `sample_preview` to any `caveats` list.

## Required checks
- component:missingness
- param:scope=all_columns
- component:duplicate_check
- list:keys+=medical_claims.claim_id
- list:keys+=pharmacy_claims.rx_claim_id
- list:keys+=members.member_id
- list:keys+=providers.provider_npi
- list:keys+=adherence.member_id
- list:keys+=adherence.member_id+therapeutic_class
- component:date_ranges
- param:consistency_checks=true
- list:columns+=medical_claims.service_date_from
- list:columns+=medical_claims.service_date_to
- list:columns+=medical_claims.adjudication_date
- component:join_check
- list:pairs+=medical_claims.member_id->members.member_id
- list:pairs+=medical_claims.rendering_npi->providers.provider_npi
- list:pairs+=medical_claims.billing_npi->providers.provider_npi
- list:pairs+=pharmacy_claims.member_id->members.member_id
- list:pairs+=pharmacy_claims.pharmacy_npi->providers.provider_npi
- list:pairs+=adherence.member_id->members.member_id
- component:write_report
- list:caveats+=synthetic_data
- list:caveats+=sample_preview

## Expected artifacts
- data_contract.json
- missingness.csv
- report.md

## Failure modes
- A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.
- List additions may name fields or pairs a later task does not load.

## Example
Include the `missingness` component.

## Provenance
Evolved skill learned in run `run_002` (condition `skill_learning`) after task T1 (task index 0) from feedback ids T1-missingness_scope, T1-candidate_keys, T1-duplicate_check_executed, T1-date_ranges, T1-date_consistency, T1-join_cardinality, T1-join_check_executed, T1-caveat_synthetic, T1-caveat_sample_preview. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-rule-learner` via provider mode `rule_learner` (model `rule-learner-v1`). Declared applicable task ids: T2, T3, T4, T5, T6, T7, T8.
