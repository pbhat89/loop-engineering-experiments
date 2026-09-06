# Lead catalogue skeleton (L0) — binding for A3 (tasks/goldens/evaluator) and A6 (executor)

This file fixes the **component ids, parameter options, defaults, produced metric keys/shapes, artifact names and golden conventions** for T1–T8, so the golden pack, the evaluator and the executor are built independently against one contract. A3 turns it into `config/tasks.yaml` (adding fair objective text and descriptions) and `goldens/`; A6 implements every component in `src/analyses/`. Neither may rename ids, options or metric keys; additions are allowed only if reported to the lead. Data facts come from `data/processed/manifest.json` and A2's report.

Plan-parameter grammar (validated by `src/graph_nodes.validate_plan`): a param has `options` and a `default`; `multi: true` params take a **list** whose items are all in `options`; option values are compared by string form (`"30"` matches `30`). Omitted params take defaults. `default_selected: true` marks components an unguided/stub baseline includes; **defaults are the naive analyst choice, never automatically the golden choice**.

## 0. Conventions (apply everywhere)

| Term | Definition |
|---|---|
| `all_claims` | every row of `medical_claims` (12,845) |
| `adjudicated_claims` | `claim_status ∈ {Paid, Denied, Adjusted}` (Pended excluded) → 12,339 |
| `paid_and_denied` | `claim_status ∈ {Paid, Denied}` |
| denied | `claim_status == "Denied"` (1,286) |
| fraud positive | `fraud_label == 1` (647) |
| month key | `%Y-%m` of the chosen date column, parsed with `pd.to_datetime(errors="coerce")`; unparseable rows dropped **and counted** |
| rates | plain floats, unrounded in `metrics.json`; goldens compare with tolerance `1e-6` (rates) / `0.01` (currency sums) unless stated |
| small group | `n < min_group_size` (`min_group_size = 0` ⇒ never flagged) |
| seed | `run_context["seed"]` (42) for every split and model |
| row order | as returned by `src.profile_data.load_table(name)` — never re-sort before splitting |
| split | `sklearn.model_selection.train_test_split(indices, test_size=test_size, random_state=seed, shuffle=True, stratify=<target or None>)` on `np.arange(len(df))` |
| models | `LogisticRegression(max_iter=1000, random_state=seed)`; `RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=1)`; `HistGradientBoostingClassifier(random_state=seed)`; categorical → `OneHotEncoder(handle_unknown="ignore")`; numeric → `StandardScaler` only when `scaling=standard`; positive-class scores via `predict_proba[:, 1]`; classification threshold 0.5 |
| id fields | `claim_id, member_id, rendering_npi, billing_npi, plan_id, auth_number, rx_claim_id, provider_npi` |
| protected attributes | `member_sex, member_race_ethnicity, member_age_band, member_income_band` (members table joined on `member_id`) — never targeting features |
| label-derived fields | `fraud_pattern_type` (non-null iff `fraud_label == 1`); `high_cost_flag` is a deterministic function of `billed_amount` |
| `metrics.json` | `{task_id, run_id, condition, attempt, seed, generated_at, plan_sha256, plan, tables: {name: {rows, columns}}, <one key per produced metric>}` — always written, as is `report.md` |
| `report.md` | `# <title>` · `## Summary` · `## Results` (one subsection per executed component) · `## Artifacts` (relative paths) · `## Caveats` (only when `caveats` non-empty; fixed sentence per caveat id) · `## Method` (components, params, seed). With `show_denominators=true` every rate prints as `numerator / denominator = rate`; with `cite_artifacts=true` every results bullet ends with `[source: <artifact path or metrics.json#key>]` |
| execution order | the executor runs selected components in the canonical order listed per task (not plan order); a component whose dependency was not selected records `{"type": "missing_dependency"}` and is skipped |
| paths | `run_context["output_dir"]` is repo-relative; artifacts are reported repo-relative |

Shared components (same shape wherever they appear):

