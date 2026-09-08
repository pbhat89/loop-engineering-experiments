# Write-up v6 — experiments 4 and 5: does a plain memory do what a validated skill does, and does either carry over?

**Reported runs:** `run_006` (experiment 4, Part A) and `run_008` (experiment 5 v2, Part B) — both manual mode, Claude Haiku 4.5 as a fresh stateless subagent per decision. Experiments 1 (`run_001`), 2 (`run_004`) and 3 (`run_005`) are summarised at the end of Part A and archived under `archive/`; experiment 5 v1 (`run_007`) is summarised in Part B′ and archived at `archive/experiment-5_run_007_heldout-v1/`. Every number below is computed from `logs/*.jsonl` and `artifacts/reports/run_summaries.json`; nothing is estimated. Synthetic data; educational demonstration; nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory or operational evidence. **Public article** (Substack-ready, PB voice): `articles/loop-engineering-markdown-skills/article.md` — web version at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee.

## Part A — experiment 4: does a plain memory of past comments do what a validated skill does? (`run_006`)

Freeze `59fb61d35fe8…`, evaluator 1.3.

## 1. What was tested

Six questions an insurance analytics team is actually asked, on the synthetic HLT-008 claims sample (12,845 medical claims across five linked tables), in a fixed order. All six briefs are blinded — written as a sponsor would ask, with no denominators, thresholds, train-only rules or required caveats stated; the loop has to learn the house rules from the checker.

| # | Task | The sponsor's question (blinded brief) | What the frozen checker holds (examples of golden values) |
|---|---|---|---|
| 1 | T1 Dataset reconnaissance | Five files have just arrived from the vendor — what's in each, can the identifiers be trusted, what period do the dates cover, do the files join the way we'd expect, anything wrong? | five tables at exact row/column counts (members 500×44, providers 150×7, medical_claims 12,845×54, pharmacy_claims 18,310×35, adherence 10,627×7); `member_id` alone is **not** a key on `adherence` (500 unique of 10,627 rows) but the composite `member_id+therapeutic_class` is (10,627/10,627); 36 claims whose adjudication date precedes their own service end; `pharmacy_claims.pharmacy_npi → providers.provider_npi` joins to **zero** providers (all 18,310 unmatched); required caveats: synthetic/simulated + sample preview |
| 2 | T2 Claims portfolio description | How many claims, split by status? What's our denial rate? How common is the fraud flag? Amounts? Monthly volume? | 12,845 claims; status mix Paid 10,511 / Denied 1,286 / Adjusted 542 / Pended 506; **denial rate = 1,286 / 12,339 = 10.42 %** over adjudicated claims (Pended excluded); fraud flag 647 / 12,845 = 5.04 %; billed total $21.25 M, median $429.52; 36 months of monthly trend from 2021-01; every rate shown as numerator/denominator; synthetic-data caveat required |
| 3 | T4 Denial analysis | Which denial codes dominate, how many claims carry no code, how does the denial rate differ by claim type, specialty, network, place of service, prior auth? | code shares over **denied** claims (CO-15 18.7 %, CO-4 16.0 %, CO-11 11.4 % …); 11,559 claims without a code, 0 among denied; Professional denial rate 693 / 6,754 = 10.26 %; all five segments reported; segments under 30 claims flagged small |
| 4 | T3 Provider and network patterns | Where do money and denials go by specialty and network? Who are the top-10 rendering providers? | in-network denial rate 1,095 / 10,370 = 10.56 % vs out-of-network 191 / 1,969 = 9.70 %; each group with count, paid sum, denial and fraud rate; provider join verified many-to-one, 0 unmatched; top-10 providers by claim count (first: 115 claims, Physical Therapy, in-network); association-not-causation caveat |
| 5 | T7 High-cost claim identification | Which incoming claims will land in the most expensive 5 %? | 25 % hold-out, seed 42; **threshold $3,198.99 computed on the training split only** (the all-data value $3,161.93 would be wrong); positive rate 5.00 % train / 4.67 % test; amount fields and the pre-computed high-cost flag are forbidden features; preprocessing fit on train only; **ROC-AUC must fall in [0.60, 0.95]** (leakage-free models reach 0.89–0.91, leaky ones ≈0.997) |
| 6 | T8 Executive brief | ≤600-word brief for the head of claims, built only from the earlier tasks' saved results | required sections `key_findings`, `model_results`, `limitations`, `synthetic_caveats`, `next_steps`; must cite T2's denial rate and total claims, T5's class prevalence, T6's ROC-AUC, T7's threshold value; **every numeric statement ends with `[source: …]`** (`n_cited_statements == n_numeric_statements`); **no causal phrasing** (forbidden: "causes", "drives", "leads to", "because of"); ≤600 words; synthetic-data + no-operational-use caveats |

