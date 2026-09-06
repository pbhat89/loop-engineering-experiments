# Data profile summary — HLT-008 sample (synthetic)

Generated 2026-09-06T13:25:44+00:00 by `src/profile_data.py` (pandas 3.0.5).  
Source `xpertsystems/hlt008-sample` @ `7309ddb30e67468748b7aa9182d8517fe28c2f9c`, licence `cc-by-nc-4.0`, retrieved 2026-09-06T13:19:44+00:00.

> All records are **synthetic** (dataset card: no real claims, members, NPIs or PHI). Every count below describes the generator's output, not real-world healthcare behaviour.

## Tables

| table | rows | cols | bytes | sha256 (12) | candidate keys | date range |
|---|---:|---:|---:|---|---|---|
| members | 500 | 44 | 79935 | `4b5c811048ed` | member_id | enrollment_start: 2020-01-03…2021-01-01; enrollment_end: 2023-12-31…2023-12-31 |
| providers | 150 | 7 | 10610 | `8a3a41e69ce6` | provider_npi | — |
| medical_claims | 12845 | 54 | 3525830 | `96ede50f98bb` | claim_id | service_date_from: 2021-01-01…2023-12-31; service_date_to: 2021-01-01…2024-01-09; adjudication_date: 2021-01-08…2024-02-11 |
| pharmacy_claims | 18310 | 35 | 4335821 | `7341275cee17` | rx_claim_id | fill_date: 2021-01-01…2023-12-31; paid_date: 2021-01-02…2024-01-04; end_date: 2021-01-08…2024-03-30 |
| adherence | 10627 | 7 | 520053 | `b89e2343d5f8` | member_id+therapeutic_class | — |

## Key checks

| table | key | rows | null keys | distinct | duplicate rows | unique |
|---|---|---:|---:|---:|---:|---|
| members | member_id | 500 | 0 | 500 | 0 | yes |
| providers | provider_npi | 150 | 0 | 150 | 0 | yes |
| providers | group_id | 150 | 0 | 149 | 2 | no |
| medical_claims | claim_id | 12845 | 0 | 12845 | 0 | yes |
| medical_claims | member_id | 12845 | 0 | 500 | 12845 | no |
| pharmacy_claims | rx_claim_id | 18310 | 0 | 18310 | 0 | yes |
| pharmacy_claims | member_id | 18310 | 0 | 500 | 18310 | no |
| adherence | member_id | 10627 | 0 | 500 | 10627 | no |
| adherence | member_id+therapeutic_class | 10627 | 0 | 10627 | 0 | yes |

## Relationships

| from | to | cardinality | unmatched rows / denominator | unmatched distinct | to-keys unreferenced | match rate |
|---|---|---|---:|---:|---:|---:|
| medical_claims.member_id | members.member_id | many_to_one | 0 / 12845 | 0 | 0 | 1.0 |
| pharmacy_claims.member_id | members.member_id | many_to_one | 0 / 18310 | 0 | 0 | 1.0 |
| adherence.member_id | members.member_id | many_to_one | 0 / 10627 | 0 | 0 | 1.0 |
| medical_claims.rendering_npi | providers.provider_npi | many_to_one | 0 / 12845 | 0 | 0 | 1.0 |
| medical_claims.billing_npi | providers.provider_npi | many_to_one | 0 / 12845 | 0 | 0 | 1.0 |
| pharmacy_claims.pharmacy_npi | providers.provider_npi | no_match | 18310 / 18310 | 18310 | 150 | 0.0 |
| pharmacy_claims.prescriber_npi | providers.provider_npi | no_match | 18310 / 18310 | 18310 | 150 | 0.0 |

## Cross-table consistency

| check | rows | joined | consistent |
|---|---:|---:|---:|
| medical_claims.network_status == providers.network_status (join on rendering_npi = provider_npi) | 12845 | 12845 | 12845 |
| medical_claims.provider_specialty == providers.specialty (join on rendering_npi = provider_npi) | 12845 | 12845 | 12845 |
| medical_claims.service_date_from within members enrollment window | 12845 | 12845 | 12845 |

