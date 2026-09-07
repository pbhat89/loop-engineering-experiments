# Teaching an agent procedures, not answers — and what happened when the agent did not need them

**Status:** populated 2026-09-07 (L0) from `logs/*.jsonl`, `logs/runs/*.json`, `artifacts/reports/run_summaries.json`, `artifacts/figures/`, `artifacts/graphs/`, `goldens/` and `config/freeze_manifest.json`. Every number below traces to one of those files (appendix). Synthetic data; educational demonstration; nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory or operational evidence.

## 1. The idea in one paragraph

An analysis agent should get more reliable as it works, without anyone retraining a model. The mechanism tried here is **external procedural memory**: a LangGraph loop plans a claims-analysis task, executes it with deterministic code, is scored against a rubric and a golden reference that were frozen *before* the run, reflects on the evaluator's feedback, turns reusable lessons into versioned Markdown skills, and retrieves those skills on later tasks. The question was whether persistent skills make later tasks more reliable than (a) no memory at all and (b) within-task reflection only.

## 2. What was built (`docs/plan.md`, `artifacts/graphs/langgraph_topology.png`)

- A typed LangGraph `StateGraph` with twelve nodes, one compiled graph whose routers read the experimental condition, LangGraph `interrupt()` at every LLM-decision node and a SQLite checkpointer so a paused task survives across processes (D-03).
- A deterministic executor (`src/task_runner.py`, `src/analyses/`) that interprets a structured plan against a fixed **component catalogue** for eight tasks — data reconnaissance, portfolio description, provider/network patterns, denial analysis, fraud-pattern exploration, a fraud baseline model, a high-cost model, and an executive brief — and never executes model-generated code.
- A deterministic evaluator (`src/evaluator.py`, 152 checks in `config/rubric.yaml`) that compares each task's artifacts with a **golden pack** built once by independent reference code (`src/build_goldens.py`, `goldens/`), reviewed by the user, and frozen by hash (`config/freeze_manifest.json`, 15 files, `freeze_sha256 1566c5698a50ba82e2df5e94e6da37b5fa738e53281f19283f3f9431334566ab`). A manual run refuses to start if any hashed file changes (verified by a drift test, `docs/verification-log.md`).
- A skill system (`skills/`, `src/skill_store.py`, `src/skill_validator.py`): six foundational skills, deterministic tag/keyword retrieval, a validator that rejects duplicates, unsafe or ungrounded procedures and proposals without feedback provenance, and run-scoped immutable persistence under `skills/evolved/<run_id>/`.
- Structured JSONL logs for every attempt, node transition, feedback item and skill event, a static dashboard with a rough ETA, and seven figures generated only from logs.

Figure 1 — `artifacts/graphs/langgraph_topology.png`: the **designed** workflow (not observed performance).

## 3. How the LLM steps happened (Addendum B)

> LLM steps were performed by Claude (Fable 5.1) subagents inside the author's Claude Code session in a human/agent-in-the-loop manual mode; the Python runtime made no model API calls.

Each LLM-decision node paused the graph and wrote a request file; the lead spawned one **fresh, stateless** subagent per request, which read that file only and wrote a response file; the runner validated the response and resumed. Recorded on every event: `provider_mode: manual`, `operator: claude-code-subagent`, `model_identifier: claude-fable-5-1`.

| From `logs/graph_events.jsonl` / `logs/runs/run_001.json` | baseline | reflection_only | skill_learning |
|---|---:|---:|---:|
| operator steps used (cap 64) | 8 | 8 | 21 |
| operator requests by node | 8 plan | 8 plan | 8 plan · 8 reflect · 5 propose |
| responses failing schema/catalogue validation | 0 | 0 | 0 |
| tasks stopped by `operator_cap` | 0 | 0 | 0 |

37 request/response pairs in total (`artifacts/manual/run_001/`). One protocol change was applied after T1 in every condition: requests list the remaining tasks with their titles, not ids alone (D-16).

## 4. The frozen target (`config/freeze_manifest.json`, `goldens/`, `artifacts/reports/golden_review.md`)

Dataset: Hugging Face `xpertsystems/hlt008-sample`, revision `7309ddb30e67468748b7aa9182d8517fe28c2f9c`, CC-BY-NC-4.0, 100 % synthetic (12,845 medical claims, 18,310 pharmacy claims, 500 members, 150 providers, 10,627 adherence rows). Golden values reviewed and approved by the user on 2026-09-07 (52 values, 0 sanity failures), for example: denial rate **0.104222 = 1,286 / 12,339 adjudicated claims** (Pended excluded); fraud-label prevalence **0.050370 = 647 / 12,845**; high-cost threshold **3,198.99** (95th percentile of `paid_amount` on the training split, seed 42; the all-data value would be 3,161.93, so a leaked threshold is detectable); 36 service months with 302–405 claims each.

