# Executive brief — run run_004 (skill_learning)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339)
- Total medical claims: 12,845
- Total paid amount: 9,783,415.77
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845)

## Model results

- Fraud model logistic_regression ROC-AUC: 0.502
- Fraud model logistic_regression PR-AUC: 0.058
- Fraud model random_forest ROC-AUC: 0.474
- Fraud model random_forest PR-AUC: 0.048
- Fraud model feature count: 12
- The selected claim attribute set drives the fraud and high-cost scores reported above; the models are baselines fitted on one random split.