112 rubric checks across the six tasks (15 / 21 / 17 / 20 / 24 / 15), five dimensions (correctness, completeness, reproducibility, statistical discipline, communication), score 0–4, pass = score ≥ 3.5 and no critical check failed. The pack was built by independent reference code, reviewed by the user, and frozen by hash before the run.

### The loop

Plan (agent picks components and parameters from a fixed catalogue) → Run (deterministic pandas / scikit-learn) → Check (frozen evaluator, checker arms) *or* Self-review (agent scores its own report, self-review arms) → pass/accept: next task · fail/revise: reflect (or self-critique) and revise the plan → Run again, up to five attempts. Checker arms are shown only the **three most severe findings**, the scorecard and a count of further failures; the literal parameter fix is withheld (decision D-21). Self-review arms never see the checker at all — the frozen evaluator still scores every attempt for the record, but the agent decides accept/revise from its own report and metrics alone.

### Five arms

| Arm | Sees the checker's feedback? | Carries anything between tasks? | Analogue in the literature |
|---|---|---|---|
| `reflection_only` — checker, no memory | yes (3 findings/attempt) | no | verification loop / within-rollout refinement |
| `feedback_memory` — checker + raw log | yes (3 findings/attempt) | yes — every checker finding it was ever shown, appended verbatim after each task, newest first, ≤ 30 items; no distillation, filtering or dedup | "a searchable log of past reviewer comments" |
| `skill_learning` — checker + skill notebook | yes | yes — after a pass, may write one reusable lesson as a validated, retrievable Markdown skill; library starts **empty** | Reflexion / Voyager / ExpeL (cross-task procedural memory) |
| `self_refine` — self-review only | **no** | no | Self-Refine (Madaan et al., 2023) |
| `self_refine_memory` — self-review + raw log | **no** | yes — its own review findings (verdict + summary) from earlier tasks, verbatim, newest first, ≤ 30 items | Self-Refine + a searchable log of its own past comments |

The operator was a fresh, stateless Claude Haiku 4.5 subagent for every decision — 115 operator requests across the five arms (23 reflection_only / 16 feedback_memory / 31 skill_learning / 21 self_refine / 24 self_refine_memory), spawned inside the author's Claude Code session using `.claude/agents/experiment-operator-blind.md`, which carries **no** list of analytical conventions. 2 responses failed validation and were re-requested (1 in `reflection_only`, 1 in `self_refine`); 0 execution errors. No API key, no Agent SDK.

## 2. What happened

### Attempts and scores (frozen checker, every attempt)

| Task | Checker only | Checker + raw log | Checker + skills | Self-review only | Self-review + raw log |
|---|---|---|---|---|---|
| T1 Reconnaissance | 3.02 → **4.00** (2) | 3.20 → **4.00** (2) | 3.20 → **4.00** (2) | 3.29, accept → fail | 3.20, accept → fail |
| T2 Portfolio | 2.83 → **3.80** (2) | 2.83 → **3.80** (2) | 2.43 → 3.40 → **4.00** (3) ★skill 002 written | **3.64** (1) — accept → fail | 2.03 → 2.69, accept → fail |
| T4 Denials | 2.81 → **4.00** (2) | 3.19 → **4.00** (2) | **3.64** (1) ★skill 002 cited | 2.65 → 3.14, accept → fail | 2.81 → 2.98, accept → fail |
| T3 Providers | 1.35 → 3.11 → **3.87** (3) | **3.87** (1) — 9 past notes available | 2.45 → **3.64** (2) ★★ both skills cited | 1.97, accept → fail | 2.07, accept → fail |
| T7 High-cost model | 2.75 → **3.60** (2) | 3.15 → **3.80** (2) | 2.20 → 3.40 → **4.00** (3) ★skill 001 cited | 3.15 → **3.60**, accept → **PASS** | 2.60 → **3.80**, accept → **PASS** |
| T8 Executive brief | 1.29 → 2.16 → **3.91** (3) | 2.78 → **3.64** (2) — 14 past notes available | 2.86 → **4.00** (2) ★skill 001 cited | **3.64** → 3.38, accept → fail (revised out of a pass) | 1.52 → 1.52 → 1.90 → 2.59, accept → fail — 7 past notes available |
| **Total attempts** | **14** | **11** | **13** | **10** | **12** |
| Failed checks on first tries | 3+5+5+12+5+9 = **39** | 2+5+3+1+4+5 = **20** | 2+7+2+8+7+2 = **28** | 2+5+6+10+4+2 = **29** | 2+9+5+9+6+8 = **39** |
| First-attempt mean score | 2.34 | **3.17** | 2.80 | 2.92 | 2.37 |
| Mean final score | 3.86 | 3.85 | **3.88** | 3.04 | 2.89 |
| Tasks passed (checker) | **6 / 6** | **6 / 6** | **6 / 6** | **1 / 6** | **1 / 6** |

