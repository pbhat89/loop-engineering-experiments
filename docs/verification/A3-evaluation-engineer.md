# A3 — evaluation engineer: verification notes

Date: 2026-09-07. Owner: A3. Scope: `config/tasks.yaml`, `config/rubric.yaml`, `src/build_goldens.py`, `goldens/`,
`src/evaluator.py`, `tests/test_evaluator.py`, `artifacts/reports/golden_review.md`. Binding contract:
`docs/LEAD_CATALOGUE_SKELETON.md`; interface: `docs/plan.md` §11, §14, §15; brief Addendum A.

## Deliverables and how each was verified

| unit | artifact | verification performed |
|---|---|---|
| 1–2 | `config/tasks.yaml` (T1–T8, suite_version "1") | parses; ids/options/defaults transcribed from the skeleton; every param has description/options/default; `validate_plan(default_plan(spec), spec)` returns no errors for all eight tasks; objectives contain no option names (`test_objectives_do_not_name_options_as_correct`) |
| 3 | `config/rubric.yaml` (rubric_version "1", pass_threshold 3.5) | parses; 152 checks (T1 15, T2 21, T3 20, T4 17, T5 18, T6 22, T7 24, T8 15); every `related_components` entry is a valid component / param / option of its task; every required artifact has a critical `artifact_exists` check; every check target root is a produced metric key (or `plan:`), a required artifact, a catalogue component or a golden caveat id |
| 4–5 | `src/build_goldens.py`, `goldens/T1…T7*.json`, `goldens/T8_executive_brief_rubric.yaml` | `uv run python -m src.build_goldens` then `uv run python -m src.build_goldens --check` → "golden pack check clean: 8 files match the recomputation (built_at ignored)", exit 0; imports only pandas/numpy/yaml, `sklearn.train_test_split` (the skeleton's split convention), `src.profile_data.load_table` and `src.utils` — never `src/task_runner.py` or `src/analyses/` |
| 6 | `artifacts/reports/golden_review.md` | 52 rows (task, metric, value, definition, tolerance, sanity); 0 sanity failures — this is the Phase 1.5 user checkpoint (G3) |
| 7–8 | `src/evaluator.py` | nine check kinds, dotted-path resolution with dotted keys and `*`, scoring per §7 (null dimensions excluded), critical logic, `observed: null` on missing metrics, feedback items with `related_components`/`reusable`/`applicable_task_ids` copied from the rubric, `rubric_sha256` / `golden_sha256` / `freeze_sha256` |
| 9 | `tests/test_evaluator.py` | `uv run --extra dev pytest tests/test_evaluator.py -q` → **24 passed** (parse + cross-reference tests, one unit test per kind, scoring/feedback tests, ideal/naive/single-critical T2 scenarios, `build_goldens --check`) |
| 10 | integration dry run + this note | hand-built T2 and T6 results (see below); `uv run --extra dev pytest tests/test_graph_routes.py -q` → **11 passed** (unchanged) |

## Headline golden values (all from `goldens/`, definitions in `artifacts/reports/golden_review.md`)

| value | golden | definition |
|---|---|---|
| denial rate (T2) | **0.104222** (1286 / 12339) | Denied / adjudicated (Paid + Denied + Adjusted; 506 Pended excluded); tolerance 1e-6 |
| fraud prevalence (T2, T5) | **0.050370** (647 / 12845) | fraud_label == 1 / all medical claims; imbalance ratio 18.85 |
| monthly claim counts (T2) | 36 months 2021-01..2023-12, **302–405 per month**, sum 12845, 0 unparseable | count per %Y-%m of `service_date_from` |
| financial sums (T2) | billed 21,254,208.81 · allowed 12,175,223.45 · paid 9,783,415.77 | sums over all rows; tolerance 0.01 (means, median, p90, p99 also frozen) |
| T7 threshold | **3198.988** (tolerance 0.01) | `numpy.percentile(paid_amount[train], 95)`, train = `train_test_split(np.arange(12845), test_size=0.25, random_state=42, shuffle=True)`; positives train 482 / 9633, test 150 / 3212. All-data percentile would be 3161.934, so the check discriminates `train_only` from `all_data` |
| split sizes (T6, T7) | n_train 9633, n_test 3212 | same split call (T6 stratified on fraud_label; prevalence train 0.05035 / test 0.05044) |
| denial codes (T4) | CO-15 241, CO-4 206, CO-11 147, CO-18 138, PR-1 120, CO-27 115, CO-97 99, CO-50 87, CO-29 82, CO-119 51 | among denied claims; shares sum to 1; missing codes 11559 / 12845 overall, 0 / 1286 among denied |
| T1 | rows 500 / 150 / 12845 / 18310 / 10627; 7 all-null medical columns; 36 adjudication-before-service-end; six join pairs incl. two `no_match` | see review page |

## Integration dry run (real rubric + goldens, hand-built results following the skeleton)

```
T2 ideal : total 4.00 passed=True  (21/21)
T2 naive : total 1.28 passed=False (9/21)  critical: T2.denial_rate_value, T2.denial_rate_denominator
           feedback e.g. T2-denial_rate_value -> [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}]
                         T2-monthly_date_column -> monthly_trend.date_column=service_date_from
                         T2-caveat_synthetic -> write_report.caveats=[synthetic_data, descriptive_only]
T2 ideal except all_claims denominator: total <= 3.3, passed=False (test_single_critical_convention_lands_below_threshold)
T6 ideal : total 4.00 passed=True  (22/22)
T6 naive : total 2.24 passed=False (14/22) critical: T6.no_leakage_features, T6.fit_on_train_only
           feedback e.g. T6-no_leakage_features observed=["fraud_pattern_type"] -> feature_set.features=[16 permitted features]
                         T6-fit_on_train_only -> preprocessing.fit_on=train_only ; T6-split_stratified -> split.stratify=true
```

`freeze_sha256` is `null` until the lead writes `config/freeze_manifest.json` (L0-8) after the user's golden review.

## Additions to the skeleton (reported, nothing renamed)

- `config/tasks.yaml`: `shared_conventions` block (documentary); `artifacts:` list per component (the side files the skeleton lists after "+"); `produces[].shape` written as strings; `target: fraud_label` on T6 as in the skeleton.
- `config/rubric.yaml`: ninth kind `component_executed`; optional `golden_key` when two checks read one metric path (`models_logistic`, `models_tree`, `models_metrics`, `findings_core_sources`, `findings_segment_source`, `group_comparison.metrics_each_group`); per-check `issue_type`; optional `fields` narrowing for `field_excluded`; `evaluator_version`. Check counts (15–24 per task) exceed the 8–14 aim because the skeleton makes every required artifact a critical check and the modelling tasks have six artifacts each.
- Goldens: `reference` sections (informational values such as the all-data threshold, stratified prevalences), `expected_metrics` entries with `values` (a dict of numbers compared key by key), T8 carries `forbidden_phrases`, `max_words`, `required_findings`, `artifact_reference_requirement`.
- Evaluator output: extra fields beyond §7 — `golden_version`, `task_id`, `pass_threshold`, `critical_failures`, `n_checks`, `n_passed`; each feedback item also carries `check_id`, `observed`, `expected`, `detail` (so `resolved` can be tracked by `check_id`). `rubric_sha256` / `golden_sha256` are SHA-256 of the canonical JSON of the dicts passed to `evaluate` (the freeze manifest holds the file hashes).

## Conventions the executor (A6) must follow for the goldens to match (skeleton left them implicit)

1. `date_ranges` is keyed by the option string `medical_claims.service_date_from` (table-qualified), as are `duplicates` keys and `join_check` pairs.
2. Group / segment values are keyed by `str(value)`: `auth_required_flag` → `"0"` / `"1"`; composite `"<specialty>|<network_status>"`.
3. T3 `group_comparison` groups carry `n` (all claims in the group), `small_group_flag = n < min_group_size`; T4 `small_group_flag = denominator < min_group_size` (at 30 both definitions give identical flags on this data — every group is larger).
4. `provider_ranking.rows` need `provider_npi`, `specialty`, `network_status`, `n`; rows are matched order-insensitively because of ties inside the top 10 (106 ×2, 102 ×3; no tie at the 10th/11th boundary).
5. Caveats are satisfied when the id is in `report.caveats` **or** a keyword appears in `report.md` / `executive_brief.md` (keywords in `goldens/*.required_caveats`).
6. Artifacts are located via the `artifacts` list, `metrics_path` / `report_path`, then `output_dir/<name>` (an unlisted file still passes; the detail says "not listed").
7. `metrics.json` must carry `seed` (checked in T6/T7) and `plan`; `report.md` denominators print as `numerator / denominator = rate` (regex `\d[\d,]*\s*/\s*\d[\d,]*\s*=\s*\d`); citations as `[source: ...]`.

## Open issues / observations for the lead

- `FixtureProvider._plan` merges multi-valued `related_components` params by union, so a leakage remediation (remove `fraud_pattern_type`) can never be applied by the stub and `_feedback_applied` will report it as not incorporated; the stub baseline therefore keeps failing T5–T7 leakage checks by construction. The manual operator is unaffected. Not an A3 file — flagged, not changed.
- `pass_threshold` 3.5 in `config/experiment.yaml` equals the rubric (the lead's assertion holds).
- After the user review, the lead should run `uv run python -m src.build_goldens --check` once more and then `uv run python -m src.run_experiment freeze`.

## Commands

```
uv run python -m src.build_goldens && uv run python -m src.build_goldens --check
uv run --extra dev pytest tests/test_evaluator.py -q          # 24 passed
uv run --extra dev pytest tests/test_graph_routes.py -q       # 11 passed
```
