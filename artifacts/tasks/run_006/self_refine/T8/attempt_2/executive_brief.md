# Executive brief — run run_006 (self_refine)

## Key findings

- members row count: 500 [source: artifacts/tasks/run_006/self_refine/T1/attempt_2/metrics.json#tables.members.rows]
- providers row count: 150 [source: artifacts/tasks/run_006/self_refine/T1/attempt_2/metrics.json#tables.providers.rows]
- medical_claims row count: 12,845 [source: artifacts/tasks/run_006/self_refine/T1/attempt_2/metrics.json#tables.medical_claims.rows]
- pharmacy_claims row count: 18,310 [source: artifacts/tasks/run_006/self_refine/T1/attempt_2/metrics.json#tables.pharmacy_claims.rows]
- adherence row count: 10,627 [source: artifacts/tasks/run_006/self_refine/T1/attempt_2/metrics.json#tables.adherence.rows]
- Denial rate (denominator: all_claims): 10.01% (1,286 / 12,845) [source: artifacts/tasks/run_006/self_refine/T2/attempt_1/metrics.json#denial_rate]
- Total medical claims: 12,845 [source: artifacts/tasks/run_006/self_refine/T2/attempt_1/metrics.json#claim_volume.total_claims]
- Total paid amount: 9,783,415.77 [source: artifacts/tasks/run_006/self_refine/T2/attempt_1/metrics.json#financial_summary.paid_amount.sum]
- Fraud prevalence (denominator: all_claims): 5.04% (647 / 12,845) [source: artifacts/tasks/run_006/self_refine/T2/attempt_1/metrics.json#fraud_prevalence]

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