`self_refine` and `self_refine_memory` stopped every task by their own "accept" verdict (`self_declared_pass = true`, 6/6 each); the frozen checker's pass/fail column above is what actually happened to that output, which the operator never saw.

### The two skills that were learned

`skill_learning` wrote two skills, both rejected once for a missing example (`example_present: example has 0 characters; needs at least 10`) and persisted after one revision each:
- **`evolved_run_006_001`** *"Include synthetic data caveat in reports"* — written after T1 (feedback id `T1-caveat_synthetic`), applicable to T2/T3/T4/T7/T8. Cited on T3, T7 and T8.
- **`evolved_run_006_002`** *"Denial-rate denominator standardization"* — written after T2 (feedback ids `T2-denial_rate_value`, `T2-denial_rate_denominator`), applicable to T3/T4. Cited on T4 and T3.

7 retrievals, 5 reuse events, 4 proposals skipped (T4, T3, T7, T8 — the agent judged no lesson applicable to ≥ 2 remaining tasks each time).

### What the raw log did

`feedback_memory` passed **T3 on the first attempt** (3.87) with 9 accumulated notes available from T1/T2/T4 — the only first-try pass of any checker arm on any task in this run, and the same task that took `reflection_only` three attempts (1.35 → 3.11 → 3.87) and `skill_learning` two (2.45 → 3.64) despite two skills cited. Its first-attempt mean across all six tasks (3.17) was the highest of the five arms — higher than `skill_learning`'s (2.80) — while it wrote no skills, ran no validator, and used 16 operator steps to `skill_learning`'s 31. Where the log helped least was T8: 14 notes were available but the task still needed 2 attempts, because "every numeric statement cited" and "no causal phrasing" are structural requirements that a verbatim log of earlier findings does not obviously generalise into.

### The self-review arms

Both self-review arms declared every task done (`self_declared_pass` 6/6) but the frozen checker passed only one of six in each — T7, the task whose two failure modes (train-only threshold, leaking amount features) are the same ones the self-review process in experiment 3 also caught. The sharpest case is `self_refine` on **T8**: its first attempt scored 3.64 — a checker **pass** — but the operator asked itself for a revision anyway, and the revision scored 3.38, a fail; it revised its way out of a pass with no one there to tell it not to. Giving the self-review arm a memory of its own past verdicts did not help: `self_refine_memory`'s first-attempt mean (2.37) is lower than plain `self_refine`'s (2.92), and its mean final score (2.89) is the lowest of all five arms. An agent that only ever hears from itself does not get better at hearing itself by keeping notes on what it said before.

### By rubric dimension (first attempt → final, mean over the six tasks)

Computed from `evaluator_score_by_dimension` on every logged attempt.

| Dimension | Checker only | Checker + raw log | Checker + skills | Self-review only | Self-review + raw log |
|---|---|---|---|---|---|
| correctness | 2.34 → 4.00 | 3.33 → 4.00 | 2.81 → 4.00 | 2.34 → 2.70 | 2.29 → 2.85 |
| completeness | 3.11 → 3.93 | 3.55 → 3.70 | 3.39 → 3.83 | 3.26 → 3.04 | 3.11 → 3.33 |
| reproducibility | 3.52 → 4.00 | 3.52 → 4.00 | 4.00 → 4.00 | 4.00 → 4.00 | 3.52 → 4.00 |
| statistical discipline | 1.28 → 3.83 | 2.90 → 3.83 | 1.81 → 3.81 | 2.14 → 2.57 | 1.24 → 2.10 |
| communication | 1.45 → 3.55 | 2.53 → 3.72 | 1.97 → 3.76 | 2.87 → 2.87 | 1.69 → 2.17 |

The pattern holds across every dimension: the three checker arms climb to 3.7–4.0 by the final attempt; the two self-review arms barely move (correctness, statistical discipline and communication all stall well under 3.0), because "final" for them means "the operator stopped asking", not "the checker was satisfied".

## 3. Reading the result honestly

