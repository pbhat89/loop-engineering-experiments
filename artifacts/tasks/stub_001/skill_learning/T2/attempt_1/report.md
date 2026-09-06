# T2 — Claims portfolio description

## Summary

Task T2 (Claims portfolio description) for run `stub_001` / condition `skill_learning`, attempt 1: status **ok**; 6 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### claim_volume

- Total claims: 12845
- claim_status = Paid: share of claims: 0.818295
- claim_status = Denied: share of claims: 0.100117
- claim_status = Adjusted: share of claims: 0.042195
- claim_status = Pended: share of claims: 0.039393

### denial_rate

- Denial rate (denominator: all_claims): 0.100117

### financial_summary

- paid_amount: sum: 9783415.770000
- paid_amount: mean: 761.651675

### monthly_trend

- Date column adjudication_date: months covered: 38
- Range 2021-01 … 2024-02; unparseable dates: 0
- claim_count: mean per month: 338.026316

## Artifacts

- `artifacts/tasks/stub_001/skill_learning/T2/attempt_1/claims_status_distribution.png`
- `artifacts/tasks/stub_001/skill_learning/T2/attempt_1/financial_summary.csv`
- `artifacts/tasks/stub_001/skill_learning/T2/attempt_1/monthly_trend.csv`
- `artifacts/tasks/stub_001/skill_learning/T2/attempt_1/monthly_claim_volume.png`
- `artifacts/tasks/stub_001/skill_learning/T2/attempt_1/metrics.json`
- `artifacts/tasks/stub_001/skill_learning/T2/attempt_1/report.md`

## Method

- Seed: 42; plan sha256: `73fc586c6cdc15fbd10af5a1f8d005a151f615e1b35f615a665c0c9652f80a5a`.
- Components (canonical order): load_tables, claim_volume, denial_rate, financial_summary, monthly_trend, write_report.
- `load_tables` params: `{}`
- `claim_volume` params: `{'by': ['claim_status'], 'figure': True}`
- `denial_rate` params: `{'denominator': 'all_claims'}`
- `financial_summary` params: `{'amount_columns': ['paid_amount'], 'statistics': 'sum_mean'}`
- `monthly_trend` params: `{'date_column': 'adjudication_date', 'metrics': ['claim_count']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
