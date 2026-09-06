# Golden pack review (Phase 1.5 user checkpoint)

Built 2026-09-06T17:10:51+00:00 by `src/build_goldens.py` from dataset revision `7309ddb30e67468748b7aa9182d8517fe28c2f9c` (synthetic HLT-008 sample). Every row is one frozen reference value; the definition states numerator / denominator / filters / seed / split. Review once, then the lead freezes `config/freeze_manifest.json`. Rebuild with `uv run python -m src.build_goldens`; verify with `--check`.

| task | metric | value | definition | tolerance | sanity |
|---|---|---|---|---|---|
| T1 | `tables.members.rows` | 500 | len(load_table(name)) | exact | OK: 44 columns |
| T1 | `tables.providers.rows` | 150 | len(load_table(name)) | exact | OK: 7 columns |
| T1 | `tables.medical_claims.rows` | 12845 | len(load_table(name)) | exact | OK: 54 columns |
| T1 | `tables.pharmacy_claims.rows` | 18310 | len(load_table(name)) | exact | OK: 35 columns |
| T1 | `tables.adherence.rows` | 10627 | len(load_table(name)) | exact | OK: 7 columns |
| T1 | `missingness.all_null_columns.medical_claims` | auth_number, denial_reason_desc, dx3, dx4, dx5, modifier1, modifier2 | columns of medical_claims with null_count == rows | exact (order-insensitive) | OK: 7 columns expected from A2 profile |
| T1 | `duplicates.medical_claims.claim_id` | 12845 unique of 12845 | rows vs drop_duplicates(subset=key) | exact | OK: candidate key |
| T1 | `duplicates.pharmacy_claims.rx_claim_id` | 18310 unique of 18310 | rows vs drop_duplicates(subset=key) | exact | OK: candidate key |
| T1 | `duplicates.members.member_id` | 500 unique of 500 | rows vs drop_duplicates(subset=key) | exact | OK: candidate key |
| T1 | `duplicates.providers.provider_npi` | 150 unique of 150 | rows vs drop_duplicates(subset=key) | exact | OK: candidate key |
| T1 | `duplicates.adherence.member_id` | 500 unique of 10627 | rows vs drop_duplicates(subset=key) | exact | OK: not a key (composite key expected instead) |
| T1 | `duplicates.adherence.member_id+therapeutic_class` | 10627 unique of 10627 | rows vs drop_duplicates(subset=key) | exact | OK: candidate key |
| T1 | `date_ranges.medical_claims.service_date_from` | 2021-01-01 .. 2023-12-31 | pd.to_datetime(errors='coerce') min/max | exact | OK: 0 unparseable |
| T1 | `date_ranges.medical_claims.service_date_to` | 2021-01-01 .. 2024-01-09 | pd.to_datetime(errors='coerce') min/max | exact | OK: 0 unparseable |
| T1 | `date_ranges.medical_claims.adjudication_date` | 2021-01-08 .. 2024-02-11 | pd.to_datetime(errors='coerce') min/max | exact | OK: 0 unparseable |
| T1 | `date_consistency.adjudication_before_service_end` | 36 | count(adjudication_date < service_date_to) | exact | OK: A2 reported 36; service_end_before_start = 0 |
| T1 | `join_check.medical_claims.member_id->members.member_id` | many_to_one, unmatched 0/12845 | left keys not in right key set; inner join row count | exact | OK: matched + unmatched = rows_left |
| T1 | `join_check.medical_claims.rendering_npi->providers.provider_npi` | many_to_one, unmatched 0/12845 | left keys not in right key set; inner join row count | exact | OK: matched + unmatched = rows_left |
| T1 | `join_check.medical_claims.billing_npi->providers.provider_npi` | many_to_one, unmatched 0/12845 | left keys not in right key set; inner join row count | exact | OK: matched + unmatched = rows_left |
| T1 | `join_check.pharmacy_claims.member_id->members.member_id` | many_to_one, unmatched 0/18310 | left keys not in right key set; inner join row count | exact | OK: matched + unmatched = rows_left |
| T1 | `join_check.pharmacy_claims.pharmacy_npi->providers.provider_npi` | no_match, unmatched 18310/18310 | left keys not in right key set; inner join row count | exact | OK: matched + unmatched = rows_left |
| T1 | `join_check.adherence.member_id->members.member_id` | many_to_one, unmatched 0/10627 | left keys not in right key set; inner join row count | exact | OK: matched + unmatched = rows_left |
| T2 | `claim_volume.total_claims` | 12845 | all rows of medical_claims | exact | OK: A2 row count |
| T2 | `claim_volume.by.claim_status` | Paid 10511, Denied 1286, Adjusted 542, Pended 506 | value_counts(claim_status) | exact | OK: status counts sum to total |
| T2 | `denial_rate` | 0.104222 | 1286 denied / 12339 adjudicated (Paid+Denied+Adjusted) | 1e-06 | OK: adjudicated = total - Pended |
| T2 | `fraud_prevalence` | 0.050370 | 647 fraud_label==1 / 12845 all claims | 1e-06 | OK: A2 reported 647 |
| T2 | `financial_summary.billed_amount` | sum 21254208.81; mean 1654.67; median 429.52; p90 4279.02; p99 21256.58 | sum/mean/median/p90/p99 over all rows | 0.01 | OK: median <= p90 <= p99 |
| T2 | `financial_summary.allowed_amount` | sum 12175223.45; mean 947.86; median 241.90; p90 2359.65; p99 11562.75 | sum/mean/median/p90/p99 over all rows | 0.01 | OK: median <= p90 <= p99 |
| T2 | `financial_summary.paid_amount` | sum 9783415.77; mean 761.65; median 124.90; p90 2043.85; p99 10911.44 | sum/mean/median/p90/p99 over all rows | 0.01 | OK: median <= p90 <= p99 |
| T2 | `monthly_trend.series.claim_count` | 36 months 2021-01..2023-12; min 302, max 405 per month | count per %Y-%m of service_date_from | exact per month | OK: monthly counts + unparseable = total |
| T3 | `group_comparison.groups.network_status.In-Network` | n 10788; denial 1095/10370 = 0.105593; fraud 543/10788 | per network_status: n = all claims; denial over adjudicated; fraud over n; small if n < 30 | n exact; rate 1e-06 | OK: group not small |
| T3 | `group_comparison.groups.network_status.Out-of-Network` | n 2057; denial 191/1969 = 0.097004; fraud 104/2057 | per network_status: n = all claims; denial over adjudicated; fraud over n; small if n < 30 | n exact; rate 1e-06 | OK: group not small |
| T3 | `group_comparison.groups.provider_specialty` | 25 specialties; n 71..1225; small flags 0 | per specialty: n, denial numerator/denominator (adjudicated), fraud numerator/denominator, small_group_flag (n < 30) | exact | OK: n sums to 12845, denied sums to 1286 |
| T3 | `group_comparison.groups.network_status (totals)` | n sum 12845 | sum over network_status groups | exact | OK: sums to 12845 |
| T3 | `provider_ranking.rows` | 1186826716 115; 1563980627 108; 1644128543 106; 1609526529 106; 1193493783 105; 1752470395 104; 1590915516 102; 1125190055 102; 1103747954 102; 1531398223 101 | top 10 rendering_npi by claim count (ties inside the top 10 matched order-insensitively) | exact (order-insensitive) | OK: no tie at the boundary (10th 101 > 11th 100) |
| T3 | `join_check.medical_claims.rendering_npi->providers.provider_npi` | many_to_one, unmatched 0/12845, rows after inner join 12845 | rendering_npi in providers.provider_npi | exact | OK: full match, no row-count change |
| T4 | `denial_code_ranking.codes` | CO-15 241; CO-4 206; CO-11 147; CO-18 138; PR-1 120; CO-27 115; CO-97 99; CO-50 87; CO-29 82; CO-119 51 | value_counts(denial_code_carc) among denied claims; share = n / denied | exact (share float) | OK: counts sum to 1286; shares sum to 1 |
| T4 | `denial_code_ranking.missing_denial_codes` | overall 11559/12845; among denied 0/1286 | denial_code_carc.isna() | exact | OK: missing overall = total - denied; none missing among denied |
| T4 | `denial_rate_by_segment.segments.claim_type` | 3 values; rates 0.0935..0.1125; small flags 0 | per value: denied / adjudicated in segment; small if denominator < 30; values keyed by str() | exact counts | OK: numerators sum to 1286, denominators to 12339 |
| T4 | `denial_rate_by_segment.segments.provider_specialty` | 25 values; rates 0.0588..0.1325; small flags 0 | per value: denied / adjudicated in segment; small if denominator < 30; values keyed by str() | exact counts | OK: numerators sum to 1286, denominators to 12339 |
| T4 | `denial_rate_by_segment.segments.network_status` | 2 values; rates 0.0970..0.1056; small flags 0 | per value: denied / adjudicated in segment; small if denominator < 30; values keyed by str() | exact counts | OK: numerators sum to 1286, denominators to 12339 |
| T4 | `denial_rate_by_segment.segments.place_of_service` | 11 values; rates 0.0874..0.1472; small flags 0 | per value: denied / adjudicated in segment; small if denominator < 30; values keyed by str() | exact counts | OK: numerators sum to 1286, denominators to 12339 |
| T4 | `denial_rate_by_segment.segments.auth_required_flag` | 2 values; rates 0.0956..0.1057; small flags 0 | per value: denied / adjudicated in segment; small if denominator < 30; values keyed by str() | exact counts | OK: numerators sum to 1286, denominators to 12339 |
| T4 | `denial_rate_by_segment.segments.claim_type.Professional.rate` | 0.102606 | 693 / 6754 | 1e-06 | OK: rate in (0, 1) |
| T5 | `class_prevalence` | positives 647; negatives 12198; prevalence 0.050370; imbalance_ratio 18.8532 | fraud_label == 1 over all claims; imbalance = negatives / positives | counts exact; rates 1e-06 | OK: positives + negatives = total |
| T5 | `feature_comparison.billed_amount.{flagged,unflagged}.mean` | flagged 1692.4845; unflagged 1652.6620 | mean billed_amount by fraud_label | 1e-06 | OK: positive means |
| T5 | `feature_comparison.claim_type.flagged` | Institutional-IP 0.1515; Institutional-OP 0.3261; Professional 0.5224 | value_counts(normalize=True) within flagged claims | 1e-06 | OK: shares sum to 1 |
| T6 | `split` | n_train 9633; n_test 3212; prevalence_train 0.050348; prevalence_test 0.050436 | train_test_split(np.arange(12845), test_size=0.25, random_state=42, shuffle=True, stratify=fraud_label) | sizes exact | OK: sizes sum to total; stratified prevalences match |
| T7 | `target_definition.threshold_value` | 3198.9880 | numpy.percentile(paid_amount[train], 95) with train from train_test_split(np.arange(12845), test_size=0.25, random_state=42, shuffle=True) | 0.01 | OK: differs from the all-data percentile 3161.9340, so the check discriminates |
| T7 | `target_definition.positive_rate_{train,test}` | train 482/9633 = 0.050036; test 150/3212 = 0.046700 | paid_amount > threshold_value in each partition | 1e-06 | OK: train positive rate about 5 percent |
| T7 | `split` | n_train 9633; n_test 3212 | plain split, no stratification | exact | OK: sizes sum to total |
| T8 | `brief contracts` | sources >= {T2,T5,T6,T7} + one of {T3,T4}; 5 sections; cite_artifacts; causal_language avoid; <= 600 words | structural golden (no data values) | n/a | OK: forbidden phrases: causes, drives, leads to, because of |