- **The loop still visibly iterates.** With three findings per attempt and no literal fix, `reflection_only` needed 14 attempts across six tasks; nothing closes on the first retry by construction.
- **Raw log and skills both cut attempts, with different profiles.** `reflection_only` needed 14 attempts and 39 first-try failures; `feedback_memory` cut that to 11 attempts and 20 failures; `skill_learning` cut it to 13 attempts and 28 failures. The raw log's biggest win was concentrated where the same convention recurred across tasks (T3's first-try pass, 9 notes deep); the skill arm's wins were spread across more tasks but cost more operator effort to get there (31 steps vs. 16) for a similar final pass rate and a mean final score within two hundredths of the raw log's.
- **Self-review arms declared done 6/6 and 6/6 but passed 1/6 each.** The frozen checker disagreed with almost every "accept" verdict, and in `self_refine`'s T8 the operator revised a checker-passing attempt into a checker-failing one. Memory of its own past reviews did not help `self_refine_memory` — its first-attempt and final means are both lower than plain `self_refine`'s. An evaluator inside the loop is not interchangeable with a memory of the evaluator's absence.
- **Operator variance is real and must be stated.** Before any arm had accumulated anything, the three checker arms' very first plans on T1 already scored differently — 3.02 (`reflection_only`) vs. 3.20 (`feedback_memory`) vs. 3.20 (`skill_learning`) — from the same stochastic operator starting from the same empty state. Some of every gap reported above is operator variance, not the memory mechanism under test.

## 4. Limitations

Single run per arm; a stochastic operator whose T1 variance is comparable in size to some of the effects reported above; six tasks, one run; the raw-memory arms show every finding verbatim with no relevance filtering, ranking or deduplication — a curated or retrieval-ranked memory could plausibly do better or worse than either extreme tested here; a skill library of two is barely more a library than experiment 3's library of one; the self-review arms' accept/revise verdicts are never independently audited except by the frozen checker, which they never see, so "self_declared_pass" is a status report, not a quality claim; the goldens encode one team's conventions (adjudicated-claims denominator, 30-claim small-group threshold, service-date months, cited-numbers/no-causal-language brief style) — a different team would freeze different rules; the checker is only as good as its 112 rules, and the briefs were blinded by the same author who wrote the rubric. Synthetic data throughout: nothing here is evidence about any real payer, provider or member.

## 5. Earlier experiments (archived)

- **Experiment 1, `run_001`** — Fable 5.1 operators with briefs that stated the conventions: every arm 4.00 first attempt on all eight tasks, no feedback, no skills. A ceiling, not a result. `archive/experiment-1_run_001/`.
- **Experiment 2, `run_004`** — a deterministic rule learner from textbook defaults, full feedback with literal fixes: first-attempt mean 1.55 (no memory) vs 2.17 (skills) over T2–T8, six skills, 22 reuses — but exactly one retry per task, because the feedback handed over the whole fix. `archive/experiment-2_run_004/`.
- **Experiment 3, `run_005`** — a blinded four-task suite (T2, T4, T3, T7), Claude Haiku 4.5 operator, feedback capped to the three most severe findings, three arms: checker-no-memory needed 10 attempts to pass 4 tasks, checker+skills needed 8, self-review-only declared every task done but the checker passed only 1 of 4. `archive/experiment-3_run_005/`.

Experiment 4 is not comparable task-for-task with experiment 3: six tasks instead of four (T1 and T8 are new and were not run in experiment 3), a different freeze, and two arms that did not exist before. The four shared tasks (T2, T4, T3, T7) are comparable only with the operator-variance caveat above in mind.

## 6. Reproduce

```bash
uv run --extra dev pytest -q                                   # 185 tests
uv run python -m src.build_goldens --check                     # golden pack reproduces exactly
uv run python -m src.run_experiment init --run-id run_007 --conditions reflection_only,feedback_memory,skill_learning,self_refine,self_refine_memory --mode manual
uv run python -m src.run_experiment advance-all --run-id run_007   # then one fresh operator subagent per request (docs/OPERATOR_PROTOCOL.md)
uv run python scripts/summarize_run.py --run-id run_007
uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py --run-id run_007
```

## Part B — experiment 5 v2: does the memory carry over, once the test can show it? (`run_008`)

**Reported run:** `run_008`, manual mode, freeze `bab215a5fbcc…`, evaluator 1.3, model `claude-haiku-4-5-20251001`. Experiment 4 (above) measured whether memory helps *within* a suite the arm was repeatedly corrected on. Experiment 5 asks the harder question decision D-23 poses: does what an arm accumulated in `run_006` transfer to tasks it has never attempted? A first attempt at that question, `run_007`, hit a ceiling and is superseded; decision D-24 explains why and is summarised as Part B′ below.

### 7. Design

