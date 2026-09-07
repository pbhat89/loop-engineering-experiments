# Loop engineering with Markdown skills — experiment 2: a rule learner that learns house conventions

**Status:** populated 2026-09-07 (L0) from `logs/*.jsonl`, `logs/runs/run_004.json`, `artifacts/reports/run_summaries.json`, `skills/evolved/run_004/`, `artifacts/figures/`, `goldens/` and `config/freeze_manifest.json`. **Public article** (Substack-ready, PB voice): `articles/loop-engineering-markdown-skills/article.md` — web version at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee. Experiment 1's write-up is preserved unchanged at `archive/experiment-1_run_001/docs/writeup_run_001.md`. Synthetic data; educational demonstration; nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory or operational evidence.

## 1. What changed since experiment 1

Experiment 1 asked a Fable 5.1-class stateless planner to work eight claims-analysis tasks from briefs that stated the house conventions. It never failed, the evaluator never issued feedback, and a loop that learns from feedback had nothing to learn (0 evolved skills; all scores 4.00 first attempt). Rather than argue with a ceiling, experiment 2 replaces the planner with something that *starts ignorant of the conventions*: a deterministic **rule learner** (`src/rule_learner.py`, runtime mode `rule_learner`, D-18) that

- starts every task from the catalogue's textbook defaults (all-claims denominators, adjudication date for trends, no small-group flag, preprocessing fitted on all data, leaky default features, no caveats);
- changes a choice only when the evaluator's feedback on the current task recommends it, or when a retrieved skill carries a machine-readable convention (`param:<name>=<value>`, `list:<name>+=<value>`, `list:<name>-=<value>`, `component:<id>`);
- generalises conventions **by parameter name** — "any `denominator` means adjudicated claims", "any `min_group_size` is 30" — and proposes one skill per task containing only conventions no existing skill already holds, with the feedback ids as provenance.

Everything else is unchanged: the same frozen task suite, rubric (152 checks) and golden pack (`freeze_sha256 1566c569…`), the same LangGraph, the same three conditions, `max_retries = 2`, and the stopping rule "pass → finalise". The runtime still makes no model API calls; in this experiment it makes no LLM calls of any kind. Two fixes were made between the first and the reported run and are logged as D-19: the evaluator's caveat-keyword check could be satisfied by the condition name `baseline` appearing in a report's own header (evaluator 1.0 → 1.1), and the learner now learns list *removals* only from exclusion-type feedback. Runs `run_002` and `run_003` are archived; `run_004` is reported.

## 2. Results — quality on the first attempt (`logs/experiment_events.jsonl`, `status = attempt`, `attempt = 1`)

| condition | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | mean | mean T2–T8 |
|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 1.38 | 1.28 | 0.73 | 1.18 | 2.29 | 2.24 | 1.93 | 1.21 | 1.53 | 1.55 |
| reflection_only | 1.38 | 1.28 | 0.73 | 1.18 | 2.29 | 2.24 | 1.93 | 1.21 | 1.53 | 1.55 |
| skill_learning | 1.38 | **1.55** | **1.36** | **2.21** | 2.29 | **3.02** | **3.18** | **1.55** | **2.07** | **2.17** |

Baseline and reflection_only are identical on first attempts by construction (neither carries anything between tasks), which is also the check that the evaluator now grades conditions symmetrically. `skill_learning` is identical on T1 (nothing learned yet) and higher on six of the seven later tasks; T5 is unchanged because its first-attempt failures are task-specific (feature lists and a leakage-assessment component) rather than conventions.

Mean first-attempt score by rubric dimension, T2–T8:

| dimension | baseline = reflection_only | skill_learning |
|---|---|---|
| correctness | 2.47 | 2.47 |
| completeness | 1.49 | 1.65 |
| reproducibility | 3.45 | 3.45 |
| statistical discipline | 0.12 | **0.81** |
| communication | 0.23 | **2.43** |

The gain is where a convention *is* the requirement — denominators stated, small groups flagged, leakage exclusions, caveats and citations in the report — and absent where correctness depends on task-specific scope (which segments, which sources, which features).

