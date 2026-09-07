# Write-up v3 — experiment 3: can a claims-analyst agent learn the house rules from a frozen checker?

**Reported run:** `run_005` (manual mode, Claude Haiku 4.5 as a fresh stateless subagent per decision, freeze `64b7292e8214…`, evaluator 1.2). Experiments 1 (`run_001`) and 2 (`run_004`) are summarised at the end and archived under `archive/`. Every number below is computed from `logs/*.jsonl` by `scripts/summarize_run.py` and the per-attempt records; nothing is estimated. Synthetic data; educational demonstration; nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory or operational evidence. **Public article** (Substack-ready, PB voice): `articles/loop-engineering-markdown-skills/article.md` — web version at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee.

## 1. What was tested

Four questions an insurance analytics team is actually asked, on the synthetic HLT-008 claims sample (12,845 medical claims), in a fixed order:

| # | Task | The sponsor's question (blinded brief) | What the frozen checker holds (examples of golden values) |
|---|---|---|---|
| 1 | T2 Describe the book | How many claims, split by status? What is our denial rate? How common is the fraud flag? Amounts? Monthly volume? | 12,845 claims; status mix Paid 10,511 / Denied 1,286 / Adjusted 542 / Pended 506; **denial rate = 1,286 / 12,339 = 10.42 %** over adjudicated claims (Pended excluded); fraud flag 647 / 12,845 = 5.04 %; billed total $21.25 M, median $429.52; monthly trend keyed on service start date, 36 months from 2021-01; report must show numerator / denominator for every rate and say the data is synthetic |
| 2 | T4 Where denials happen | Which denial codes dominate, how many claims carry no code, how does the denial rate differ by claim type, specialty, network, place of service, prior auth? | code shares over **denied** claims (CO-15 18.7 %, CO-4 16.0 %, CO-11 11.4 % …); 11,559 claims without a code, 0 among denied; Professional denial rate 693 / 6,754 = 10.26 %; all five segments; segments under 30 claims flagged; small-groups caveat |
| 3 | T3 Providers & network | Where do money and denials go by specialty and network? Who are the top-10 rendering providers? | In-network denial rate 1,095 / 10,370 = 10.56 % vs out-of-network 191 / 1,969 = 9.70 %; each group with count, paid sum, denial and fraud rate; join to the provider directory verified many-to-one, 0 unmatched; top-10 providers by claim count (first: 115 claims, Physical Therapy, in-network); association-not-causation caveat |
| 4 | T7 High-cost model | Which incoming claims will land in the most expensive 5 %? | 25 % hold-out with seed 42; **threshold $3,198.99 computed on the training split only** (all-data value $3,161.93 would be wrong); positive rate 5.00 % train / 4.67 % test; amount fields, the pre-computed high-cost flag and ids are forbidden features; preprocessing fitted on train only; logistic regression plus a tree model; **ROC-AUC must fall in [0.60, 0.95]** — leakage-free models reach 0.89–0.91, leaky ones 0.997 |

76 rubric checks across the four tasks (21 / 17 / 20 / 24), five dimensions (correctness, completeness, reproducibility, statistical discipline, communication), score 0–4, pass = score ≥ 3.5 and no critical check failed. The pack was built by independent reference code, reviewed by the user, and frozen by hash before the run.

### The loop

Plan (agent picks components and parameters from a fixed catalogue) → Run (deterministic pandas / scikit-learn) → Check (frozen evaluator) → pass: next task · fail: Reflect and Revise (agent) → Run again, up to five attempts. After each attempt the agent is shown **only the three most severe findings**, the scorecard and a count of further failures; the literal parameter fix is withheld (decision D-21).

### Three arms

| Arm | Sees the checker's feedback? | Carries anything between tasks? | Analogue in the literature |
|---|---|---|---|
| `reflection_only` — checker, no memory | yes (3 findings per attempt) | no | verification loop / within-rollout refinement |
| `skill_learning` — checker + skill notebook | yes | yes: after a pass, the agent may write one reusable lesson as a Markdown skill; skills are retrieved before planning later tasks; the library starts **empty** | cross-task accumulation (Reflexion / Voyager-style memory) |
| `self_refine` — self-review only | **no** — the checker scores every attempt for the record, but the agent only sees its own report and metrics and decides accept / revise | no | Self-Refine (Madaan et al., 2023) |

