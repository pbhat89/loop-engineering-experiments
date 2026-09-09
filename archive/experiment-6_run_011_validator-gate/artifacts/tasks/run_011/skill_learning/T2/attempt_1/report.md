# T2 — Claims portfolio description

## Summary

Task T2 (Claims portfolio description) for run `run_011` / condition `skill_learning`, attempt 1: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns [source: metrics.json#tables]

### claim_volume

- Total claims: 12845 [source: metrics.json#claim_volume.total_claims]
- claim_status = Paid: share of claims: 10511 / 12845 = 0.818295 [source: metrics.json#claim_volume.by.claim_status]
- claim_status = Denied: share of claims: 1286 / 12845 = 0.100117 [source: metrics.json#claim_volume.by.claim_status]
- claim_status = Adjusted: share of claims: 542 / 12845 = 0.042195 [source: metrics.json#claim_volume.by.claim_status]
- claim_status = Pended: share of claims: 506 / 12845 = 0.039393 [source: metrics.json#claim_volume.by.claim_status]

### denial_rate

- Denial rate (denominator: all_claims): 1286 / 12845 = 0.100117 [source: metrics.json#denial_rate]

### fraud_prevalence

- Fraud prevalence (denominator: all_claims): 647 / 12845 = 0.050370 [source: metrics.json#fraud_prevalence]

### financial_summary

- billed_amount: sum: 21254208.810000 [source: metrics.json#financial_summary]
- billed_amount: mean: 1654.667872 [source: metrics.json#financial_summary]
- allowed_amount: sum: 12175223.450000 [source: metrics.json#financial_summary]
- allowed_amount: mean: 947.857022 [source: metrics.json#financial_summary]
- paid_amount: sum: 9783415.770000 [source: metrics.json#financial_summary]
- paid_amount: mean: 761.651675 [source: metrics.json#financial_summary]

### monthly_trend

- Date column adjudication_date: months covered: 38 [source: metrics.json#monthly_trend]
- Range 2021-01 … 2024-02; unparseable dates: 0 [source: metrics.json#monthly_trend.unparseable_dates]
- claim_count: mean per month: 338.026316 [source: artifacts/tasks/run_011/skill_learning/T2/attempt_1/monthly_trend.csv]

## Artifacts

- `artifacts/tasks/run_011/skill_learning/T2/attempt_1/claims_status_distribution.png`
- `artifacts/tasks/run_011/skill_learning/T2/attempt_1/financial_summary.csv`
- `artifacts/tasks/run_011/skill_learning/T2/attempt_1/monthly_trend.csv`
- `artifacts/tasks/run_011/skill_learning/T2/attempt_1/monthly_claim_volume.png`
- `artifacts/tasks/run_011/skill_learning/T2/attempt_1/metrics.json`
- `artifacts/tasks/run_011/skill_learning/T2/attempt_1/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `35f8cade9695f749c3365b12bed543db8a0ede7abe660a389d31185157859e36`.
- Components (canonical order): load_tables, claim_volume, denial_rate, fraud_prevalence, financial_summary, monthly_trend, write_report.
- `load_tables` params: `{}`
- `claim_volume` params: `{'by': ['claim_status'], 'figure': True}`
- `denial_rate` params: `{'denominator': 'all_claims'}`
- `fraud_prevalence` params: `{'denominator': 'all_claims'}`
- `financial_summary` params: `{'amount_columns': ['billed_amount', 'allowed_amount', 'paid_amount'], 'statistics': 'sum_mean'}`
- `monthly_trend` params: `{'date_column': 'adjudication_date', 'metrics': ['claim_count']}`
- `write_report` params: `{'caveats': ['synthetic_data'], 'show_denominators': True, 'cite_artifacts': True}`
- Report options: show_denominators=True, cite_artifacts=True, caveats=['synthetic_data'].
