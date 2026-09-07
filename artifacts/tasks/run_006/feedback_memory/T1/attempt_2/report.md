# T1 — Dataset reconnaissance

## Summary

Task T1 (Dataset reconnaissance) for run `run_006` / condition `feedback_memory`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: members (500 rows), providers (150 rows), medical_claims (12845 rows), pharmacy_claims (18310 rows), adherence (10627 rows).

## Results

### load_tables

- members: 500 rows, 44 columns [source: metrics.json#tables]
- providers: 150 rows, 7 columns [source: metrics.json#tables]
- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]
- pharmacy_claims: 18310 rows, 35 columns [source: metrics.json#tables]
- adherence: 10627 rows, 7 columns [source: metrics.json#tables]

### schema_summary

- members: 500 rows, 44 columns, dtypes {'float64': 1, 'int64': 32, 'str': 11} [source: metrics.json#schema]
- providers: 150 rows, 7 columns, dtypes {'str': 7} [source: metrics.json#schema]
- medical_claims: 12845 rows, 54 columns, dtypes {'float64': 8, 'int64': 14, 'str': 32} [source: metrics.json#schema]
- pharmacy_claims: 18310 rows, 35 columns, dtypes {'float64': 8, 'int64': 10, 'str': 17} [source: metrics.json#schema]
- adherence: 10627 rows, 7 columns, dtypes {'float64': 2, 'int64': 3, 'str': 2} [source: metrics.json#schema]

### missingness

- members: null cells share (all columns); all-null columns: none: 2 / 22000 = 0.000091 [source: metrics.json#missingness]
- providers: null cells share (all columns); all-null columns: none: 0 / 1050 = 0.000000 [source: metrics.json#missingness]
- medical_claims: null cells share (all columns); all-null columns: ['dx3', 'dx4', 'dx5', 'modifier1', 'modifier2', 'denial_reason_desc', 'auth_number']: 164369 / 693630 = 0.236969 [source: metrics.json#missingness]
- pharmacy_claims: null cells share (all columns); all-null columns: none: 0 / 640850 = 0.000000 [source: metrics.json#missingness]
- adherence: null cells share (all columns); all-null columns: none: 0 / 74389 = 0.000000 [source: metrics.json#missingness]

### duplicate_check

- medical_claims.claim_id: duplicate rows (candidate key: True): 0 / 12845 = 0.000000 [source: metrics.json#duplicates]
- pharmacy_claims.rx_claim_id: duplicate rows (candidate key: True): 0 / 18310 = 0.000000 [source: metrics.json#duplicates]
- members.member_id: duplicate rows (candidate key: True): 0 / 500 = 0.000000 [source: metrics.json#duplicates]
- providers.provider_npi: duplicate rows (candidate key: True): 0 / 150 = 0.000000 [source: metrics.json#duplicates]
- adherence.member_id: duplicate rows (candidate key: False): 10127 / 10627 = 0.952950 [source: metrics.json#duplicates]
- adherence.member_id+therapeutic_class: duplicate rows (candidate key: True): 0 / 10627 = 0.000000 [source: metrics.json#duplicates]

### date_ranges

- medical_claims.service_date_from: 2021-01-01 … 2023-12-31, unparseable rows: 0 [source: metrics.json#date_ranges]
- medical_claims.service_date_to: 2021-01-01 … 2024-01-09, unparseable rows: 0 [source: metrics.json#date_ranges]
- medical_claims.adjudication_date: 2021-01-08 … 2024-02-11, unparseable rows: 0 [source: metrics.json#date_ranges]
- pharmacy_claims.fill_date: 2021-01-01 … 2023-12-31, unparseable rows: 0 [source: metrics.json#date_ranges]
- pharmacy_claims.paid_date: 2021-01-02 … 2024-01-04, unparseable rows: 0 [source: metrics.json#date_ranges]
- members.enrollment_start: 2020-01-03 … 2021-01-01, unparseable rows: 0 [source: metrics.json#date_ranges]
- members.enrollment_end: 2023-12-31 … 2023-12-31, unparseable rows: 0 [source: metrics.json#date_ranges]
- medical_claims consistency — adjudication_before_service_end: 36 [source: metrics.json#date_consistency]
- medical_claims consistency — service_end_before_start: 0 [source: metrics.json#date_consistency]

### join_check

- medical_claims.member_id->members.member_id: many_to_one, unmatched left rows: 0 / 12845 = 0.000000 [source: metrics.json#join_check]
- medical_claims.rendering_npi->providers.provider_npi: many_to_one, unmatched left rows: 0 / 12845 = 0.000000 [source: metrics.json#join_check]
- medical_claims.billing_npi->providers.provider_npi: many_to_one, unmatched left rows: 0 / 12845 = 0.000000 [source: metrics.json#join_check]
- pharmacy_claims.member_id->members.member_id: many_to_one, unmatched left rows: 0 / 18310 = 0.000000 [source: metrics.json#join_check]
- pharmacy_claims.pharmacy_npi->providers.provider_npi: no_match, unmatched left rows: 18310 / 18310 = 1.000000 [source: metrics.json#join_check]
- adherence.member_id->members.member_id: many_to_one, unmatched left rows: 0 / 10627 = 0.000000 [source: metrics.json#join_check]

## Artifacts

- `artifacts/tasks/run_006/feedback_memory/T1/attempt_2/data_contract.json`
- `artifacts/tasks/run_006/feedback_memory/T1/attempt_2/missingness.csv`
- `artifacts/tasks/run_006/feedback_memory/T1/attempt_2/metrics.json`
- `artifacts/tasks/run_006/feedback_memory/T1/attempt_2/report.md`

## Caveats

- **descriptive_only**: The results are descriptive summaries; they estimate no effects and support no inference.
- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.

## Method

- Seed: 42; plan sha256: `f70a903d667c29e4b492778aeb9e75ab0e86bc52088198ba77e4db8cdfb0ba3d`.
- Components (canonical order): load_tables, schema_summary, missingness, duplicate_check, date_ranges, join_check, write_report.
- `load_tables` params: `{}`
- `schema_summary` params: `{}`
- `missingness` params: `{'scope': 'all_columns'}`
- `duplicate_check` params: `{'keys': ['medical_claims.claim_id', 'pharmacy_claims.rx_claim_id', 'members.member_id', 'providers.provider_npi', 'adherence.member_id', 'adherence.member_id+therapeutic_class']}`
- `date_ranges` params: `{'columns': ['medical_claims.service_date_from', 'medical_claims.service_date_to', 'medical_claims.adjudication_date', 'pharmacy_claims.fill_date', 'pharmacy_claims.paid_date', 'members.enrollment_start', 'members.enrollment_end'], 'consistency_checks': True}`
- `join_check` params: `{'pairs': ['medical_claims.member_id->members.member_id', 'medical_claims.rendering_npi->providers.provider_npi', 'medical_claims.billing_npi->providers.provider_npi', 'pharmacy_claims.member_id->members.member_id', 'pharmacy_claims.pharmacy_npi->providers.provider_npi', 'adherence.member_id->members.member_id']}`
- `write_report` params: `{'caveats': ['descriptive_only', 'synthetic_data', 'sample_preview'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['descriptive_only', 'synthetic_data', 'sample_preview'].