**Three convention-dense held-out tasks, order T11 → T12 → T13** (article tasks 7–9), each built verbatim from an earlier task's components so the conventions on trial are exactly the ones the memory was corrected on, while none of the three tasks' own numeric answers has ever been seen by any arm. Every brief below is quoted verbatim from `config/tasks.yaml`; no convention is stated in any of them.

| # | Task | The sponsor's question (blinded brief, quoted) | What the frozen checker holds (examples of golden values) |
|---|---|---|---|
| 7 | T11 Portfolio deep-dive | "The head of claims wants a fuller picture of the medical book than a status count. How do claims split by status and what is our denial rate? How common is the fraud flag? What do billed, allowed and paid amounts look like — not just totals, but how they are distributed? And how have both claim volume and paid spend moved month by month? Produce the standard artifacts (status chart, monthly trend chart and table, financial summary table, report)." | status mix Paid 10,511 / Denied 1,286 / Adjusted 542 / Pended 506; **denial rate = 1,286 / 12,339 = 10.42 %** over adjudicated claims; fraud prevalence 647 / 12,845 = 5.04 %; three amount columns with quantiles — billed (sum $21.25 M, median $429.52, p90 $4,279.02, p99 $21,256.58), allowed (median $241.90, p90 $2,359.65, p99 $11,562.75), paid (median $124.90, p90 $2,043.85, p99 $10,911.44); 36 monthly `claim_count` and `paid_amount_sum` values keyed on `service_date_from`, 2021-01 to 2023-12; synthetic-data + descriptive-only caveats required |
| 8 | T12 High-cost model, wider net | "Medical management wants the early-warning idea extended to a wider net: when a claim arrives, how likely is it to end up in the most expensive 10 percent by paid amount? Hold out a quarter of the claims for testing, train a logistic regression plus one tree-based model on what is known when a claim is submitted, and report how well the models rank claims (PR-AUC, ROC-AUC, and precision and recall among the top 5 percent of held-out claims by score). Produce the standard artifacts (model metrics, threshold, feature list, precision-at-k chart, report)." | 25 % hold-out, seed 42, n_train 9,633 / n_test 3,212; **90th-percentile threshold $2,074.35, computed on the training split only** (the all-data value $2,043.85 would be wrong); positive rate 10.01 % train (964/9,633) / 9.12 % test (293/3,212); every amount field, `high_cost_flag`, `claim_id` and `member_id` are forbidden features; preprocessing fit on train only; **ROC-AUC must fall in [0.60, 0.95]** — the golden's own leakage-free reference logistic regression reaches **0.9165** |
| 9 | T13 Brief for the CFO | "Write a one-page brief (no more than 600 words) for the chief financial officer using only the saved results of the two tasks just completed in this set — the portfolio deep-dive and the wider-net high-cost model. Cover the key findings, how the model performed, the limitations and what to do next. Produce the standard artifacts (executive brief, findings table, report)." | sources restricted to `[T11, T12]` only (default `[T11]`); required sections `key_findings`, `model_results`, `limitations`, `synthetic_caveats`, `next_steps`; must cite T11's total claim count and denial rate and T12's threshold value and ROC-AUC; **every numeric statement ends with `[source: …]`**; **no causal phrasing** (forbidden: "causes", "drives", "leads to", "because of"); ≤ 600 words; synthetic-data + no-operational-use caveats |

63 rubric checks across the three tasks (T11 25, T12 24, T13 14), same five dimensions, same pass rule (score ≥ 3.5, no critical miss). Goldens rebuilt from parameterised reference code (`_build_portfolio`, `_build_high_cost` — so T11 cannot drift from T2 nor T12 from T7) and reviewed by the user; the ten goldens carried over from experiments 3–4 and v1 are byte-identical apart from `built_at`; `build_goldens --check` clean over all thirteen files. New freeze `bab215a5fbcc…` (v1: `74e64e1d38e3…`; experiment 4: `59fb61d35fe8…`; 3: `64b7292e8214…`; 1–2: `1566c5698a50…`).

