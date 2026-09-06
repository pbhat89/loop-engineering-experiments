# T1 — Dataset reconnaissance

## Summary

Task T1 (Dataset reconnaissance) for run `stub_001` / condition `skill_learning`, attempt 1: status **ok**; 5 component(s) executed, 0 failed, 0 error(s) recorded.
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

### date_ranges

- medical_claims.service_date_from: 2021-01-01 … 2023-12-31, unparseable rows: 0

## Artifacts

- `artifacts/tasks/stub_001/skill_learning/T1/attempt_1/data_contract.json`
- `artifacts/tasks/stub_001/skill_learning/T1/attempt_1/missingness.csv`
- `artifacts/tasks/stub_001/skill_learning/T1/attempt_1/metrics.json`
- `artifacts/tasks/stub_001/skill_learning/T1/attempt_1/report.md`

## Method

- Seed: 42; plan sha256: `36ac0f4531e02c09def8e23e4de23c4fd912e96cb4ab86e99359bc409646d1ce`.
- Components (canonical order): load_tables, schema_summary, missingness, date_ranges, write_report.
- `load_tables` params: `{}`
- `schema_summary` params: `{}`
- `missingness` params: `{'scope': 'top_10'}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- `date_ranges` params: `{'columns': ['medical_claims.service_date_from'], 'consistency_checks': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
