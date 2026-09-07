# T2 — Claims portfolio description

## Summary

Task T2 (Claims portfolio description) for run `stub_004` / condition `reflection_only`, attempt 3: status **ok**; 7 component(s) executed, 0 failed, 0 error(s) recorded.
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

- Denial rate (denominator: adjudicated_claims): 0.104222

### fraud_prevalence

- Fraud prevalence (denominator: all_claims): 0.050370

### financial_summary

- billed_amount: sum: 21254208.810000
- billed_amount: mean: 1654.667872
- billed_amount: median / p90 / p99 = 429.52 / 4279.02 / 21256.58
- allowed_amount: sum: 12175223.450000
- allowed_amount: mean: 947.857022
- allowed_amount: median / p90 / p99 = 241.90 / 2359.65 / 11562.75
- paid_amount: sum: 9783415.770000
- paid_amount: mean: 761.651675
- paid_amount: median / p90 / p99 = 124.90 / 2043.85 / 10911.44

### monthly_trend

- Date column service_date_from: months covered: 36
- Range 2021-01 … 2023-12; unparseable dates: 0
- claim_count: mean per month: 356.805556

## Artifacts

- `artifacts/tasks/stub_004/reflection_only/T2/attempt_3/claims_status_distribution.png`
- `artifacts/tasks/stub_004/reflection_only/T2/attempt_3/financial_summary.csv`
- `artifacts/tasks/stub_004/reflection_only/T2/attempt_3/monthly_trend.csv`
- `artifacts/tasks/stub_004/reflection_only/T2/attempt_3/monthly_claim_volume.png`
- `artifacts/tasks/stub_004/reflection_only/T2/attempt_3/metrics.json`
- `artifacts/tasks/stub_004/reflection_only/T2/attempt_3/report.md`

## Method

- Seed: 42; plan sha256: `253cf5d02dfb9fc38f9c82e49d601212728921a9664e3f6d6559d68f4ac64c24`.
- Components (canonical order): load_tables, claim_volume, denial_rate, fraud_prevalence, financial_summary, monthly_trend, write_report.
- `load_tables` params: `{}`
- `claim_volume` params: `{'by': ['claim_status'], 'figure': True}`
- `denial_rate` params: `{'denominator': 'adjudicated_claims'}`
- `financial_summary` params: `{'amount_columns': ['billed_amount', 'allowed_amount', 'paid_amount'], 'statistics': 'sum_mean_quantiles'}`
- `monthly_trend` params: `{'date_column': 'service_date_from', 'metrics': ['claim_count']}`
- `write_report` params: `{'caveats': [], 'show_denominators': False, 'cite_artifacts': False}`
- `fraud_prevalence` params: `{'denominator': 'all_claims'}`
- Report options: show_denominators=False, cite_artifacts=False, caveats=[].