## Missingness and degenerate columns

- **members**: 2 null cells of 22000 (0.0001); columns with nulls: age_band (2); all-null: none; constant: enrollment_end.
- **providers**: 0 null cells of 1050 (0.0000); columns with nulls: none; all-null: none; constant: none.
- **medical_claims**: 164369 null cells of 693630 (0.2370); columns with nulls: dx3 (12845), dx4 (12845), dx5 (12845), drg_code (10914), drg_type (10914), mdc_code (10914), poa_flag (10914), modifier1 (12845), modifier2 (12845), revenue_code (7041), denial_code_carc (11559), denial_reason_desc (12845), auth_number (12845), fraud_pattern_type (12198); all-null: dx3, dx4, dx5, modifier1, modifier2, denial_reason_desc, auth_number; constant: none.
- **pharmacy_claims**: 0 null cells of 640850 (0.0000); columns with nulls: none; all-null: none; constant: controlled_substance_flag.
- **adherence**: 0 null cells of 74389 (0.0000); columns with nulls: none; all-null: none; constant: adherence_flag_pdc80.

## Date columns

- **members**: enrollment_start [2020-01-03 … 2021-01-01], unparseable 0; enrollment_end [2023-12-31 … 2023-12-31], unparseable 0
- **medical_claims**: service_date_from [2021-01-01 … 2023-12-31], unparseable 0; service_date_to [2021-01-01 … 2024-01-09], unparseable 0; adjudication_date [2021-01-08 … 2024-02-11], unparseable 0
- **pharmacy_claims**: fill_date [2021-01-01 … 2023-12-31], unparseable 0; paid_date [2021-01-02 … 2024-01-04], unparseable 0; end_date [2021-01-08 … 2024-03-30], unparseable 0

## Findings for downstream tasks

- members: constant columns (single value, no variance): enrollment_end.
- members: 2 rows have null age_band (age [0]).
- providers.group_id is not unique (2 rows share a value).
- medical_claims: entirely empty columns: dx3, dx4, dx5, modifier1, modifier2, denial_reason_desc, auth_number.
- medical_claims.fraud_pattern_type is populated exactly when fraud_label == 1: it is label-derived and must be excluded from any fraud model.
- medical_claims.high_cost_flag is perfectly separable on billed_amount (flag 0 max 7688.2, flag 1 min 10299.58): treat it as derived from the claim amount, not as an independent target.
- medical_claims.denial_code_carc: 0 of 1286 Denied claims lack a code; 11559 nulls overall, all on non-denied statuses.
- medical_claims: 36 claims have adjudication_date earlier than service_date_to (none earlier than service_date_from).
- medical_claims.rendering_npi == billing_npi on every row; the two provider joins are redundant.
- medical_claims: 404 of 506 Pended claims carry paid_amount > 0.
- pharmacy_claims: constant columns (single value, no variance): controlled_substance_flag.
- adherence: constant columns (single value, no variance): adherence_flag_pdc80.
- adherence.pdc == adherence.mpr on every row (no independent information).
- adherence: no row reaches PDC 0.80 (max 0.4447); adherence_flag_pdc80 has no positive class.
- pharmacy_claims.pharmacy_npi never matches providers.provider_npi (18310 of 18310 rows unmatched, 18310 distinct values): pharmacy claims cannot be joined to the provider directory.
- pharmacy_claims.prescriber_npi never matches providers.provider_npi (18310 of 18310 rows unmatched, 18310 distinct values): pharmacy claims cannot be joined to the provider directory.

## Per-table domain checks (computed)

### members

```json
{
  "age_band_null_rows": [
    {
      "age": 0,
      "member_id": "MBR00000052"
    },
    {
      "age": 0,
      "member_id": "MBR00000423"
    }
  ],
  "enrollment_end_distinct_values": [
    "2023-12-31"
  ]
}
```

### providers

```json
{
  "group_id_duplicate_values": [
    "GRP4198"
  ]
}
```

### medical_claims

