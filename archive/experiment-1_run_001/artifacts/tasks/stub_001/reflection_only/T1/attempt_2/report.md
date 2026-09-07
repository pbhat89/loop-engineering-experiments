# T1 — Dataset reconnaissance

## Summary

Task T1 (Dataset reconnaissance) for run `stub_001` / condition `reflection_only`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: members (500 rows), providers (150 rows), medical_claims (12845 rows), pharmacy_claims (18310 rows), adherence (10627 rows).

## Results

### load_tables

- members: 500 rows, 44 columns
- providers: 150 rows, 7 columns
- medical_claims: 12845 rows, 54 columns
- pharmacy_claims: 18310 rows, 35 columns
- adherence: 10627 rows, 7 columns

### schema_summary

- members: 500 rows, 44 columns, dtypes {'float64': 1, 'int64': 32, 'str': 11}
- providers: 150 rows, 7 columns, dtypes {'str': 7}
- medical_claims: 12845 rows, 54 columns, dtypes {'float64': 8, 'int64': 14, 'str': 32}
- pharmacy_claims: 18310 rows, 35 columns, dtypes {'float64': 8, 'int64': 10, 'str': 17}
- adherence: 10627 rows, 7 columns, dtypes {'float64': 2, 'int64': 3, 'str': 2}

### missingness

- members: null cells share (all columns); all-null columns: none: 0.000091
- providers: null cells share (all columns); all-null columns: none: 0.000000
- medical_claims: null cells share (all columns); all-null columns: ['dx3', 'dx4', 'dx5', 'modifier1', 'modifier2', 'denial_reason_desc', 'auth_number']: 0.236969
- pharmacy_claims: null cells share (all columns); all-null columns: none: 0.000000
- adherence: null cells share (all columns); all-null columns: none: 0.000000

### duplicate_check

- medical_claims.claim_id: duplicate rows (candidate key: True): 0.000000
- pharmacy_claims.rx_claim_id: duplicate rows (candidate key: True): 0.000000
- members.member_id: duplicate rows (candidate key: True): 0.000000
- providers.provider_npi: duplicate rows (candidate key: True): 0.000000
- adherence.member_id: duplicate rows (candidate key: False): 0.952950
- adherence.member_id+therapeutic_class: duplicate rows (candidate key: True): 0.000000

### date_ranges

- medical_claims.service_date_from: 2021-01-01 … 2023-12-31, unparseable rows: 0
- medical_claims.service_date_to: 2021-01-01 … 2024-01-09, unparseable rows: 0
- medical_claims.adjudication_date: 2021-01-08 … 2024-02-11, unparseable rows: 0
- medical_claims consistency — adjudication_before_service_end: 36
- medical_claims consistency — service_end_before_start: 0

### join_check

- medical_claims.member_id->members.member_id: many_to_one, unmatched left rows: 0.000000
- medical_claims.rendering_npi->providers.provider_npi: many_to_one, unmatched left rows: 0.000000
- medical_claims.billing_npi->providers.provider_npi: many_to_one, unmatched left rows: 0.000000
- pharmacy_claims.member_id->members.member_id: many_to_one, unmatched left rows: 0.000000
- pharmacy_claims.pharmacy_npi->providers.provider_npi: no_match, unmatched left rows: 1.000000
- adherence.member_id->members.member_id: many_to_one, unmatched left rows: 0.000000

## Artifacts

- `artifacts/tasks/stub_001/reflection_only/T1/attempt_2/data_contract.json`
- `artifacts/tasks/stub_001/reflection_only/T1/attempt_2/missingness.csv`
- `artifacts/tasks/stub_001/reflection_only/T1/attempt_2/metrics.json`
- `artifacts/tasks/stub_001/reflection_only/T1/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.
- **sample_preview**: The data are a sample preview of the dataset; counts and distributions need not match the full release.

## Method

- Seed: 42; plan sha256: `6e31d66f2875b98a63065340c93405ef96ed81c360fd05af2749ef194ee99402`.
- Components (canonical order): load_tables, schema_summary, missingness, duplicate_check, date_ranges, join_check, write_report.
- `load_tables` params: `{}`
- `schema_summary` params: `{}`
- `missingness` params: `{'scope': 'all_columns'}`
- `write_report` params: `{'caveats': ['synthetic_data', 'sample_preview'], 'show_denominators': False, 'cite_artifacts': False}`
- `duplicate_check` params: `{'keys': ['medical_claims.claim_id', 'pharmacy_claims.rx_claim_id', 'members.member_id', 'providers.provider_npi', 'adherence.member_id', 'adherence.member_id+therapeutic_class']}`
- `date_ranges` params: `{'columns': ['medical_claims.service_date_from', 'medical_claims.service_date_to', 'medical_claims.adjudication_date'], 'consistency_checks': True}`
- `join_check` params: `{'pairs': ['medical_claims.member_id->members.member_id', 'medical_claims.rendering_npi->providers.provider_npi', 'medical_claims.billing_npi->providers.provider_npi', 'pharmacy_claims.member_id->members.member_id', 'pharmacy_claims.pharmacy_npi->providers.provider_npi', 'adherence.member_id->members.member_id']}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=['synthetic_data', 'sample_preview'].
