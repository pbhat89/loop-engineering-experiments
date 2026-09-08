# Write-up v5 — experiments 4 and 5: does a plain memory do what a validated skill does, and does either carry over?

**Reported runs:** `run_006` (experiment 4, Part A) and `run_007` (experiment 5, Part B) — both manual mode, Claude Haiku 4.5 as a fresh stateless subagent per decision. Experiments 1 (`run_001`), 2 (`run_004`) and 3 (`run_005`) are summarised at the end of Part A and archived under `archive/`. Every number below is computed from `logs/*.jsonl` and `artifacts/reports/run_summaries.json`; nothing is estimated. Synthetic data; educational demonstration; nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory or operational evidence. **Public article** (Substack-ready, PB voice): `articles/loop-engineering-markdown-skills/article.md` — web version at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee.

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

## Part B — experiment 5: does the memory carry over? (`run_007`)

**Reported run:** `run_007`, manual mode, freeze `74e64e1d38e3…`, evaluator 1.3, model `claude-haiku-4-5-20251001`. Experiment 4 (above) measured whether memory helps *within* a suite the arm was repeatedly corrected on. Experiment 5 asks the harder question decision D-23 poses: does what an arm accumulated in `run_006` transfer to tasks it has never attempted?

### 7. Design

**Four held-out tasks, none attempted by any earlier run**, order T9 → T10 → T5 → T6 (article tasks 7–10). T9 and T10 reuse T4's and T3's components and house conventions but ask different questions; T5 and T6 have never been run before and are blinded here for the first time. Every brief below is quoted verbatim from `config/tasks.yaml`; no convention is stated in any of them.

| # | Task | The sponsor's question (blinded brief, quoted) | What the frozen checker holds (examples of golden values) |
|---|---|---|---|
| 7 | T9 Denial hotspots | "The denials team wants to know where denials cluster by setting. How does the denial rate differ by place of service, by whether prior authorisation was required, and by network status? Which denial reason codes dominate? Produce the standard artifacts (denial code ranking table, denial rate by segment table and chart, report)." | denial-code shares over **denied** claims (CO-15 18.7 %/241, CO-4 16.0 %/206, CO-11 11.4 %/147 …); 11,559 claims without a code, 0 among denied; three segments (`place_of_service`, `auth_required_flag`, `network_status`) at `min_group_size` 30; new tolerance check — the largest place-of-service segment (code `22`) denial rate = 545/4,946 = 11.019 %; denominator = adjudicated claims; synthetic-data + small-group caveats required |
| 8 | T10 Specialty spend and denials | "Finance wants to know which provider specialties account for the most paid spend and how their denial rates compare. Compare claim volume, total and average paid amount and denial rate across specialties, and list the ten rendering providers with the highest paid spend, with their specialty and network status taken from the provider directory." | 25 specialties; the largest by paid spend is Critical Access Hospital — 1,225 claims, $898,337.36 paid, denial rate 137/1,172 = 11.69 %; `provider_ranking` now ranks by `paid_amount_sum` (T3 ranked by claim count), `top_n` 10, `min_claims` 30 — first row NPI 1450094833, Outpatient Clinic, In-Network, 82 claims, $126,138.73; `rendering_npi→providers` join many-to-one, 0 unmatched of 12,845; synthetic-data, small-group and association-not-causation caveats required |
| 9 | T5 Fraud-pattern exploration | "Explore how claims flagged by the fraud indicator differ from unflagged claims: how common is the flag, and which claim characteristics look different between the two groups? Produce the standard artifacts (comparison table, prevalence chart, report)." | 647/12,845 = 5.04 % prevalence, imbalance ratio 18.85; billed_amount mean $1,692.48 flagged vs $1,652.66 unflagged; `claim_type` shares shift (Professional 52.2 % flagged vs 55.0 % unflagged); `fraud_pattern_type` is a label-derived field and `member_sex`/`member_race_ethnicity`/`member_age_band` are prohibited protected attributes — none may enter the feature comparison; synthetic-data, class-imbalance, association-not-causation and no-operational-use caveats required |
| 10 | T6 Baseline fraud model | "Train a first model that predicts the fraud flag on medical claims — logistic regression plus one tree-based model — with a quarter of the claims held out for testing, and report how well each model does on the held-out claims." | stratified 75/25 split, seed 42, n_train 9,633 / n_test 3,212; preprocessing fit on train only; ROC-AUC sanity range [0.40, 1.0], PR-AUC ≥ 0.5 × prevalence_test; `prevalence_test` must land in [0.03, 0.07] (actual 0.0504); prohibited fields `fraud_pattern_type`, `claim_id`, `member_id`, `rendering_npi`; synthetic-data, class-imbalance, model-limitations and no-operational-use caveats required |

