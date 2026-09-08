# Executive brief — run stub_006 (reflection_only)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339) [source: artifacts/tasks/stub_006/reflection_only/T11/attempt_4/metrics.json#denial_rate]
- Total medical claims: 12,845 [source: artifacts/tasks/stub_006/reflection_only/T11/attempt_4/metrics.json#claim_volume.total_claims]
- Total paid amount: 9,783,415.77 [source: artifacts/tasks/stub_006/reflection_only/T11/attempt_4/metrics.json#financial_summary.paid_amount.sum]
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845) [source: artifacts/tasks/stub_006/reflection_only/T11/attempt_4/metrics.json#fraud_prevalence]

## Model results

- High-cost threshold (paid_amount p90, train_only): 2,074.35 [source: artifacts/tasks/stub_006/reflection_only/T12/attempt_3/metrics.json#target_definition.threshold_value]
- High-cost model logistic_regression PR-AUC: 0.394 [source: artifacts/tasks/stub_006/reflection_only/T12/attempt_3/metrics.json#models.logistic_regression.pr_auc]
- High-cost model logistic_regression ROC-AUC: 0.918 [source: artifacts/tasks/stub_006/reflection_only/T12/attempt_3/metrics.json#models.logistic_regression.roc_auc]
- High-cost model random_forest PR-AUC: 0.387 [source: artifacts/tasks/stub_006/reflection_only/T12/attempt_3/metrics.json#models.random_forest.pr_auc]
- High-cost model random_forest ROC-AUC: 0.908 [source: artifacts/tasks/stub_006/reflection_only/T12/attempt_3/metrics.json#models.random_forest.roc_auc]
- The selected claim attribute set drives the fraud and high-cost scores reported above; the models are baselines fitted on one random split.
