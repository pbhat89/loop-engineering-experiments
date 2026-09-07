# Executive brief — run run_006 (self_refine_memory)

## Key findings

- Denial rate (denominator: all_claims): 10.01% (1,286 / 12,845)
- Total medical claims: 12,845
- Total paid amount: 9,783,415.77
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845)
- Top denial code CO-15 (scope: denied_claims): 18.74% (241 / 1,286)

## Model results

- High-cost threshold (paid_amount p95, train_only): 3,198.99
- High-cost model logistic_regression PR-AUC: 0.223
- High-cost model random_forest PR-AUC: 0.197
- The selected claim attribute set drives the fraud and high-cost scores reported above; the models are baselines fitted on one random split.

## Limitations

- Every model is an untuned baseline evaluated on a single random hold-out split; no temporal validation, calibration or confidence intervals were produced.
- Rates depend on the denominators chosen by the source tasks and are only comparable when the denominator definitions match.
- Group differences are descriptive associations; the analyses do not identify mechanisms or effects.

## Synthetic-data caveats

- All records are synthetic (the HLT sample preview); no real members, providers or claims are described and no PHI is present.
- Distributions reflect the data generator, so magnitudes must not be quoted as real-world benchmarks or used for operational decisions.

## Next steps

- Re-run the fraud and high-cost baselines with a temporal split and calibrated thresholds before any comparison across models.
- Extend the denial analysis to code-by-segment breakdowns with minimum group sizes and explicit denominators.
- Confirm the data contract (all-null columns, label-derived fields, unmatched pharmacy NPIs) with the data owner before further modelling.