78 rubric checks across the four tasks (T9 16, T10 22, T5 18, T6 22), same five dimensions, same pass rule (score ≥ 3.5, no critical miss). Goldens for T9 and T10 are new, built by independent reference code that never imports the executor; the eight goldens carried over from experiments 3–4 are byte-identical apart from `built_at`. New freeze `74e64e1d38e3…` (experiment 4: `59fb61d35fe8…`).

**Three arms, two of them warm, no self-review arms** (experiment 4 already answered the self-review question — 6/6 declared done, 1/6 checker passes):

| Arm | Starting state | What it inherits from `run_006` |
|---|---|---|
| `reflection_only` — cold | empty | nothing |
| `feedback_memory` — warm | seeded | 19 raw checker-finding notes, every numeric token redacted |
| `skill_learning` — warm | seeded | the 2 learned skills, listed read-only from `skills/evolved/run_006/`, never copied |

**Seeding mechanics (D-23).** `config/experiment.yaml` sets `seed_from_run: run_006` and `task_index_offset: 6`. At `init`, `Runner._seed_memory` copies `artifacts/memory/run_006/feedback_memory.jsonl` (19 records) once, read-only, into `artifacts/memory/run_007/feedback_memory.jsonl`, stamping each record `seeded_from: run_006`. `skill_learning` needs no copy: `SkillStore(seed_run_ids=["run_006"])` simply also lists `skills/evolved/run_006/*.md`, so `evolved_run_006_001` and `evolved_run_006_002` are retrievable in `run_007` while new skills persist under `skills/evolved/run_007/`, numbered from `evolved_run_007_001`. `task_index_offset: 6` continues `run_006`'s task numbering (0–5) so a skill written after `run_006` index 0 or 1 stays eligible from `run_007`'s first task.

**Redaction rule.** Every numeric token in a seeded note's `text` and `detail` — digit sequences with optional thousands separators, decimals and a trailing percent sign — is replaced by `[n]`, except `T\d+` (task ids) and the quantile names `p90`/`p99`. Example: `"denial rate 1,286 / 12,339 = 10.42 % on T2, p90"` seeds as `"denial rate [n] / [n] = [n] on T2, p90"`. 24 numeric tokens were redacted across the 19 notes (confirmed live: `logs/runs/run_007.json`'s `seeding` block records `records_seeded: 19`, `numbers_redacted: 24`).

**Leakage audit, re-run for this write-up.** `uv run python scripts/seed_audit.py --run-id run_007 --holdout T9,T10,T5,T6` → **clean**: 181 material golden numbers (≥ 3 significant digits) in 1,833 string forms compared against 58 numeric tokens surviving in the seeded notes and skill files; 0 reachable. The audit also names what redaction *prevented*: 4 golden values from `run_006`'s T4 note — the denial-code counts 241 and 206 and their shares 0.1874 and 0.1602, all of which are T9 goldens — would otherwise have carried straight through. A golden number counts as leakable only at ≥ 3 significant digits (so a skill's `version: 1` or the illustrative `200` in `evolved_run_006_002`'s worked example do not count); no skill file needed editing or exclusion.

### 8. What happened

**Attempts and scores (frozen checker, every attempt), scores by attempt with failed checks on first try in brackets:**

| Task | `reflection_only` (cold) | `feedback_memory` (warm, 19 → 25 notes) | `skill_learning` (warm, 2 seeded skills) |
|---|---|---|---|
| T9 Denial hotspots | 3.26 → **4.00** (2) — [3, 0] failed checks | **3.52** (1) — [2] failed, 19 notes on hand | **3.77** (1) — [1] failed, `evolved_run_006_002` (denominator) cited |
| T10 Specialty spend | 3.09 → **3.69** (2) — [5, 2] failed checks | **3.64** (1) — [2] failed, 21 notes | **3.51** (1) — [3] failed, all three skills cited (incl. the new `evolved_run_007_001`) |
| T5 Fraud exploration | 3.28 → **4.00** (2) — [3, 0] failed checks | 3.44 → **4.00** (2) — [2, 0] failed, 23 notes | 3.28 → **4.00** (2) — [3, 0] failed; skill `evolved_run_007_001` retrieved, not cited |
| T6 Fraud model | **3.68** (1) — [2] failed checks | **3.68** (1) — [1] failed, 25 notes | **3.84** (1) — [1] failed, `evolved_run_006_001` (synthetic caveat) cited |
| **Total attempts** | **7** | **5** | **5** |
| Failed checks on first tries | 3+5+3+2 = **13** | 2+2+2+1 = **7** | 1+3+3+1 = **8** |
| First-try passes | 1 / 4 (T6) | 3 / 4 (T9, T10, T6) | 3 / 4 (T9, T10, T6) |
| Mean first-attempt score | 3.33 | 3.57 | 3.60 |
| Mean final score | 3.84 | 3.71 | 3.78 |
| Tasks passed (checker) | **4 / 4** | **4 / 4** | **4 / 4** |
| Operator steps used | 10 | 6 | 12 |

