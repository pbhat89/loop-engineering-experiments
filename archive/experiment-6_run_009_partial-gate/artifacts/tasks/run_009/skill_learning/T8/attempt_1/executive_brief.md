# Executive brief — run run_009 (skill_learning)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339) [source: artifacts/tasks/run_009/skill_learning/T2/attempt_2/metrics.json#denial_rate]
- Total medical claims: 12,845 [source: artifacts/tasks/run_009/skill_learning/T2/attempt_2/metrics.json#claim_volume.total_claims]
- Total paid amount: 9,783,415.77 [source: artifacts/tasks/run_009/skill_learning/T2/attempt_2/metrics.json#financial_summary.paid_amount.sum]
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845) [source: artifacts/tasks/run_009/skill_learning/T2/attempt_2/metrics.json#fraud_prevalence]
- Sources without a completed attempt: T6; their values are not reported. [source: artifacts/tasks/run_009/skill_learning/T8/attempt_1/findings.json]

## Model results

- No model results were available from the selected source tasks.

## Limitations

- Every model is an untuned baseline evaluated on a single random hold-out split; no temporal validation, calibration or confidence intervals were produced.
- Rates depend on the denominators chosen by the source tasks and are only comparable when the denominator definitions match.
- Group differences are descriptive associations; the analyses do not identify mechanisms or effects.

## Next steps

- Re-run the fraud and high-cost baselines with a temporal split and calibrated thresholds before any comparison across models.
- Extend the denial analysis to code-by-segment breakdowns with minimum group sizes and explicit denominators.
- Confirm the data contract (all-null columns, label-derived fields, unmatched pharmacy NPIs) with the data owner before further modelling.
