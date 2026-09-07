# Executive brief — run run_006 (feedback_memory)

## Key findings

- members row count: 500
- providers row count: 150
- medical_claims row count: 12,845
- pharmacy_claims row count: 18,310
- adherence row count: 10,627
- Denial rate, network_status = In-Network: 10.56% (1,095 / 10,370)
- Denial rate, network_status = Out-of-Network: 9.70% (191 / 1,969)
- Top denial code CO-15 (scope: denied_claims): 18.74% (241 / 1,286)
- In-Network status is associated with a higher denial rate in this sample.

## Model results

- High-cost threshold (paid_amount p95, train_only): 3,198.99
- High-cost model logistic_regression PR-AUC: 0.223
- High-cost model gradient_boosting PR-AUC: 0.217
- The selected claim attribute set is associated with the fraud and high-cost scores reported above; the models are baselines fitted on one random split.

## Limitations

- Every model is an untuned baseline evaluated on a single random hold-out split; no temporal validation, calibration or confidence intervals were produced.
- Rates depend on the denominators chosen by the source tasks and are only comparable when the denominator definitions match.
- Group differences are descriptive associations; the analyses do not identify mechanisms or effects.

## Next steps

- Re-run the fraud and high-cost baselines with a temporal split and calibrated thresholds before any comparison across models.
- Extend the denial analysis to code-by-segment breakdowns with minimum group sizes and explicit denominators.
- Confirm the data contract (all-null columns, label-derived fields, unmatched pharmacy NPIs) with the data owner before further modelling.