```yaml
- id: load_tables            # default_selected: true; params: {}
  produces: tables -> {table: {rows: int, columns: int}}
- id: join_check             # default_selected: false
  params:
    pairs: {multi: true, default: [],
            options: [medical_claims.member_id->members.member_id, medical_claims.rendering_npi->providers.provider_npi,
                      medical_claims.billing_npi->providers.provider_npi, pharmacy_claims.member_id->members.member_id,
                      pharmacy_claims.pharmacy_npi->providers.provider_npi, adherence.member_id->members.member_id]}
  produces: join_check -> {pair: {cardinality: many_to_one|one_to_one|no_match|many_to_many, rows_left: int, rows_after_inner_join: int,
                                  unmatched_left: int, unmatched_left_denominator: int, right_key_unique: bool}}
- id: write_report           # default_selected: true
  params:
    caveats: {multi: true, default: [],
              options: [synthetic_data, sample_preview, descriptive_only, association_not_causation, small_groups,
                        class_imbalance, model_limitations, no_operational_use]}
    show_denominators: {options: [true, false], default: false}
    cite_artifacts: {options: [true, false], default: false}
  produces: report -> {caveats: [..], show_denominators: bool, cite_artifacts: bool, sections: [..]}   # + report.md
```

## T1 — Dataset reconnaissance

```yaml
task_id: T1
input_tables: [members, providers, medical_claims, pharmacy_claims, adherence]
tags: [data_contract, schema, keys, missingness, duplicates, dates, joins, cardinality, data_quality]
required_artifacts: [data_contract.json, missingness.csv, report.md, metrics.json]
components (canonical order):
  - load_tables
  - id: schema_summary        # default_selected: true; params: {}
    produces: schema -> {table: {rows: int, n_columns: int, dtypes: {dtype: count}}}      # + data_contract.json {table: {rows, columns: [{name, dtype}]}}
  - id: missingness           # default_selected: true
    params: {scope: {options: [top_10, all_columns], default: top_10}}
    produces: missingness -> {scope, per_table: {table: {column: null_count}}, all_null_columns: {table: [column]}}   # + missingness.csv (table, column, null_count, null_share)
  - id: duplicate_check       # default_selected: false
    params: {keys: {multi: true, default: [medical_claims.claim_id],
                    options: [medical_claims.claim_id, pharmacy_claims.rx_claim_id, members.member_id, providers.provider_npi,
                              adherence.member_id, adherence.member_id+therapeutic_class]}}
    produces: duplicates -> {key: {n_rows: int, n_unique: int, duplicate_rows: int, is_candidate_key: bool}}
  - id: date_ranges           # default_selected: false
    params:
      columns: {multi: true, default: [medical_claims.service_date_from],
                options: [medical_claims.service_date_from, medical_claims.service_date_to, medical_claims.adjudication_date,
                          pharmacy_claims.fill_date, pharmacy_claims.paid_date, members.enrollment_start, members.enrollment_end]}
      consistency_checks: {options: [true, false], default: false}
    produces: date_ranges -> {column: {min: "YYYY-MM-DD", max: "YYYY-MM-DD", unparseable: int}}
              date_consistency (only if true) -> {adjudication_before_service_end: int, service_end_before_start: int}
  - join_check
  - write_report
golden conventions: exact row counts for the five tables; `all_null_columns.medical_claims` must equal
  [auth_number, denial_reason_desc, dx3, dx4, dx5, modifier1, modifier2] (needs scope=all_columns); duplicates for all six keys with
  is_candidate_key true for each; date ranges for the three medical date columns + date_consistency.adjudication_before_service_end = 36;
  join_check for all six pairs including the two `no_match` pharmacy NPI pairs; caveats ⊇ [synthetic_data, sample_preview].
```

## T2 — Claims portfolio description