```json
{
  "amount_order_violations": {
    "allowed_gt_billed": 0,
    "negative_amounts": 0,
    "paid_gt_allowed": 0
  },
  "date_order_violations": {
    "adjudication_before_service_from": 0,
    "adjudication_before_service_to": 36,
    "service_to_before_from": 0
  },
  "denial_code_by_claim_status": {
    "Adjusted": {
      "missing_denial_code": 542,
      "rows": 542,
      "with_denial_code": 0
    },
    "Denied": {
      "missing_denial_code": 0,
      "rows": 1286,
      "with_denial_code": 1286
    },
    "Paid": {
      "missing_denial_code": 10511,
      "rows": 10511,
      "with_denial_code": 0
    },
    "Pended": {
      "missing_denial_code": 506,
      "rows": 506,
      "with_denial_code": 0
    }
  },
  "denial_code_counts": {
    "CO-11": 147,
    "CO-119": 51,
    "CO-15": 241,
    "CO-18": 138,
    "CO-27": 115,
    "CO-29": 82,
    "CO-4": 206,
    "CO-50": 87,
    "CO-97": 99,
    "PR-1": 120
  },
  "denial_code_missing_total": 11559,
  "drg_code_present_by_claim_type": {
    "Institutional-IP": {
      "rows": 1931,
      "with_drg": 1931
    },
    "Institutional-OP": {
      "rows": 3873,
      "with_drg": 0
    },
    "Professional": {
      "rows": 7041,
      "with_drg": 0
    }
  },
  "fraud_label_prevalence": 0.05037,
  "fraud_pattern_by_label": {
    "0": {
      "rows": 12198,
      "with_pattern": 0,
      "without_pattern": 12198
    },
    "1": {
      "rows": 647,
      "with_pattern": 647,
      "without_pattern": 0
    }
  },
  "fraud_pattern_type_present_iff_fraud_label_1": true,
  "high_cost_flag_prevalence": 0.023355,
  "high_cost_flag_separability": {
    "allowed_amount": {
      "flag0_max": 6147.36,
      "flag1_min": 3960.63,
      "perfectly_separable": false
    },
    "billed_amount": {
      "flag0_max": 7688.2,
      "flag1_min": 10299.58,
      "perfectly_separable": true
    },
    "paid_amount": {
      "flag0_max": 5988.45,
      "flag1_min": 0.0,
      "perfectly_separable": false
    }
  },
  "paid_amount_by_claim_status": {
    "Adjusted": {
      "paid_max": 20087.31,
      "paid_sum": 525744.59,
      "rows": 542,
      "rows_paid_gt_0": 430
    },
    "Denied": {
      "paid_max": 0.0,
      "paid_sum": 0.0,
      "rows": 1286,
      "rows_paid_gt_0": 0
    },
    "Paid": {
      "paid_max": 24677.53,
      "paid_sum": 8850958.52,
      "rows": 10511,
      "rows_paid_gt_0": 8283
    },
    "Pended": {
      "paid_max": 13135.26,
      "paid_sum": 406712.66,
      "rows": 506,
      "rows_paid_gt_0": 404
    }
  },
  "rendering_npi_equals_billing_npi_fraction": 1.0
}
```

### pharmacy_claims

```json
{
  "date_order_violations": {
    "end_before_fill": 0,
    "paid_before_fill": 0
  },
  "diversion_flag_prevalence": 0.015401,
  "early_refill_flag_prevalence": 0.07089,
  "end_date_equals_fill_plus_days_supply_fraction": 1.0,
  "fraud_label_rx_prevalence": 0.0355,
  "pharmacy_npi_distinct_equals_rows": true,
  "prescriber_npi_distinct_equals_rows": true
}
```

### adherence

```json
{
  "adherence_flag_pdc80_distinct_values": [
    0
  ],
  "pdc_equals_mpr_all_rows": true,
  "pdc_max": 0.4447,
  "pdc_min": 0.0064,
  "rows_pdc_ge_0_80": 0
}
```

Machine-readable profiles: `artifacts/data_profile/<table>.profile.json`; contract: `data/processed/manifest.json`.
