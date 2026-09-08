# Executive brief — run run_008 (skill_learning)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339) [source: artifacts/tasks/run_008/skill_learning/T11/attempt_1/metrics.json#denial_rate]
- Total medical claims: 12,845 [source: artifacts/tasks/run_008/skill_learning/T11/attempt_1/metrics.json#claim_volume.total_claims]
- Total paid amount: 9,783,415.77 [source: artifacts/tasks/run_008/skill_learning/T11/attempt_1/metrics.json#financial_summary.paid_amount.sum]
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845) [source: artifacts/tasks/run_008/skill_learning/T11/attempt_1/metrics.json#fraud_prevalence]

## Model results

- High-cost threshold (paid_amount p90, train_only): 2,074.35 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_2/metrics.json#target_definition.threshold_value]
- High-cost model logistic_regression PR-AUC: 0.394 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_2/metrics.json#models.logistic_regression.pr_auc]
- High-cost model logistic_regression ROC-AUC: 0.918 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_2/metrics.json#models.logistic_regression.roc_auc]
- High-cost model gradient_boosting PR-AUC: 0.391 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_2/metrics.json#models.gradient_boosting.pr_auc]
- High-cost model gradient_boosting ROC-AUC: 0.913 [source: artifacts/tasks/run_008/skill_learning/T12/attempt_2/metrics.json#models.gradient_boosting.roc_auc]
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