```yaml
task_id: T2
input_tables: [medical_claims]
tags: [descriptive, portfolio, rates, denominators, financial, trends, status_mix]
required_artifacts: [claims_status_distribution.png, monthly_claim_volume.png, financial_summary.csv, monthly_trend.csv, report.md, metrics.json]
components:
  - load_tables
  - id: claim_volume          # default_selected: true
    params:
      by: {multi: true, default: [claim_status], options: [claim_status, claim_type, cpt_category, place_of_service, network_status, provider_specialty]}
      figure: {options: [true, false], default: true}
    produces: claim_volume -> {total_claims: int, by: {column: {value: {n: int, share: float}}}}     # + claims_status_distribution.png when claim_status in by and figure
  - id: denial_rate           # default_selected: true
    params: {denominator: {options: [all_claims, adjudicated_claims, paid_and_denied], default: all_claims}}
    produces: denial_rate -> {value: float, numerator: int, denominator: int, numerator_definition: str, denominator_definition: str, denominator_option: str}
  - id: fraud_prevalence      # default_selected: false
    params: {denominator: {options: [all_claims, adjudicated_claims], default: all_claims}}
    produces: fraud_prevalence -> {value, numerator, denominator, denominator_option}
  - id: financial_summary     # default_selected: true
    params:
      amount_columns: {multi: true, default: [paid_amount], options: [billed_amount, allowed_amount, paid_amount, member_oop, cob_amount]}
      statistics: {options: [sum_mean, sum_mean_quantiles], default: sum_mean}
    produces: financial_summary -> {column: {n: int, sum: float, mean: float, median?: float, p90?: float, p99?: float}}   # quantiles only with sum_mean_quantiles; + financial_summary.csv
  - id: monthly_trend         # default_selected: true
    params:
      date_column: {options: [service_date_from, service_date_to, adjudication_date], default: adjudication_date}
      metrics: {multi: true, default: [claim_count], options: [claim_count, paid_amount_sum]}
    produces: monthly_trend -> {date_column, n_months: int, first_month, last_month, unparseable_dates: int, series: {metric: {"YYYY-MM": value}}}   # + monthly_claim_volume.png, monthly_trend.csv
  - write_report
golden conventions: total_claims 12845; by.claim_status exact (Paid 10511, Denied 1286, Adjusted 542, Pended 506); denial_rate with
  denominator_option adjudicated_claims = 1286 / 12339; fraud_prevalence all_claims = 647 / 12845; financial sums for billed, allowed and paid
  (tolerance 0.01) with statistics sum_mean_quantiles; monthly_trend.date_column == service_date_from with exact claim_count per month and n_months;
  report.show_denominators true; caveats ⊇ [synthetic_data, descriptive_only].
```

## T3 — Provider and network patterns

Group by the **claim-level** columns `provider_specialty` and `network_status` of `medical_claims` (the providers table is used for the join check and the provider ranking).

```yaml
task_id: T3
input_tables: [medical_claims, providers]
tags: [providers, network, specialty, group_comparison, small_groups, rates, denominators, joins, cardinality]
required_artifacts: [group_comparison.csv, group_comparison.png, provider_ranking.csv, report.md, metrics.json]
components:
  - load_tables
  - join_check
  - id: provider_join         # default_selected: false
    params:
      provider_key: {options: [rendering_npi, billing_npi], default: rendering_npi}
      how: {options: [inner, left], default: inner}
      validate: {options: [none, many_to_one], default: none}
    produces: provider_join -> {provider_key, how, validate, rows_before: int, rows_after: int, unmatched: int, providers_matched: int}
  - id: group_comparison      # default_selected: true
    params:
      group_by: {multi: true, default: [provider_specialty], options: [provider_specialty, network_status, provider_specialty+network_status]}
      metrics: {multi: true, default: [claim_count, paid_amount_sum], options: [claim_count, paid_amount_sum, paid_amount_mean, denial_rate, fraud_rate]}
      denominator: {options: [all_claims, adjudicated_claims], default: all_claims}     # applies to denial_rate; fraud_rate is always over all claims in the group
      min_group_size: {options: [0, 30, 50, 100], default: 0}
    produces: group_comparison -> {min_group_size, denominator_option, groups: {group_by_key: {group_value: {n: int, claim_count?: int, paid_amount_sum?: float,
                 paid_amount_mean?: float, denial_rate?: {value, numerator, denominator}, fraud_rate?: {value, numerator, denominator}, small_group_flag: bool}}}}
              # composite key value formatted "<specialty>|<network_status>"; + group_comparison.csv, group_comparison.png (claim_count by first group_by)
  - id: provider_ranking      # default_selected: false
    params:
      metric: {options: [claim_count, paid_amount_sum, denial_rate], default: claim_count}
      top_n: {options: [5, 10, 20], default: 10}
      min_claims: {options: [0, 30], default: 0}
    produces: provider_ranking -> {metric, top_n, min_claims, rows: [{provider_npi, specialty, network_status, n: int, value: float}]}   # + provider_ranking.csv (rendering_npi joined to providers)
  - write_report
golden conventions: group_by ⊇ [provider_specialty, network_status]; metrics ⊇ [claim_count, paid_amount_sum, denial_rate, fraud_rate];
  denominator adjudicated_claims; min_group_size 30 and the resulting flags; exact n and denial_rate per network_status and per specialty;
  provider_ranking top 10 by claim_count exact; join_check for medical_claims.rendering_npi->providers.provider_npi with unmatched_left 0;
  show_denominators true; caveats ⊇ [synthetic_data, small_groups, association_not_causation].
```

