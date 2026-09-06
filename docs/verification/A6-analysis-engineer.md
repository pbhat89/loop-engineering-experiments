# A6 — Analysis engineer: verification note

Date: 2026-09-07. Deterministic executor for T1–T8 built against `docs/LEAD_CATALOGUE_SKELETON.md`
(binding) and `docs/LEAD_DESIGN_DECISIONS.md` §3–§5, §11, §14. `config/tasks.yaml` did not exist while
this was built; the executor carries its own transcription of the skeleton in `src/analyses/catalogue.py`.

## Deliverables

| Unit | Path |
|---|---|
| 1 | `src/task_runner.py`, `src/analyses/__init__.py`, `src/analyses/common.py`, `src/analyses/catalogue.py` |
| 2 | `src/analyses/t1_recon.py`, `src/analyses/t2_portfolio.py` |
| 3 | `src/analyses/t3_providers.py`, `src/analyses/t4_denials.py` |
| 4 | `src/analyses/t5_fraud_exploration.py` |
| 5 | `src/analyses/t6_fraud_model.py`, `src/analyses/modeling.py` (shared feature/preprocessing/estimator helpers for T6/T7) |
| 6 | `src/analyses/t7_high_cost.py` |
| 7 | `src/analyses/t8_brief.py` |
| 8 | `tests/test_task_runner.py` |

## Commands run

```bash
cd "d:/Projects/SkillRL/claims-skill-loop"
uv run python -m src.agent_tracker start --agent A6 --task "Deterministic executor T1-T8"
# smoke runs of every task with the default plan and an expert plan (scratch driver, outputs deleted afterwards)
uv run --extra dev pytest tests/test_task_runner.py -q -s          # per-task runtime prints
uv run --extra dev pytest tests/test_task_runner.py -o addopts="" -q
```

## Results

`22 passed in 68.44s` (second run; first run after two test-expectation fixes also all green).
The suite skips with a reason when `data/raw/medical_claims.csv` or `members.csv` is absent.

Per-task wall time (real data, seed 42; from the `-s` run):

| Task | default plan | expert plan (run twice for determinism) |
|---|---:|---:|
| T1 | 0.2 s | 0.6 s / 0.8 s |
| T2 | 0.3 s | 1.2 s / 1.3 s |
| T3 | 0.3 s | 1.0 s / 0.9 s |
| T4 | 0.2 s | 1.6 s / 1.6 s |
| T5 | 0.2 s | 0.5 s / 0.4 s |
| T6 | 2.5 s | 18.4 s / 18.7 s (LR + RF(200 trees, n_jobs=1) + HGB on 107 encoded features) |
| T7 | 0.5 s | 10.6 s / 10.3 s |
| T8 | 0.1 s | 0.1 s / 0.1 s |

What the tests assert, per task and plan: `status == ok`; every required artifact exists (expert plan) or
`metrics.json`/`report.md` exist (default plan — the naive T3 plan cannot produce `provider_ranking.csv`
because `provider_ranking` is not `default_selected`; that is the evaluator's business, not a bug);
every produced metric key of every executed component is present with the skeleton's sub-keys;
`metrics.json` on disk equals the returned `metrics`; all artifacts live inside `output_dir`; the report has
the fixed sections, `## Caveats` iff caveats were requested, every results bullet cited when
`cite_artifacts`, `numerator / denominator = rate` when `show_denominators`; determinism (same plan twice into
the same directory → identical metrics except `generated_at`, identical artifact list). Documented data facts
are checked: all-null medical columns, 36 adjudication-before-service-end rows, `no_match` pharmacy NPI pair,
1286 / 12339 adjudicated denial rate, 647 / 12845 fraud prevalence, 36 months for `service_date_from`, exact
status mix, 10 denial codes summing to 1286 with 11559 / 0 missing overall / among denied, imbalance ratio,
stratified prevalences, positives = amount > p95(train), leakage-free feature sets, T8 `n_cited ==
n_numeric`, no causal phrases under `avoid`, brief ≤ 600 words, missing sources recorded not invented.

Error paths: unknown component → `errors[0].type == unknown_component`, other components still run
(status `partial`); T6 `models`/`preprocessing` without `feature_set` → `missing_dependency`; invalid option →
`invalid_param` for that component only; nothing runnable → `status error` with `metrics.json` and `report.md`
still written; an exception inside a component (monkeypatched) → `runtime_error`, execution continues.

## Interface notes for the lead (additions, never renames)

- `denial_code_ranking` carries an extra `quantify_missing` field; with `quantify_missing=none` the
  `missing_denial_codes` sub-object is omitted (nothing was quantified) — the evaluator will see it missing.
- T4 `small_group_flag` uses the segment's denominator count (rows counted under the chosen denominator);
  T3 uses `n` (all claims in the group) as the skeleton's shape implies.
- T7 `target_derived_present` uses the fixed set {billed_amount, allowed_amount, paid_amount, member_oop,
  cob_amount, high_cost_flag} regardless of `amount_column`.
- Categorical features are one-hot encoded after filling nulls with the literal `"missing"`; numeric features
  pass through a median imputer (no nulls in practice) before the optional `StandardScaler`.
- `gradient_boosting` needs a dense matrix; a design wider than 40M cells (e.g. `claim_id` one-hot) is refused
  for that model only and recorded as a `runtime_error` on `models` while the other models' results stay.
- T2 `claim_volume` writes `claims_status_distribution.png` for `claim_status` and `claim_volume_by_<col>.png`
  for any other `by` column when `figure=true`.
- `load_tables` is not a hard dependency: any component loads the tables it needs; the `tables` head key is
  always filled from whatever was loaded.
- Data observation worth a rubric look: with leakage-free features the synthetic `fraud_label` is essentially
  unpredictable (ROC-AUC 0.499 / 0.498 / 0.515 for LR / RF / HGB, PR-AUC ≈ prevalence). A strict
  `roc_auc ∈ [0.5, 1.0]` check will fail honest models by rounding noise; a tolerance (e.g. ≥ 0.45) or a
  PR-AUC ≥ prevalence check would be fairer.