The operator was a fresh, stateless Claude Haiku 4.5 subagent for every decision (46 in total), spawned inside the author's Claude Code session, using an operator definition that carries **no** list of analytical conventions. No API key, no Agent SDK.

## 2. What happened

### Attempts and scores (frozen checker, every attempt)

| Task | Checker, no memory | Checker + skills | Self-review only |
|---|---|---|---|
| 1 Describe the book | 2.16 → 3.13 → **4.00** (3 attempts) | 2.83 → **3.80** (2) | 2.89, agent said "done" → **fail** |
| 2 Where denials happen | 2.07 → 3.00 → **3.84** (3) | 3.31 ★ → **4.00** (2) | 3.14, agent said "done" → **fail** (critical: denominator) |
| 3 Providers & network | 2.34 → **3.87** (2) | 2.09 ★ → **3.51** (2) | 1.21 → 1.61, agent said "done" → **fail** |
| 4 High-cost model | 2.75 → **3.60** (2) | 3.15 → **3.80** (2) | 2.62 → **3.60**, agent said "done" → pass |
| **Total attempts** | **10** | **8** | 6 (stopped by its own verdict) |
| Failed checks on first tries | 8 + 8 + 8 + 5 = **29** | 5 + 3 + 10 + 4 = **22** | 5 + 4 + 13 + 6 = 28 |
| First-attempt mean score | 2.33 | 2.85 | 2.47 |
| Tasks passed (checker) | 4 / 4 | 4 / 4 | **1 / 4** |

★ = the learned skill was cited in that plan.

### The one skill that was learned

After passing task 1, the `skill_learning` agent wrote `evolved_run_005_001` — *Correct denial-rate denominator selection*: compute denial rates over adjudicated claims (Paid, Denied, Adjusted), exclude Pended, record numerator and denominator definitions, set `denominator_option: adjudicated_claims`. Provenance: feedback ids `T2-denial_rate_denominator`, `T2-denial_rate_value`. The validator asked for one revision (missing `expected_artifacts`), then accepted it. It was retrieved on all three later tasks and cited in the plans of tasks 2 and 3; on task 4 (a model, no denial rate) the agent correctly did not use it. No further skill was proposed: for tasks 2–4 the agent judged that no lesson applied to at least two remaining tasks.

Where it bit: on task 2 the no-memory arm's first plan used the wrong denominator and no small-group threshold (8 failed checks, one critical); the skill arm's first plan set `adjudicated_claims` and `min_group_size: 30` (3 failed checks, none critical) and passed one attempt earlier.

### The self-review arm

The agent accepted its own first attempt on tasks 1 and 2 with confident summaries ("no analytical errors or missing requirements identified") while the checker recorded a wrong denial rate (1,286 / 12,845 instead of 1,286 / 12,339) and a critical denominator miss. On task 3 it asked itself for one revision (add a synthetic-data caveat, show denominators) and then accepted an output that still lacked the separate specialty and network breakdowns — 11 failed checks, score 1.61. On task 4 it caught the two things that matter most in a first model — the threshold computed on all data and the amount fields leaking the target — revised, and passed at 3.60. Net: four "done" declarations, one checker pass.

### By rubric dimension (first attempt → final, mean over the four tasks)

| Dimension | Checker, no memory | Checker + skills | Self-review only |
|---|---|---|---|
| correctness | 2.07 → 4.00 | 2.18 → 4.00 | 1.77 → 2.27 |
| completeness | 3.08 → 4.00 | 3.08 → 4.00 | 3.33 → 3.33 |
| reproducibility | 4.00 → 4.00 | 4.00 → 4.00 | 4.00 → 4.00 |
| statistical discipline | 1.50 → 4.00 | 1.78 → 3.47 | 1.10 → 1.82 |
| communication | 1.00 → 3.13 | 3.17 → 3.42 | 2.13 → 2.63 |

## 3. Reading the result honestly