## T4 — Denial analysis

```yaml
task_id: T4
input_tables: [medical_claims]
tags: [denials, denial_codes, rates, denominators, segments, small_groups, missingness]
required_artifacts: [denial_code_ranking.csv, denial_rates_by_segment.csv, denial_rate_by_segment.png, report.md, metrics.json]
components:
  - load_tables
  - id: denial_code_ranking   # default_selected: true
    params:
      scope: {options: [denied_claims, all_claims], default: all_claims}          # share = n / claims in scope
      quantify_missing: {options: [none, overall, by_status], default: overall}
    produces: denial_code_ranking -> {scope, codes: [{code, n: int, share: float}],
                 missing_denial_codes: {definition: str, overall: int, overall_denominator: int, among_denied: int, among_denied_denominator: int,
                                        by_status?: {status: {missing: int, n: int}}}}    # + denial_code_ranking.csv
  - id: denial_rate_by_segment  # default_selected: true
    params:
      segments: {multi: true, default: [claim_type], options: [claim_type, provider_specialty, network_status, place_of_service, auth_required_flag]}
      denominator: {options: [all_claims, adjudicated_claims], default: all_claims}
      min_group_size: {options: [0, 30, 50, 100], default: 0}
    produces: denial_rate_by_segment -> {denominator_option, min_group_size, segments: {segment: {value: {numerator: int, denominator: int, rate: float, small_group_flag: bool}}}}
              # + denial_rates_by_segment.csv, denial_rate_by_segment.png
  - write_report
golden conventions: codes ranking exact with scope denied_claims (shares sum to 1); among_denied = 0 of 1286; overall = 11559 of 12845; by_status present;
  all five segments; denominator adjudicated_claims; exact rates; min_group_size 30; show_denominators true; caveats ⊇ [synthetic_data, small_groups].
```

## T5 — Fraud-pattern exploration

```yaml
task_id: T5
input_tables: [medical_claims, members]
tags: [fraud, exploration, class_imbalance, leakage, protected_attributes, comparison, prevalence]
required_artifacts: [fraud_comparison.csv, fraud_prevalence.png, report.md, metrics.json]
components:
  - load_tables
  - id: class_prevalence      # default_selected: true; params: {}
    produces: class_prevalence -> {positives: int, negatives: int, total: int, prevalence: float, imbalance_ratio: float}   # + fraud_prevalence.png
  - id: feature_comparison    # default_selected: true
    params: {features: {multi: true, default: [claim_type, billed_amount, fraud_pattern_type],
                        options: [claim_type, cpt_category, place_of_service, provider_specialty, network_status, billed_amount, allowed_amount, paid_amount,
                                  service_units, length_of_stay, er_flag, auth_required_flag, fraud_pattern_type, high_cost_flag,
                                  member_sex, member_race_ethnicity, member_age_band, member_payer_type]}}
    produces: feature_comparison -> {feature: {kind: categorical|numeric, n_flagged: int, n_unflagged: int,
                 flagged: {value: share} | {mean, median}, unflagged: {value: share} | {mean, median}}}   # member_* via m:1 join on member_id; + fraud_comparison.csv
  - id: leakage_assessment    # default_selected: false; params: {}
    produces: leakage_risks -> {label_derived_fields: [fraud_pattern_type], id_fields: [..], protected_attributes: [..], flagged_in_plan: [features from the plan that are label-derived or protected]}
  - write_report
golden conventions: prevalence 647 / 12845 and imbalance_ratio; features ⊇ 4 permitted features and ∩ [fraud_pattern_type, member_sex, member_race_ethnicity, member_age_band] = ∅ (critical);
  expected billed_amount means flagged/unflagged and claim_type shares (tolerance 1e-6); leakage_assessment present and lists fraud_pattern_type;
  caveats ⊇ [synthetic_data, class_imbalance, association_not_causation, no_operational_use].
```

## T6 — Baseline fraud model