**Why these three tasks.** `run_007`'s four held-out tasks left almost no room for memory to show anything: the cold arm's first attempts already scored 3.09–3.68 against a 3.50 pass threshold (D-24). T11, T12 and T13 are deliberately convention-dense — T11 alone exercises six convention families in one task (denominator, prevalence, three amount columns' quantiles, the month key, printed denominators, two caveats). Measured on the frozen evaluator before the run: **catalogue defaults score 1.18 / 1.69 / 1.57** on T11/T12/T13, and the **house conventions score 4.00 / 4.00 / 4.00** — the gap the cold arm has to climb is real again (D-24; not independently rerun for this write-up).

**The memory is frozen for the whole run** (`memory_read_only: true`). Recall is untouched — `feedback_memory` still sees all 19 seeded notes before every plan, and `skill_learning` still lists `run_006`'s two skills — but nothing is written: `finalize_task` logs `memory_write_skipped` (`reason: read_only`) instead of appending, and `skill_learning` routes straight to `completed` with no reflect-for-learning, no proposal, no validation, no persistence. So the notes shown to `feedback_memory` on T13 are the same 19 shown on T11 — a test of what `run_006` left behind, not of what the run learns on its way through (D-24).

**Seeding, mechanics unchanged from `run_007`** (D-23). `config/experiment.yaml` sets `seed_from_run: run_006`, `task_index_offset: 6`. `feedback_memory` is seeded once at `init` with `run_006`'s **19** raw notes (not `run_007`'s 25 — that log was archived with `run_007`), every numeric token replaced by `[n]` except task ids and `p90`/`p99`; **24 tokens redacted**. `skill_learning` lists (never copies) `evolved_run_006_001_v1.md` and `evolved_run_006_002_v1.md` read-only.

**Leakage audit, re-run for this write-up.** `uv run python scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13` → **clean**: 95 material golden numbers (≥ 3 significant digits) in 981 string forms compared against 58 numeric tokens surviving in the seeded notes and skill files; 0 reachable. The audit also names what redaction *prevented*: **one** real golden value — `12339`, T11's adjudicated-claims denominator — sat in the detail of `run_006`'s T2 note and would otherwise have carried straight through.

### 8. What happened

**Attempts and scores (frozen checker, every attempt), scores by attempt with failed checks on first try in brackets:**

| Task | `reflection_only` (cold) | `feedback_memory` (warm, 19 notes, frozen) | `skill_learning` (warm, 2 seeded skills, frozen) |
|---|---|---|---|
| T11 Portfolio deep-dive | 2.85 → **3.73** (2) — [6, 1] failed | **3.87** (1) — [1] failed | **3.60** (1) — [4] failed, `evolved_run_006_002` cited |
| T12 High-cost, wider net | 3.15 → **3.80** (2) — [4, 1] failed | **4.00** (1) — [0] failed | 2.95 → **3.80** (2) — [4, 1] failed, `evolved_run_006_001` cited |
| T13 Brief for the CFO | 2.44 → **4.00** (2) — [4, 0] failed | 2.86 → **4.00** (2) — [2, 0] failed | **4.00** (1) — [0] failed, `evolved_run_006_001` cited |
| **Total attempts** | **6** | **4** | **4** |
| Failed checks on first tries | 6+4+4 = **14** | 1+0+2 = **3** | 4+4+0 = **8** |
| First-try passes | 0 / 3 | 2 / 3 (T11, T12) | 2 / 3 (T11, T13) |
| Mean first-attempt score | 2.81 | 3.58 | 3.52 |
| Mean final score | 3.84 | 3.96 | 3.80 |
| Tasks passed (checker) | **3 / 3** | **3 / 3** | **3 / 3** |
| Operator steps used | 9 | 5 | 5 |

19 operator requests total (9 / 5 / 5), 0 validation re-requests, 0 execution errors. No skill was written, proposed or persisted — the frozen memory closes that path by construction (D-24).

**First-try findings — what transferred, what was new:**

| Task | Cold arm's first-try failures | Warm-arm first-try failures | Reading |
|---|---|---|---|
| T11 Portfolio deep-dive | `denial_rate_value`, `denial_rate_denominator`, `monthly_date_column` (6 checks) | `feedback_memory`: `caveat_descriptive` only (1). `skill_learning`: `monthly_date_column`, `monthly_counts`, `monthly_paid_series` (4) | The denominator and month-key conventions transferred to both warm arms; the skills arm still missed the month column and both new monthly series — no seeded skill covers `monthly_trend` |
| T12 High-cost, wider net | `no_target_leakage`, `roc_auc_range`, `caveat_synthetic` (4) | `feedback_memory`: passed clean (0). `skill_learning`: `no_target_leakage`, `roc_auc_range`, `caveat_model_limitations` (4) — `evolved_run_006_001` cited but is the *caveat* skill, not a leakage skill | The raw log's verbatim T7-family notes carried leakage and the AUC band across; no seeded skill covers leakage exclusion, so `skill_learning` repeated the cold arm's mistake almost exactly |
| T13 Brief for the CFO | `sections`, `no_causal_language`, `causal_language_setting` (4) | `feedback_memory`: `no_causal_language`, `causal_language_setting` (2) — no note in its log ever mentioned causal wording; in `run_006` this arm was corrected on sources and citations, not phrasing. `skill_learning`: passed clean (0), `evolved_run_006_001` cited | The one convention neither the cold arm nor the raw-log memory had — avoid causal phrasing — is exactly the one the raw log had never been shown; the skills arm passed because its cited skill's own worked example happened to use associative language |