`skill_learning` wrote one new skill, `evolved_run_007_001` ("min-group-size threshold for segmented rates"), after T9 — rejected once for the same `example_present` check that tripped both `run_006` skills, persisted after one revision; retrieved 7 times, reused 5.

**First-try findings — what transferred, what was new:**

| Task | Failed by the cold arm only (convention transferred to both warm arms) | Failed by a warm arm too (partial transfer or new to this task) | Failed by every arm (no training task taught it) |
|---|---|---|---|
| T9 Denial hotspots | `segment_rates`, `largest_place_of_service_denial_rate`, `segment_denominator` — the adjudicated-claims denominator, again | `show_denominators`, `caveat_synthetic` (feedback_memory only); `min_group_size` (skill_learning only) | — |
| T10 Specialty spend | `groups_specialty`, `top_spend_specialty_denial_rate`, `group_denominator` | `provider_ranking_min_claims`, `join_check_rendering_npi` (both warm arms); `caveat_association` (skill_learning only) | — |
| T5 Fraud exploration | — | `caveat_synthetic` (cold and skill_learning, not feedback_memory) | `no_leaking_features`, `caveat_no_operational_use` — `fraud_pattern_type` / protected attributes, a convention no training task had taught |
| T6 Fraud model | `caveat_synthetic` | `caveat_model_limitations` (feedback_memory only) | `caveat_no_operational_use` (cold and skill_learning; feedback_memory alone caught it) |

### 9. Reading the result honestly