```yaml
task_id: T6
input_tables: [medical_claims]
target: fraud_label
tags: [modeling, fraud, classification, leakage, splits, seeds, metrics, class_imbalance]
required_artifacts: [model_metrics.json, confusion_matrices.png, pr_curves.png, feature_list.json, report.md, metrics.json]
components:
  - load_tables
  - id: feature_set           # default_selected: true
    params: {features: {multi: true, default: [claim_type, billed_amount, paid_amount, fraud_pattern_type],
                        options: [claim_type, cpt_category, place_of_service, provider_specialty, network_status, billed_amount, allowed_amount, paid_amount,
                                  service_units, length_of_stay, er_flag, elective_flag, preventive_flag, auth_required_flag, primary_icd10_cm, drg_present,
                                  high_cost_flag, fraud_pattern_type, claim_id, member_id, rendering_npi]}}
    produces: feature_set -> {features: [..], n_categorical: int, n_numeric: int, id_fields_present: [..], label_derived_present: [..]}   # + feature_list.json; drg_present = drg_code.notna()
  - id: split                 # default_selected: true
    params: {test_size: {options: [0.2, 0.25, 0.3], default: 0.25}, stratify: {options: [true, false], default: false}}
    produces: split -> {test_size, stratify, seed, n_train, n_test, prevalence_train: float, prevalence_test: float}
  - id: preprocessing         # default_selected: true
    params: {fit_on: {options: [train_only, all_data], default: all_data}, scaling: {options: [none, standard], default: none}}
    produces: preprocessing -> {fit_on, scaling, n_features_out: int}
  - id: models                # default_selected: true
    params: {models: {multi: true, default: [logistic_regression], options: [logistic_regression, random_forest, gradient_boosting]},
             class_weight: {options: [none, balanced], default: none}}
    produces: models -> {name: {precision, recall, f1, pr_auc, roc_auc, confusion_matrix: [[tn, fp], [fn, tp]], threshold: 0.5, n_test: int}}   # + model_metrics.json, confusion_matrices.png, pr_curves.png
  - write_report
golden contracts: features ∩ [fraud_pattern_type, claim_id, member_id, rendering_npi] = ∅ (critical); split test_size 0.25 and stratify true;
  preprocessing fit_on train_only (critical); models ⊇ {logistic_regression} and ∩ {random_forest, gradient_boosting} ≠ ∅; every model reports the six metrics;
  roc_auc ∈ [0.5, 1.0], pr_auc ∈ [prevalence_test, 1.0]; prevalence_train/test present; caveats ⊇ [synthetic_data, class_imbalance, model_limitations, no_operational_use].
```

## T7 — High-cost claim identification

The split is a plain random split of rows (no stratification, the target does not exist yet); the threshold is then computed on the training partition (`train_only`) or on all rows (`all_data`).

```yaml
task_id: T7
input_tables: [medical_claims]
tags: [modeling, high_cost, threshold, percentile, leakage, splits, seeds, ranking, metrics]
required_artifacts: [model_metrics.json, threshold.json, feature_list.json, precision_at_k.png, report.md, metrics.json]
components:
  - load_tables
  - id: split                 # default_selected: true
    params: {test_size: {options: [0.2, 0.25, 0.3], default: 0.25}}
    produces: split -> {test_size, seed, n_train, n_test}
  - id: target_definition     # default_selected: true
    params:
      amount_column: {options: [paid_amount, billed_amount, allowed_amount], default: paid_amount}
      percentile: {options: [90, 95, 99], default: 95}
      threshold_source: {options: [train_only, all_data], default: all_data}
    produces: target_definition -> {amount_column, percentile, threshold_source, threshold_value: float, positive_rate_train, positive_rate_test, n_positive_train, n_positive_test}
              # threshold_value = numpy.percentile(values, percentile) (linear interpolation); positive = amount > threshold_value; + threshold.json
  - id: feature_set           # default_selected: true
    params: {features: {multi: true, default: [claim_type, billed_amount, allowed_amount],
                        options: [claim_type, cpt_category, place_of_service, provider_specialty, network_status, service_units, length_of_stay, er_flag, elective_flag,
                                  preventive_flag, auth_required_flag, primary_icd10_cm, drg_present, billed_amount, allowed_amount, paid_amount, member_oop, cob_amount,
                                  high_cost_flag, claim_id, member_id]}}
    produces: feature_set -> {features, n_categorical, n_numeric, id_fields_present, target_derived_present: [..]}   # + feature_list.json
  - id: preprocessing         # same as T6
  - id: models                # default_selected: true
    params: {models: {multi: true, default: [logistic_regression], options: [logistic_regression, random_forest, gradient_boosting]}}
    produces: models -> {name: {pr_auc, roc_auc, precision_at_top_5pct, recall_at_top_5pct, n_test: int}}   # top 5 % of test rows by score; + model_metrics.json, precision_at_k.png
  - write_report
golden contracts: amount_column paid_amount, percentile 95, threshold_source train_only (critical), threshold_value exact for seed 42 / test_size 0.25 (tolerance 0.01);
  features ∩ [billed_amount, allowed_amount, paid_amount, member_oop, cob_amount, high_cost_flag, claim_id, member_id] = ∅ (critical); fit_on train_only (critical);
  models ⊇ {logistic_regression} and one tree model; metric ranges; caveats ⊇ [synthetic_data, model_limitations, no_operational_use].
```

