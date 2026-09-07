# Executive brief — run run_006 (reflection_only)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339)
- Total medical claims: 12,845
- Total paid amount: 9,783,415.77
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845)
- Denial rate, network_status = In-Network: 10.56% (1,095 / 10,370)
- Denial rate, network_status = Out-of-Network: 9.70% (191 / 1,969)
- Top denial code CO-15 (scope: denied_claims): 18.74% (241 / 1,286)
- In-Network status drives a higher denial rate in this sample.
- Sources without a completed attempt: T6; their values are not reported.

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