- **On every held-out task, both warm arms started at or above the cold arm's first attempt — never below.** The transferred conventions are visible directly in the first-try findings: the cold arm failed the adjudicated-claims-denominator convention on both T9 and T10 (`segment_denominator`, `group_denominator`) while neither warm arm did on either task.
- **T5 is the control the design was built to produce.** All three arms failed the leakage check on first try (`no_leaking_features`, plus `caveat_no_operational_use` on two of three) — a convention no training task had taught, since T2/T4/T3/T7's briefs never raised protected attributes or label-derived fields. Warm memory transferred conventions it had actually seen; it did not invent ones it hadn't.
- **The absolute gaps are smaller than on training tasks 4 and 6 (of experiment 4).** The cold arm's first attempts on the held-out tasks were already high (3.09–3.68) rather than the 1.29–2.81 seen on `run_006`'s T3/T8 first attempts — the held-out variants have fewer independent conventions to trip on than T4 and T3 originally did, so there is less gap for memory to close.
- **Caveats that must travel with every number above:** one run per arm; operator variance of roughly ±0.2–0.4 on a first attempt (seen directly in experiment 4's T1); four held-out tasks, not a large sample; the same author wrote the goldens and the blinded briefs; the leakage audit is only as good as its numeric-token rule, stated in full in §7 above and re-run live for this write-up.

### 10. Limitations

Single run per arm, as in every experiment in this study. Operator variance (~±0.2–0.4 on a first attempt) is not distinguishable from a small memory effect on any one task — the pattern is read across all four tasks together, not any single cell. Four held-out tasks is a small sample, and two of them (T9, T10) are recombinations of T4's and T3's own components rather than fully independent tasks — the transfer they exercise is narrower than T5/T6's. The redaction rule is a regex over digit sequences; it is audited against every number in the four holdout goldens at ≥ 3 significant digits, not proven complete for arbitrary future goldens. `run_006` is not archived, because the article's figures read both runs, which means `run_007` is not a fully independent replication in the filesystem sense (though its evaluation, freeze and goldens are). The same author wrote the blinded briefs, the rubric and the seeding/redaction code, so the audit's negative result (no leakage) is a check on the author's own construction, not an external one. Experiment-5 numbers are not comparable task-for-task with any earlier experiment (D-23) — what is comparable is the three arms against each other inside `run_007`, and each arm's held-out first attempt against its own family task in `run_006`.

### 11. Reproduce

Experiment 5's carry-over mechanics are configuration, not a CLI flag — reproducing a transfer test onto a new held-out suite means setting `config/experiment.yaml`'s `seed_from_run` and `task_index_offset` keys (currently `run_006` / `6`) and the held-out `task_order`/briefs in `config/tasks.yaml`, then running the same loop with a new run id:

```bash
uv run --extra dev pytest -q                                   # 188 tests
uv run python -m src.build_goldens --check                     # golden pack reproduces exactly (10 files)
uv run python -m src.run_experiment init --run-id run_008 --conditions reflection_only,feedback_memory,skill_learning --mode manual
uv run python scripts/seed_audit.py --run-id run_008 --holdout T9,T10,T5,T6   # or a new held-out set named in config/tasks.yaml
uv run python -m src.run_experiment advance-all --run-id run_008   # then one fresh operator subagent per request (docs/OPERATOR_PROTOCOL.md)
uv run python scripts/summarize_run.py --run-id run_008
uv run python articles/loop-engineering-markdown-skills/assets/make_figures.py --run-id run_008
```

`seed_from_run: run_007` is **not** how you would rerun this experiment — the config key names the run to seed *from*, and pointing it at `run_007` would seed from a warm, already-transferred memory rather than a fresh baseline; a genuine repeat seeds from `run_006` (or another cold run) exactly as `run_007` did.

## Evidence index

`logs/experiment_events.jsonl` (attempt and done records: `score_by_attempt`, `attempts_to_pass`, `n_failed_checks`, `n_feedback_shown`, `skills_applied`, `self_declared_pass`, `past_feedback_count`, `evaluator_score_by_dimension`) · `logs/skill_events.jsonl` (`memory_retrieved` / `memory_written` for the two memory arms, plus the skill lifecycle) · `logs/graph_events.jsonl` (`self_evaluate` verdicts next to the frozen score) · `logs/feedback_events.jsonl` (what was shown, with `source`) · `artifacts/manual/run_006/` (115 request/response pairs) · `artifacts/memory/run_006/` (`feedback_memory.jsonl`, 19 notes; `self_refine_memory.jsonl`, 10 notes) · `artifacts/tasks/run_006/` (every attempt's metrics, report and charts) · `skills/evolved/run_006/` (the two persisted skills) · `artifacts/reports/run_summaries.json` · `config/freeze_manifest.json`.

**Experiment 5 (`run_007`) additions:** `logs/runs/run_007.json` (`"seeding"` block — source run, redaction rule, records/tokens redacted, skill listing mode) · `artifacts/memory/run_007/feedback_memory.jsonl` (19 seeded notes stamped `seeded_from: run_006`, growing to 25 by task end) · `skills/evolved/run_007/` (`evolved_run_007_001_v1.md`, the one skill learned in this run) · `skills/evolved/run_006/` (listed read-only into `run_007`'s retrieval, never copied) · `artifacts/manual/run_007/` (28 request/response pairs across the three arms) · `scripts/seed_audit.py --run-id run_007 --holdout T9,T10,T5,T6` (clean; names the 4 golden values the redaction removed) · `archive/experiment-5_stub_005_smoke/` (the stub gate before the manual run) · `goldens/T9_denial_hotspots_metrics.json`, `goldens/T10_specialty_spend_metrics.json` · `artifacts/reports/run_summaries.json` (both `run_006` and `run_007` entries) · `config/freeze_manifest.json` (`74e64e1d38e3…`) · `articles/loop-engineering-markdown-skills/assets/transfer_curve.png`, `results_grid.png` (regenerated from both runs).

## LinkedIn draft

I gave a small model six claims-analytics tasks — including "here are five raw files, tell us if we can trust them" and "write the exec summary" — and did not tell it the house rules. Five ways of closing the loop, same tasks, same frozen answer key:
– checker feedback, no memory: 14 attempts to pass 6 tasks
– checker feedback + a plain, unedited log of every comment it was ever shown: 11 attempts — and it passed the hardest task on the first try once it had 9 old comments to lean on
– checker feedback + a notebook of validated lessons it wrote itself: 13 attempts, similar final quality, twice the operator effort of the plain log
– reviewing its own work, no checker: declared every task done, the checker agreed once in six — and once talked itself out of a pass it had already earned
– the same self-review, plus a log of its own past verdicts: no better, sometimes worse

The cheapest possible memory — a log nobody curated — got most of the way to what a validated skill library got. That is either a reason to build simpler memory or a reason to ask harder questions about what the skill schema is actually buying you. One run, synthetic data, small numbers — but the shape is the point.

Then I redacted every number out of that memory and pointed both warm arms at four tasks neither had ever seen — two of them (fraud detection) conventions no training task had even taught. Both warm arms still opened at or above the cold arm on every held-out task, and the one convention nobody had taught — don't leak the protected attributes — tripped all three arms alike. The comments carried the house rules forward; they didn't carry the answers.

Write-up and code in the comments. #AgenticAI #LangGraph #ClaimsAnalytics #Evaluation