*The agent was measured on whether it produced the expected claims metrics, artifacts, modelling safeguards and caveats — not on whether it thought its own answer was good.*

## 5. Results — quality (`logs/experiment_events.jsonl`; `artifacts/figures/learning_curve.png`, `rubric_heatmap.png`)

Final `score_total` (0–4) per task, `run_001`, final records (`status = done`):

| condition | T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | mean |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 |
| reflection_only | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 |
| skill_learning | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 | 4.00 |

Every dimension (correctness, completeness, reproducibility, statistical discipline, communication) scored 4.00 in every cell (Figure `rubric_heatmap.png`). Later-task means (T4–T8) are therefore 4.00 in all three conditions; there is no quality difference to interpret. One run per condition; illustrative.

## 6. Results — reliability (`logs/experiment_events.jsonl`; `artifacts/figures/reliability_curve.png`)

| condition | first-attempt pass rate | retries | execution errors | mean first-attempt score |
|---|---:|---:|---:|---:|
| baseline | 8 / 8 (100 %) | 0 | 0 | 4.00 |
| reflection_only | 8 / 8 (100 %) | 0 | 0 | 4.00 |
| skill_learning | 8 / 8 (100 %) | 0 | 0 | 4.00 |

Because no task ever needed a retry, the `reflect_on_feedback → revise_plan` path was **never exercised** in `reflection_only`; that condition is structurally identical to baseline in this run.

## 7. Results — skills (`logs/skill_events.jsonl`, `skills/evolved/run_001/`; `artifacts/figures/skill_accumulation.png`, `skill_utility.png`, `skill_lifecycle_graph.png`)

- Retrievals: 47 (the six foundational skills, top-6 by tag/keyword score, on every skill_learning task).
- Cited as applied by the operator (`skills_applied`): 27 citations — `foundational_006` evaluation & charting 8, `_003` descriptive summary 6, `_001` data contract 4, `_004` categorical/numeric 4, `_005` reproducible analysis 3, `_002` safe joins 2. No foundational skill went uncited.
- Proposals: 5 (after T1–T5); proposal skipped after T6, T7 and T8 because the reflection returned no lesson meeting the "reusable in ≥ 2 remaining tasks" rule.
- Persisted evolved skills: **0**. All five proposals were rejected by the validator on **provenance** (`source_feedback_ids` empty — every task had passed with no evaluator feedback, so there was nothing grounded to cite); the T1 and T2 proposals additionally failed the generality check for an ungrounded "guarantee" claim. Proposal names, for the record: `objective_scope_coverage`, `task_spec_to_plan_alignment`, `task_spec_parameter_reconciliation`, `spec_population_binding`, `label_leakage_and_protected_attribute_screen`.
- Validated **useful** skills (persisted, then retrieved and applied later): none in `run_001`. Potential bloat (never retrieved): none.

The observed lifecycle graph (`skill_lifecycle_graph.png`) therefore shows only the deterministic **stub** run's five skills; for `run_001` there is no feedback → skill → reuse chain to draw.

**Contrast with the stub simulation (`stub_001`, deterministic fixtures, not an LLM):** first-attempt means 1.62 / 1.57 / 1.61 (baseline / reflection_only / skill_learning), one feedback-driven revision per task, 5 evolved skills persisted and 10 reuse events. The stub demonstrates that every stage of the loop — feedback → reflection → proposal → validation → persistence → retrieval → reuse — functions end to end. It says nothing about model behaviour.

## 8. What did not work / surprises (`docs/verification-log.md`, `logs/skill_events.jsonl`)

1. **Ceiling effect.** With fair task briefs and a Fable 5.1-class planner reading a fixed catalogue, the baseline cleared the frozen rubric on the first attempt of every task. Procedural memory had no headroom to show on scores or retries.
2. **The loop learns from failure, and there was none.** The brief requires evolved skills to cite the feedback they were learned from. With zero feedback items issued in the manual run, every proposal was ungrounded by construction and correctly rejected. The proposals that were written were honest about this (`source_feedback_ids: []`) rather than fabricating provenance.
3. **`reflection_only` never differed from baseline** for the structural reason in §6.
4. Model results inside the tasks are themselves a finding about the data: leakage-free fraud models score ROC-AUC 0.499 / 0.498 and PR-AUC 0.052 / 0.051 against a test prevalence of 0.047 (skill_learning T6 metrics), i.e. the synthetic fraud label is unpredictable without label-derived fields; the high-cost baselines reach PR-AUC 0.223 / 0.217 (T7). Golden sanity ranges were widened for this reason before the freeze (D-17).
5. Build-process facts: project-level agent types were not loaded in the session, so the five builder agents and all 37 operator steps ran as general-purpose subagents adopting their definition files; the first parallel build burst hit the session rate limit and was resumed the next day from checkpoints; the operator cap was raised from 40 to 64 after the stub run consumed 38 (D-15).