**First-attempt gap over the cold arm, per task:** raw log +1.02 / +0.85 / +0.42; skills +0.75 / −0.20 / +1.56.

### 9. Reading the result honestly

- **With convention-dense tasks and a frozen memory, the gap is clear and mechanistic.** The cold arm made the classic mistakes on every task — wrong denominator and date column on T11, leaking amount features and an out-of-band AUC on T12, causal wording and missing sections on T13 — and both warm arms made only the mistakes their memory had never covered. Memory transfers conventions, not competence.
- **The two memory formats diverged on T12 specifically.** `feedback_memory`'s verbatim log of T7's checker findings covered T12's failure modes almost exactly (same component family, same conventions) and passed clean on the first try. `skill_learning`'s two seeded skills are about caveats and denominators, not leakage — so it repeated the cold arm's `no_target_leakage` and `roc_auc_range` failures nearly verbatim, the one task where the raw log clearly beat the distilled library.
- **T13 shows the raw log's blind spot.** Neither the cold arm nor `feedback_memory` avoided causal language on the first try, because no note in the seeded log had ever corrected that wording — `run_006`'s T8 note was about citations and sources, not phrasing. `skill_learning` passed clean because its seeded caveat skill's own example happened to model associative phrasing.
- **Caveats that must travel with every number above:** one run per arm; operator noise of roughly ±0.2–0.4 on a first attempt (the skills arm's −0.20 on T12 is within that band); three tasks, not a large sample; the same author wrote the goldens, the blinded briefs and the redaction rule; held-out v1 (`run_007`) showed only a small gap because its tasks were too easy for a cold start, and it is reported here as superseded, not hidden — see Part B′.

### 10. Limitations

Single run per arm, as in every experiment in this study. Operator variance (~±0.2–0.4 on a first attempt) is not distinguishable from a small memory effect on any one task — the pattern is read across all three tasks together, not any single cell. Three held-out tasks is a smaller sample than `run_007`'s four, traded deliberately for convention density (D-24): each task now carries several conventions at once, so a single failed check moves the mean more than it did in `run_007`. All three tasks are built from earlier tasks' components verbatim (T11 from T2, T12 from T7, T13 from T8), so — as in `run_007` — this measures transfer of *convention*, not transfer to a wholly unfamiliar problem shape. The redaction rule is a regex over digit sequences, audited against every number in the three holdout goldens at ≥ 3 significant digits, not proven complete for arbitrary future goldens. The same author wrote the blinded briefs, the rubric and the seeding/redaction code, so the audit's negative result is a check on the author's own construction, not an external one. `run_008`'s numbers are not comparable task-for-task with any earlier experiment (D-24) — what is comparable is the three arms against each other inside `run_008`, and each arm's first-attempt behaviour against the same arm's behaviour in `run_006` on the task family it descends from (T11 vs T2, T12 vs T7, T13 vs T8).

### 11. Reproduce

```bash
uv run --extra dev pytest -q                                   # 192 tests
uv run python -m src.build_goldens --check                     # golden pack reproduces exactly (13 files)
uv run python -m src.run_experiment init --run-id run_008 --conditions reflection_only,feedback_memory,skill_learning --mode manual
uv run python scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13   # or a new held-out set named in config/tasks.yaml
uv run python -m src.run_experiment advance-all --run-id run_008   # then one fresh operator subagent per request (docs/OPERATOR_PROTOCOL.md)
uv run python scripts/summarize_run.py --run-id run_008
uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py --run-id run_008
```

The config keys that make this a transfer test rather than a fresh cold run are `seed_from_run: run_006`, `task_index_offset: 6` and — new in v2 — `memory_read_only: true` in `config/experiment.yaml`; `seed_from_run: run_007` would seed from an already-transferred (and now superseded) memory rather than a fresh baseline.

### Part B′ — held-out v1 (`run_007`, superseded)

The first attempt at the transfer test ran four held-out tasks, T9 → T10 → T5 → T6, with the memory still learning as it went (decision D-23). It reached the same directional conclusion — both warm arms opened at or above the cold arm on every task, and all three arms alike failed the one leakage convention no training task had taught (T5) — but the design had a **ceiling problem** (D-24): the cold arm's first attempts already scored **3.09–3.68** against the 3.50 pass threshold, so a warm arm had at most a few hundredths to gain on a first attempt. `reflection_only` took **7** attempts to pass all four tasks, against **5** each for `feedback_memory` and `skill_learning`; first-try passes were **1 / 4** (cold) vs **3 / 4** for each warm arm. Decision D-24 redesigned the test — three convention-dense tasks instead of four easier ones, and the memory frozen for the whole run — rather than re-running the same design hoping for a different sample. `run_007` is archived complete (logs, checkpoints, task artifacts, operator transcripts, its memory log and its one learned skill) at `archive/experiment-5_run_007_heldout-v1/`; `run_008` above is the reported run.

## Evidence index

`logs/experiment_events.jsonl` (attempt and done records: `score_by_attempt`, `attempts_to_pass`, `n_failed_checks`, `n_feedback_shown`, `skills_applied`, `self_declared_pass`, `past_feedback_count`, `evaluator_score_by_dimension`) · `logs/skill_events.jsonl` (`memory_retrieved` / `memory_written` for the two memory arms, plus the skill lifecycle) · `logs/graph_events.jsonl` (`self_evaluate` verdicts next to the frozen score) · `logs/feedback_events.jsonl` (what was shown, with `source`) · `artifacts/manual/run_006/` (115 request/response pairs) · `artifacts/memory/run_006/` (`feedback_memory.jsonl`, 19 notes; `self_refine_memory.jsonl`, 10 notes) · `artifacts/tasks/run_006/` (every attempt's metrics, report and charts) · `skills/evolved/run_006/` (the two persisted skills) · `artifacts/reports/run_summaries.json` · `config/freeze_manifest.json`.

**Experiment 5 v2 (`run_008`) additions:** `logs/runs/run_008.json` (`"seeding"` block — source run, redaction rule, records/tokens redacted, skill listing mode, `memory_read_only: true`) · `artifacts/memory/run_008/feedback_memory.jsonl` (19 seeded notes stamped `seeded_from: run_006`, unchanged at 19 for the whole run — recall only, no writes) · `skills/evolved/run_006/` (listed read-only into `run_008`'s retrieval, never copied; nothing new persisted under `skills/evolved/run_008/`) · `artifacts/manual/run_008/` (19 request/response pairs across the three arms) · `scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13` (clean; names the one golden value — `12339` — the redaction removed) · `archive/experiment-5_stub_006_smoke/` (the stub gate before the manual run) · `goldens/T11_portfolio_deep_dive_metrics.json`, `goldens/T12_high_cost_p90_model_contract.json`, `goldens/T13_cfo_brief_rubric.yaml` · `artifacts/reports/run_summaries.json` (`run_006` and `run_008` entries) · `config/freeze_manifest.json` (`bab215a5fbcc…`) · `articles/loop-engineering-markdown-skills/assets/transfer_curve.png`, `results_grid.png` (regenerated from `run_006` and `run_008`).

**Held-out v1 (`run_007`), archived:** `archive/experiment-5_run_007_heldout-v1/` — logs, checkpoints, task artifacts, operator transcripts, its memory log (25 notes at task end) and its one learned skill (`evolved_run_007_001`); superseded by decision D-24.

## LinkedIn draft

I gave a small model six claims-analytics tasks — including "here are five raw files, tell us if we can trust them" and "write the exec summary" — and did not tell it the house rules. Five ways of closing the loop, same tasks, same frozen answer key:
– checker feedback, no memory: 14 attempts to pass 6 tasks
– checker feedback + a plain, unedited log of every comment it was ever shown: 11 attempts — and it passed the hardest task on the first try once it had 9 old comments to lean on
– checker feedback + a notebook of validated lessons it wrote itself: 13 attempts, similar final quality, twice the operator effort of the plain log
– reviewing its own work, no checker: declared every task done, the checker agreed once in six — and once talked itself out of a pass it had already earned
– the same self-review, plus a log of its own past verdicts: no better, sometimes worse

The cheapest possible memory — a log nobody curated — got most of the way to what a validated skill library got. That is either a reason to build simpler memory or a reason to ask harder questions about what the skill schema is actually buying you. One run, synthetic data, small numbers — but the shape is the point.

Then I redacted every number out of that memory, froze it completely — no new notes, no new skills allowed for the rest of the run — and pointed both warm arms at three denser held-out tasks built from the same components. Both warm arms still made only the mistakes their memory had never covered, while the cold arm made every classic mistake on every task. The comments carried the house rules forward; they didn't carry the answers.

Write-up and code in the comments. #AgenticAI #LangGraph #ClaimsAnalytics #Evaluation