## 3. Results — reliability (`logs/experiment_events.jsonl`)

| condition | first-attempt passes | retries | execution errors | final score | operator steps (cap 64) |
|---|---:|---:|---:|---:|---:|
| baseline | 0 / 8 | 8 | 0 | 4.00 on every task | 16 |
| reflection_only | 0 / 8 | 8 | 0 | 4.00 on every task | 24 |
| skill_learning | 0 / 8 | 8 | 0 | 4.00 on every task | 38 |

Every task in every condition needed exactly one revision and then passed: the evaluator's feedback carries the exact fix (`related_components`), so the second attempt is always correct. The skills raise where the first attempt *starts*, not yet whether it passes — T6 and T7 reached 3.02 and 3.18 first-attempt in `skill_learning` against a pass threshold of 3.5. Reliability in the sense of fewer retries would need conventions to cover a task's whole rubric, which they do not.

## 4. Results — skills (`logs/skill_events.jsonl`, `skills/evolved/run_004/`)

- Proposed 6, validated 6, persisted 6 (one after each of T1–T6; T7's and T8's reflections produced nothing new for ≥ 2 remaining tasks). No rejections of a real proposal; the two `skill_rejected` events at T7/T8 are the validator recording a null proposal.
- Retrievals 61 (foundational + evolved, top-8 by tag/keyword score), reuse events 22. Reuse counts: skill 001 (after T1: data-contract scope, duplicate keys, date ranges, join pairs, synthetic/sample caveats) 7; 002 (after T2: adjudicated denominator, `service_date_from`, quantiles, `show_denominators`) 5; 003 (after T3: `min_group_size = 30`, both grouping fields, provider ranking, small-group/association caveats) 5; 005 (after T5: leakage assessment, permitted comparison features, `fraud_pattern_type` excluded) 3; 006 (after T6: stratified 25 % split, `fit_on = train_only`, a tree model) 2; **004 (after T4: denial-code scope and the five segments) 0 — never reused, the bloat case the brief asked to be reported.**
- Validated *useful* skills (persisted, then retrieved and applied on a later task): 001, 002, 003, 005, 006.
- Over-generalisation observed: the T5 skill's permitted-feature additions (including `allowed_amount` and `paid_amount`, legitimate for a fraud comparison) fire on T7, where amount fields are target-derived. T7 still failed its first attempt in `skill_learning` — at 3.18 rather than baseline's 1.93 — and the T7 feedback corrected it. A convention learned by parameter name can be wrong for a task with a different target; the loop absorbs that through the same feedback path.

Figures generated from these logs: `artifacts/figures/skill_accumulation.png`, `skill_utility.png`, `skill_lifecycle_graph.png` (observed lifecycle, not the designed topology), `rubric_heatmap.png`, `reliability_curve.png`, `learning_curve.png` (final scores, flat at 4.00 — the informative curve is the first-attempt one above, drawn in `articles/loop-engineering-markdown-skills/assets/first_attempt_by_task.png`).

## 5. How the decisions happened

No LLM was involved in `run_004`: every plan, reflection and proposal was produced by `rule-learner-v1` (`provider_mode: rule_learner`, `operator: deterministic-rule-learner`, recorded on all 72 experiment events). The run is therefore exactly reproducible (`uv run python -m src.run_experiment run-auto --run-id <new id> --mode rule_learner` regenerates the same numbers) and cost no model tokens. That is also its main limitation: the "intelligence" being demonstrated is the loop and its memory, not a model's reasoning.

## 6. The frozen target

Unchanged from experiment 1: Hugging Face `xpertsystems/hlt008-sample` at revision `7309ddb30e67468748b7aa9182d8517fe28c2f9c` (CC-BY-NC-4.0, fully synthetic); 52 golden values reviewed by the user on 2026-09-07 and frozen by hash; e.g. denial rate 0.104222 = 1,286 / 12,339 adjudicated claims, fraud prevalence 0.050370, high-cost threshold 3,198.99 from the training split. *The agent was measured on whether it produced the expected claims metrics, artifacts, modelling safeguards and caveats — not on whether it thought its own answer was good.*

## 7. What did not work / surprises