- **The verification loop now visibly iterates.** With only three findings per attempt and no literal fix, the no-memory arm needed 10 attempts for 4 tasks and its scores climb step by step (experiment 2's loop always closed after one retry because the feedback carried the whole checklist with fixes).
- **Memory helped where the lesson applied.** The single learned skill was about denominators; it was cited on the two later tasks that compute rates and those tasks passed one attempt earlier or with far fewer first-try failures (task 2: 3 vs 8). The skill arm needed 8 attempts to the no-memory arm's 10 and 22 first-try failures to 29.
- **But part of the gap is operator variance, not memory.** The two checker arms drew different first plans from a stochastic model: on task 1, with an empty library, the skill arm already scored 2.83 to the no-memory arm's 2.16. With four tasks and one run, the attempt counts are suggestive, not proof. A fair reading: the direction is right, the size is uncertain.
- **Self-review is not a checker.** The agent declared itself done on every task; the frozen checker failed three of the four. The one it passed is the one where its own review happened to name the same two problems the checker weighs most (leakage, train-only threshold). This is the evaluator-outside-the-loop point made concrete: an audit performed by the auditee is a status report.
- **Haiku 4.5 was a competent, fallible analyst.** 46 decisions, 0 invalid responses, plans that map feedback onto the catalogue correctly every time; it simply does not know an unwritten house rule until someone tells it — which is the situation the experiment was built to study.

## 4. Limitations

Single run per arm; a stochastic operator whose variance is comparable to the effect on some tasks; four tasks, one of which (the model) offers no rate-based lesson to reuse; the goldens encode one team's conventions (adjudicated-claims denominator, 30-claim small-group threshold, service-date months) — a different team would freeze different rules; a skill library of one is not a library; the checker is only as good as the 76 rules and the briefs were blinded by the same author who wrote the rubric. Synthetic data throughout: nothing here is evidence about any real payer, provider or member.

## 5. Earlier experiments (archived)

- **Experiment 1, `run_001`** — Fable 5.1 operators with briefs that stated the conventions: every arm 4.00 first attempt on all eight tasks, no feedback, no skills. A ceiling, not a result. `archive/experiment-1_run_001/`.
- **Experiment 2, `run_004`** — a deterministic rule learner from textbook defaults, full feedback with literal fixes: first-attempt mean 1.55 (no memory) vs 2.17 (skills) over T2–T8, six skills, 22 reuses — but exactly one retry per task, because the feedback handed over the whole fix. `archive/experiment-2_run_004/` (write-up v2 inside).

Experiment 3 is not comparable number-for-number with either: different briefs, tasks, feedback regime, operator and freeze.

## 6. Reproduce

```bash
uv run --extra dev pytest -q                                   # 108 tests
uv run python -m src.build_goldens --check                     # golden pack reproduces exactly
uv run python -m src.run_experiment init --run-id run_006 --conditions reflection_only,skill_learning,self_refine --mode manual
uv run python -m src.run_experiment advance-all --run-id run_006   # then one fresh operator subagent per request (docs/OPERATOR_PROTOCOL.md)
uv run python scripts/summarize_run.py --run-id run_006
uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py
```

## Evidence index

`logs/experiment_events.jsonl` (attempt and done records: `score_by_attempt`, `attempts_to_pass`, `n_failed_checks`, `n_feedback_shown`, `skills_applied`, `self_declared_pass`) · `logs/skill_events.jsonl` · `logs/graph_events.jsonl` (`self_evaluate` verdicts next to the frozen score) · `logs/feedback_events.jsonl` (what was shown, with `source`) · `artifacts/manual/run_005/` (46 request/response pairs) · `artifacts/tasks/run_005/` (every attempt's metrics, report and charts) · `skills/evolved/run_005/` · `artifacts/reports/run_summaries.json` · `config/freeze_manifest.json`.

## LinkedIn draft

I gave a small model four claims-analytics tasks and did not tell it the house rules. Which denominator for a denial rate? Where does the "high cost" threshold come from? It had to learn those from a checker that only ever names the three biggest problems.

Three ways of closing the loop, same tasks, same frozen answer key:
– checker feedback, no memory: 10 attempts to pass 4 tasks
– checker feedback + a notebook of lessons it wrote itself: 8 attempts, and the one lesson it kept (adjudicated-claims denominator) showed up in later plans
– reviewing its own work with no checker: declared "done" four times, actually passed once

One run, synthetic data, small numbers — but the shape is the point. The loop is the product; the evaluator has to sit outside it.

Write-up and code in the comments. #AgenticAI #LangGraph #ClaimsAnalytics #Evaluation