## T8 — Executive brief

Reads the **final attempt** (highest `attempt_<n>` directory containing `metrics.json`) of each source task under the same `artifacts/tasks/<run_id>/<condition>/`. A missing source is recorded as `{"task_id": ..., "status": "missing"}` — values are never invented.

```yaml
task_id: T8
input_tables: []
tags: [communication, executive_brief, traceability, caveats, synthesis, limitations]
required_artifacts: [executive_brief.md, findings.json, report.md, metrics.json]
components:
  - id: collect_findings      # default_selected: true
    params: {sources: {multi: true, default: [T2, T6], options: [T1, T2, T3, T4, T5, T6, T7]}}
    produces: findings -> [{task_id, metric_key, label, value, numerator?, denominator?, source_path}]   # + findings.json
    extraction map: T1 tables row counts · T2 denial_rate (+ numerator/denominator), claim_volume.total_claims, financial_summary.paid_amount.sum, fraud_prevalence ·
                    T3 group_comparison network_status denial rates · T4 top denial code · T5 class_prevalence · T6 per model roc_auc/pr_auc + feature count ·
                    T7 threshold_value + per model pr_auc
  - id: brief_sections        # default_selected: true
    params:
      sections: {multi: true, default: [key_findings, model_results], options: [key_findings, model_results, limitations, synthetic_caveats, next_steps, methodology]}
      causal_language: {options: [avoid, allow], default: allow}      # allow → "X drives Y"; avoid → "X is associated with Y"
      cite_artifacts: {options: [true, false], default: false}         # every numeric statement ends with [source: <path>]
    produces: brief -> {sections, causal_language, cite_artifacts, word_count: int, n_numeric_statements: int, n_cited_statements: int}   # + executive_brief.md (≤ 600 words)
  - write_report
golden (YAML): sources ⊇ [T2, T5, T6, T7] and ∩ [T3, T4] ≠ ∅; sections ⊇ [key_findings, model_results, limitations, synthetic_caveats, next_steps];
  cite_artifacts true (n_cited_statements == n_numeric_statements, critical); causal_language avoid — forbidden phrases in executive_brief.md: "causes", "drives", "leads to", "because of";
  caveats ⊇ [synthetic_data, no_operational_use].
```

## Rubric mapping guidance (A3)

| Dimension | Typical checks |
|---|---|
| correctness | golden values (exact / tolerance), contract choices (denominator option, date column, threshold source, split params) |
| completeness | required components executed, required artifacts exist, required sources/sections present |
| reproducibility | `metrics.json` has seed + plan_sha256, every listed artifact exists, split/threshold recorded, `feature_list.json` present |
| statistical_discipline | denominators shown, small-group flags, leakage/protected exclusions, stratification, fit_on train_only, prevalence reported |
| communication | required caveats, `cite_artifacts`, `show_denominators`, no causal phrasing (T8), brief sections |

Mark as **critical**: leakage/protected exclusions (T5–T7), `fit_on train_only` (T6–T7), `threshold_source` (T7), the denominator definition of the headline rate (T2, T4), required artifacts. Score per `docs/LEAD_DESIGN_DECISIONS.md` §7; `pass_threshold` 3.5.