1. **The evaluator was not condition-blind** until D-19: a caveat keyword ("baseline" for *model limitations*) matched the condition's own name in the report. Symmetry between baseline and reflection_only on first attempts is now a standing check.
2. **Reflection without memory is worth nothing here.** With the fix carried by the feedback itself, `reflection_only` costs eight extra operator steps and changes no outcome.
3. **Conventions transfer, scope does not.** Six of seven later tasks improved on the first attempt, none passed on it. The skill after T4 was never reused because it only encodes T4's segment list.
4. **Learned removals must be restricted.** Version 1 of the learner "unlearned" caveats that a golden merely did not list; only exclusion-type feedback (leakage, prohibited or protected fields) should teach a removal.

## 8. Limitations

A rule-based learner with no language understanding; conventions keyed by parameter name only; a single deterministic run (so no variance to report, and no claim of significance); a catalogue-bounded planner; retrieval by tag overlap with `k = 8`; `skill_learning` still bundles access to six foundational skills with evolved-skill accumulation (the foundational skills are inert for this learner, so here the bundle is harmless, but it remains in the design); deterministic, structural evaluation of prose; synthetic data whose distributions come from a generator. Findings are illustrative.

## 9. Reproduce it

```bash
uv sync --extra dev
uv run python -m src.download_data && uv run python -m src.profile_data
uv run python -m src.build_goldens --check                              # golden pack reproduces from the data
uv run python -m src.run_experiment run-auto --run-id run_005 --mode rule_learner
uv run python scripts/summarize_run.py --run-id run_005
uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py   # set RUN inside if you change the id
uv run python scripts/pipeline.py verify
```

## 10. Draft LinkedIn post (≤ 1,300 characters)

Second attempt at "loop engineering" with LangGraph, after the first one ceilinged out (a strong planner never failed, so it never learned).

This time the planner is deliberately naive: a rule learner that starts every claims-analysis task from textbook defaults and only changes a choice when the evaluator's feedback tells it to. What it learns, it writes into versioned Markdown skills as conventions — "any denominator means adjudicated claims", "small groups are < 30" — and retrieves on the next task.

Eight frozen tasks, three conditions, a golden pack hashed before the run, zero model calls, two minutes end to end.

Result: first-attempt quality rose from 1.55 to 2.17 (out of 4) on tasks 2–8 with persistent skills, driven almost entirely by statistical discipline (0.12 → 0.81) and communication (0.23 → 2.43). Correctness didn't move — conventions transfer, task-specific scope doesn't — and no task passed first time, so retries stayed at one per task. One learned skill was never reused. Reflection without memory changed nothing.

Synthetic data, one deterministic run, illustrative. Repo, logs and the full write-up: [link].

## Appendix — evidence index

| Claim | Source | Field(s) |
|---|---|---|
| First-attempt scores per task and condition | `logs/experiment_events.jsonl` (run_004, `status = attempt`, `attempt = 1`) | `evaluator_score_total`, `evaluator_score_by_dimension` |
| Retries, errors, final scores, first-attempt passes | `logs/experiment_events.jsonl` (`status = done`) | `retry_count`, `execution_errors`, `first_attempt_passed`, `evaluator_score_total` |
| Operator steps 16 / 24 / 38 | `logs/runs/run_004.json` | `operator_steps_used` |
| 6 skills proposed/validated/persisted; 61 retrievals; 22 reuses; per-skill counts | `logs/skill_events.jsonl`; `skills/evolved/run_004/*.md`; `skills/index.json` | `event`, `skill_id`, `reuse_count` |
| Provider metadata and evaluator version | `logs/experiment_events.jsonl` | `provider_mode`, `operator`, `model_identifier`, `evaluator_version` |
| Golden values and freeze | `goldens/*.json`, `artifacts/reports/golden_review.md`, `config/freeze_manifest.json` | `expected_metrics`, `freeze_sha256` |
| Evaluator fix and learner change | `docs/decision-log.md` D-19; `archive/experiment-2_run_00{2,3}_pre-fix/` | — |
| Experiment 1 (null result) | `archive/experiment-1_run_001/` | — |
