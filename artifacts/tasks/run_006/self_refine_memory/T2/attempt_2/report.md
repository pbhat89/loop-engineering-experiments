# T2 — Claims portfolio description

## Summary

Task T2 (Claims portfolio description) for run `run_006` / condition `self_refine_memory`, attempt 2: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
Tables: medical_claims (12845 rows).

## Results

### load_tables

- medical_claims: 12845 rows, 54 columns

### claim_volume

- Total claims: 12845
- claim_status = Paid: share of claims: 10511 / 12845 = 0.818295
- claim_status = Denied: share of claims: 1286 / 12845 = 0.100117
- claim_status = Adjusted: share of claims: 542 / 12845 = 0.042195
- claim_status = Pended: share of claims: 506 / 12845 = 0.039393

### denial_rate

- Denial rate (denominator: all_claims): 1286 / 12845 = 0.100117

### fraud_prevalence

- Fraud prevalence (denominator: all_claims): 647 / 12845 = 0.050370

### financial_summary

- billed_amount: sum: 21254208.810000
- billed_amount: mean: 1654.667872
- allowed_amount: sum: 12175223.450000
- allowed_amount: mean: 947.857022
- paid_amount: sum: 9783415.770000
- paid_amount: mean: 761.651675

### monthly_trend

- Date column adjudication_date: months covered: 38
- Range 2021-01 … 2024-02; unparseable dates: 0
- claim_count: mean per month: 338.026316

## Artifacts

- `artifacts/tasks/run_006/self_refine_memory/T2/attempt_2/claims_status_distribution.png`
- `artifacts/tasks/run_006/self_refine_memory/T2/attempt_2/financial_summary.csv`
- `artifacts/tasks/run_006/self_refine_memory/T2/attempt_2/monthly_trend.csv`
- `artifacts/tasks/run_006/self_refine_memory/T2/attempt_2/monthly_claim_volume.png`
- `artifacts/tasks/run_006/self_refine_memory/T2/attempt_2/metrics.json`
- `artifacts/tasks/run_006/self_refine_memory/T2/attempt_2/report.md`

## Caveats

- **synthetic_data**: All records are synthetic (HLT-008 sample preview); the figures describe the generator's output, not real-world healthcare behaviour.

## Method

- Seed: 42; plan sha256: `82d1d3c25d089cf00d127e55c02100d872771326d5e36734910f3662b53a0013`.
- Components (canonical order): load_tables, claim_volume, denial_rate, fraud_prevalence, financial_summary, monthly_trend, write_report.
- `load_tables` params: `{}`
- `claim_volume` params: `{'by': ['claim_status'], 'figure': True}`
- `denial_rate` params: `{'denominator': 'all_claims'}`
- `fraud_prevalence` params: `{'denominator': 'all_claims'}`
- `financial_summary` params: `{'amount_columns': ['billed_amount', 'allowed_amount', 'paid_amount'], 'statistics': 'sum_mean'}`
- `monthly_trend` params: `{'date_column': 'adjudication_date', 'metrics': ['claim_count']}`
- `write_report` params: `{'caveats': ['synthetic_data'], 'show_denominators': True, 'cite_artifacts': False}`
- Report options: show_denominators=True, cite_artifacts=False, caveats=['synthetic_data'].