## 9. Limitations (`docs/spec.md` §14, restated)

Single run per condition; illustrative, no significance claims; one operator model; choices bounded by a fixed catalogue (the planner selects procedures, it does not write code); `skill_learning` bundles foundational-skill access with evolved-skill accumulation (a `foundational_only` control exists but was not run, D-13); deterministic, structural evaluation of prose; synthetic data whose distributions come from a generator; the retry path and the provenance rule were never stressed because no task failed.

**What this experiment does show:** a reproducible harness in which the agent is graded by a frozen external reference, every decision is logged with provider metadata, and a null result is unambiguous. **What it does not show:** that Markdown skills improve a strong planner on tasks it can already do. The natural follow-ups are to run the same frozen suite with a deliberately weaker or lower-effort planner, with briefs that state fewer conventions, or with tasks whose correct procedure cannot be inferred from the brief — the loop only has something to learn where the evaluator has something to say.

## 10. Reproduce it

```bash
uv sync --extra dev
uv run python -m src.download_data && uv run python -m src.profile_data       # pinned revision 7309ddb3…
uv run python -m src.build_goldens --check                                     # golden pack reproduces from the data
uv run python -m src.run_experiment run-stub --run-id stub_check              # deterministic end-to-end (no model)
uv run python -m src.run_experiment init --run-id run_002 --mode manual       # refuses unless the freeze matches
uv run python -m src.run_experiment advance-all --run-id run_002              # then follow docs/OPERATOR_PROTOCOL.md
uv run python scripts/summarize_run.py --run-id run_001 --run-id stub_001     # the numbers in this write-up
uv run python scripts/pipeline.py verify                                       # tests, goldens, freeze, logs
```

Dataset licence CC-BY-NC-4.0 (attribution in `data/README.md`). Dashboard: `artifacts/dashboard/progress.html`. Figures: `artifacts/figures/`.

## 11. Draft LinkedIn post (≤ 1,300 characters)

I built a LangGraph loop that tries to make a claims-analysis agent more reliable by learning *procedures*, not answers: plan → deterministic execution → score against a golden pack frozen before the run → reflect → write a versioned Markdown skill → retrieve it next task.

Setup: 8 fixed tasks on a fully synthetic claims dataset, 3 conditions (no memory / reflection only / persistent skills), one run each, 152 deterministic rubric checks, zero model API calls — every LLM decision was a fresh Claude subagent inside my Claude Code session, logged with provider metadata.

Result: a clean null. All three conditions passed all 8 tasks on the first attempt (4.00/4.00, 0 retries). Zero evaluator feedback meant zero grounded lessons, and the validator rejected all 5 skill proposals for missing provenance — exactly as designed.

What I learned: a frozen golden pack makes a null result unambiguous; a loop that learns from failure needs failure; and the next run should use a weaker planner or briefs that give less away.

Synthetic data, illustrative single run, not operational evidence. Repo + logs + write-up: [link].

## Appendix — evidence index

| Claim | Source | Field(s) |
|---|---|---|
| Scores 4.00 everywhere, 0 retries, 0 errors, 100 % first-attempt | `logs/experiment_events.jsonl` (`status = done`, run_001); `artifacts/reports/run_summaries.json` | `evaluator_score_total`, `retry_count`, `execution_errors`, `first_attempt_passed` |
| Operator steps 8 / 8 / 21; 37 requests; 0 validation errors | `logs/runs/run_001.json`; `logs/graph_events.jsonl` | `operator_steps_used`; `event_type in {operator_request, operator_validation_error}` |
| Provider metadata | `logs/experiment_events.jsonl` | `provider_mode`, `operator`, `model_identifier` |
| 47 retrievals, 27 citations, 5 proposals, 8 rejection events, 0 persisted | `logs/skill_events.jsonl`; `logs/experiment_events.jsonl` | `event`, `checks`, `skills_reused` |
| Rejection reasons | `logs/skill_events.jsonl` | `reasons` (`provenance`, `generality`) |
| Golden values and freeze | `goldens/*.json`, `artifacts/reports/golden_review.md`, `config/freeze_manifest.json` | `expected_metrics`, `freeze_sha256` |
| Model metrics | `artifacts/tasks/run_001/skill_learning/T6/attempt_1/metrics.json`, `.../T7/attempt_1/metrics.json` | `models.*.roc_auc`, `models.*.pr_auc`, `target_definition.threshold_value` |
| Stub contrast | `logs/experiment_events.jsonl`, `logs/skill_events.jsonl` (run stub_001) | first-attempt `evaluator_score_total`, `skill_persisted`, `skill_reused` |
| Verification | `docs/verification-log.md` (2026-09-07 entries) | `scripts/pipeline.py verify`: 24 PASS |
