# Executive brief — run stub_004 (feedback_memory)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339) [source: artifacts/tasks/stub_004/feedback_memory/T2/attempt_4/metrics.json#denial_rate]
- Total medical claims: 12,845 [source: artifacts/tasks/stub_004/feedback_memory/T2/attempt_4/metrics.json#claim_volume.total_claims]
- Total paid amount: 9,783,415.77 [source: artifacts/tasks/stub_004/feedback_memory/T2/attempt_4/metrics.json#financial_summary.paid_amount.sum]
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845) [source: artifacts/tasks/stub_004/feedback_memory/T2/attempt_4/metrics.json#fraud_prevalence]
- Denial rate, network_status = In-Network: 10.56% (1,095 / 10,370) [source: artifacts/tasks/stub_004/feedback_memory/T3/attempt_3/metrics.json#group_comparison.groups.network_status.In-Network.denial_rate]
- Denial rate, network_status = Out-of-Network: 9.70% (191 / 1,969) [source: artifacts/tasks/stub_004/feedback_memory/T3/attempt_3/metrics.json#group_comparison.groups.network_status.Out-of-Network.denial_rate]
- Top denial code CO-15 (scope: denied_claims): 18.74% (241 / 1,286) [source: artifacts/tasks/stub_004/feedback_memory/T4/attempt_3/metrics.json#denial_code_ranking.codes[0]]
- In-Network status is associated with a higher denial rate in this sample.
- Sources without a completed attempt: T5, T6; their values are not reported. [source: artifacts/tasks/stub_004/feedback_memory/T8/attempt_3/findings.json]

## Model results

- High-cost threshold (paid_amount p95, train_only): 3,198.99 [source: artifacts/tasks/stub_004/feedback_memory/T7/attempt_3/metrics.json#target_definition.threshold_value]
- High-cost model logistic_regression PR-AUC: 0.221 [source: artifacts/tasks/stub_004/feedback_memory/T7/attempt_3/metrics.json#models.logistic_regression.pr_auc]
- High-cost model random_forest PR-AUC: 0.197 [source: artifacts/tasks/stub_004/feedback_memory/T7/attempt_3/metrics.json#models.random_forest.pr_auc]
- The selected claim attribute set is associated with the fraud and high-cost scores reported above; the models are baselines fitted on one random split.

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
