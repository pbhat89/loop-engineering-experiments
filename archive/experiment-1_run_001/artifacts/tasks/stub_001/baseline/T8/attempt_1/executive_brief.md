# Executive brief — run stub_001 (baseline)

## Key findings

- Denial rate (denominator: adjudicated_claims): 10.42% (1,286 / 12,339)
- Total medical claims: 12,845
- Total paid amount: 9,783,415.77
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845)

## Model results

- Fraud model logistic_regression ROC-AUC: 0.498
- Fraud model logistic_regression PR-AUC: 0.052
- Fraud model random_forest ROC-AUC: 0.492
- Fraud model random_forest PR-AUC: 0.051
- Fraud model feature count: 16
- The selected claim attribute set drives the fraud and high-cost scores reported above; the models are baselines fitted on one random split.
