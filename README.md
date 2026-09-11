# claims-skill-loop

An educational, reproducible **LangGraph** experiment in loop engineering on synthetic healthcare claims: a claims-analysis agent plans a task from a fixed component catalogue, deterministic code executes it, a deterministic evaluator scores the output against a **frozen golden pack and rubric**, the agent reflects on the (capped) feedback and retries, distils reusable lessons into **versioned Markdown skills**, and retrieves those skills on later tasks. Three arms run the same tasks so the effect of the verifier and of persistent skills can be compared.

## Honest framing

- **Synthetic data only.** HLT-008 synthetic healthcare claims sample (CC-BY-NC-4.0). Nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory, or operational evidence.
- **External procedural memory, not training.** The "learning" is Markdown skill files retrieved into the planner's context; no model weights change.
- **No model API calls.** In `manual` mode the graph pauses on a LangGraph interrupt at each decision node and a fresh, **stateless Claude Code subagent** answers one JSON request (experiment 1: Claude Fable 5.1; experiments 3-6: Claude Haiku 4.5; experiment 7: Claude Fable 5.1). In `rule_learner` mode a deterministic convention learner answers instead — no LLM at all (experiment 2). `stub` mode uses trivial fixtures for tests and is always labelled non-LLM simulation. No API key, Agent SDK, headless-CLI bridge, or session-credential reuse of any kind.
- **Illustrative results.** One run per arm; comparisons are reported as illustrative, populated only from the recorded logs.

## Results so far

| Experiment | Planner | Suite | Headline | Where |
|---|---|---|---|---|
| 1 — `run_001` | stateless Claude Fable 5.1 subagents, briefs stating the conventions | 8 tasks, 3 attempts, full feedback | Ceiling: every condition 4.00 first attempt, 0 retries, 0 feedback → 0 grounded skills (null result) | `archive/experiment-1_run_001/` |
| 2 — `run_004` | deterministic rule learner from textbook defaults | 8 tasks, 3 attempts, full feedback with literal fixes | baseline = reflection_only **1.55** vs skill_learning **2.17** first-attempt mean (T2–T8); 6 skills, 22 reuses; but every task converged after exactly one retry | `archive/experiment-2_run_004/` |
| 3 — `run_005` | stateless **Claude Haiku 4.5** subagents, **blinded** briefs and operator, feedback capped to the 3 most severe findings with the fix withheld, 5 attempts, empty starting library | 4 tasks: T2 → T4 → T3 → T7 | **Checker, no memory:** 10 attempts to pass 4 tasks (3, 3, 2, 2), 29 failed checks on first tries. **Checker + skills:** 8 attempts (2, 2, 2, 2), 22 failed checks; one learned skill (adjudicated-claims denominator), applied on 2 of 3 later tasks. **Self-review only:** declared every task done; the frozen checker failed 3 of the 4 (2.89, 3.14, 1.61), passed T7 at 3.60 after the agent caught its own leakage | `archive/experiment-3_run_005/` (writeup at `archive/experiment-3_run_005/docs/writeup_run_005.md`) |
| 4 — `run_006` | stateless **Claude Haiku 4.5** subagents, **blinded** briefs (T1 and T8 blinded too) and operator, feedback capped to the 3 most severe findings, 5 attempts, **five arms** — two of them a plain raw-memory log instead of the checker/self-review split | 6 tasks: T1 → T2 → T4 → T3 → T7 → T8 | **Checker, no memory:** 14 attempts to pass 6 tasks, 39 first-try failures. **Checker + raw log:** 11 attempts, 20 failures — passed T3 first try with 9 past notes already logged. **Checker + skills:** 13 attempts, 28 failures; 2 learned skills, 5 reuses. **Self-review only:** declared 6/6 done, checker passed 1/6 (T7 only); revised a checker-passing T8 attempt into a fail. **Self-review + raw log:** same pattern; a memory of its own past verdicts did not help (lowest mean final score of all five arms, 2.89) | `docs/writeup.md`, `articles/loop-engineering-markdown-skills/` |
| 5 — `run_008` (v2; supersedes `run_007`, archived) | stateless **Claude Haiku 4.5** subagents, **blinded** briefs and operator, a **held-out transfer test with the memory frozen** — two arms seeded (read-only) from `run_006`'s memory and skills, one arm cold, feedback capped to the 3 most severe findings, 5 attempts, no memory writes for the whole run | 3 convention-dense held-out tasks built verbatim from earlier components: T11 (T2's) → T12 (T7's, 90th percentile) → T13 (T8's, sourced only from T11/T12) | **Cold (no memory):** 6 attempts to pass 3 tasks, 14 first-try failures, first-attempt mean 2.81, 0/3 first-try passes. **Warm, raw log (19 notes seeded, frozen):** 4 attempts, 3 failures, first-attempt mean 3.58, 2/3 first-try passes. **Warm, seeded skills (2 inherited, frozen — none new written):** 4 attempts, 8 failures, first-attempt mean 3.52, 2/3 first-try passes. Both warm arms opened at or above the cold arm on every task; the raw log beat the skills on T12 (leakage/AUC — no seeded skill covers it), the skills beat the raw log on T13 (causal language — no seeded note covers it). `run_007` (4 easier held-out tasks, memory still learning) hit a ceiling — cold first attempts 3.09–3.68 — and is archived at `archive/experiment-5_run_007_heldout-v1/` | `docs/writeup.md` (Part B; v1 in Part B′), `articles/loop-engineering-markdown-skills/` |

| 7 — the underwriting apprentice (built, **not yet run live**) | stateless **Claude Fable 5.1** subagents (`model: fable`), one per request; the starter manual is the only written practice and **fourteen house rules are never shown** | **one job, 38 times**: rate a life-insurance application — 30 training cases with a reviewer markup after each, then 8 held-out with memories frozen | Five arms: `new_joiner` · `notebook` · `written_rules` · `precedent` · `ask_senior`. Headline metric: rating distance in ladder steps. Built and gated by a stub smoke (all five arms, leakage audit 0). The measured floor — what a careful reader of the manual alone scores — is **0.933** training / **0.875** held-out; that is the most any memory can recover | `docs/underwriting-apprentice-design.md`, decision D-27, `archive/experiment-7_stub_smoke/` (stub) |

Experiments 1-5 are single runs on synthetic data — illustrative, not evidence of anything operational. Experiment 7 has been built and stub-gated; no live result exists yet. The article about the experiments (Substack-ready Markdown + a self-contained web version) is in `articles/loop-engineering-markdown-skills/`; read it online at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee.

## Repository layout

```text
config/        experiment.yaml, graph.yaml (A1) · tasks.yaml, rubric.yaml (A3) · freeze_manifest.json (L0, Phase 1.5)
               underwriting.yaml (experiment 7)
data/          raw/ (git-ignored CSVs) · processed/manifest.json (data contract) · README.md (source, licence, schema)
               underwriting/ (experiment 7: starter manual, house rules, 38 cases, goldens, freeze manifest)
docs/          idea, spec, plan (interface contract), tasks (backlog), security-review, decision-log, verification-log, writeup, OPERATOR_PROTOCOL
               underwriting-apprentice-design, underwriting-build-brief (experiment 7)
goldens/       golden evaluation pack T1–T10, built once by independent reference code and frozen by hash
skills/        SKILL_SCHEMA.md · foundational/ (6 curated skills, not used in experiment 3) · evolved/<run_id>/ (learned, immutable) · archived/ · index.json
src/           llm_provider, graph_state, claims_graph, graph_nodes, run_experiment (L0) · download_data, profile_data (A2)
               build_goldens, evaluator (A3) · skill_store, skill_validator (A4) · experiment_logger, dashboard, charts (A5)
               task_runner + analyses/ (A6) · rule_learner (experiment 2) · agent_tracker, utils (L0)
               underwriting/ (experiment 7: the rating engines, the five arms, its own graph and runner)
tests/         offline pytest suite (stub mode; data-dependent tests skip without data) · underwriting/ (experiment 7)
scripts/       bootstrap.sh, run_all.sh, verify.sh (+ Python equivalents) · summarize_run.py · archive_run.py · summarize_uw_run.py
logs/          agent_status.json, agent_events.jsonl, experiment/graph/skill/feedback JSONL, experiment_status.json, checkpoints/
artifacts/     dashboard/progress.html · figures/ · graphs/ · tasks/<run_id>/… · manual/<run_id>/… (operator transcripts) · memory/<run_id>/<condition>.jsonl (raw-memory arms) · data_profile/ · reports/
               uw/<run_id>/ (experiment 7: requests, responses, per-arm logs and memories)
archive/       experiments 1 and 2 and the pre-fix / smoke runs, each with a README
.claude/agents/  the builder subagents plus the three stateless operators (experiment-operator, experiment-operator-blind, underwriter-operator)
```

## Quickstart

```bash
uv sync --extra dev                      # pinned environment (Python 3.12; pandas 3, scikit-learn 1.9, langgraph 1.2)
cp .env.example .env                     # optional — defaults already select manual mode, no key needed
./scripts/bootstrap.sh                   # validate config → one-time dataset download → profile → build goldens
uv run --extra dev pytest -q             # offline tests (314 collected)
./scripts/run_all.sh                     # config check → data → profile → topology → run conditions → refresh dashboard/charts → verify
./scripts/verify.sh                      # tests, log validation, freeze check, security greps
```

Python equivalents: `uv run python -m src.download_data` · `uv run python -m src.profile_data` · `uv run python -m src.build_goldens [--check]` · `uv run python -m src.run_experiment …` · `uv run python -m src.dashboard` · `uv run python -m src.charts`. The `uv run` warning about `VIRTUAL_ENV` is harmless.

## Runtime modes

| Mode | Default | What happens | Credentials |
|---|:-:|---|---|
| `manual` | **yes** | graph pauses at each LLM-decision node; request JSON written under `artifacts/manual/`; a stateless operator subagent writes the response; the lead resumes | none |
| `rule_learner` | | a deterministic **convention learner** (`src/rule_learner.py`) answers every decision; experiment 2 | none |
| `stub` | | deterministic fixtures answer every decision; tests and pipeline demos; labelled non-LLM simulation | none |
| `anthropic_api` | | thin fail-closed adapter around `langchain-anthropic`; refuses to start without `ANTHROPIC_API_KEY`; **not used in this study** | separate Anthropic Console billing, never the Claude Code subscription |

Set with `CLAIMS_SKILL_LOOP_LLM_MODE`; see `.env.example` and `docs/plan.md` §2.

## Experiment 7: the underwriting apprentice (`config/underwriting.yaml`, decision D-27)

A different job on the same machinery, because the claims experiment failed for one structural reason: a learning curve needs **the same job repeated**, and six different tasks each with their own conventions is six one-shot trials. So: **one job, thirty-eight times** — rate a life-insurance application — against **fourteen house rules nobody is told**.

30 training cases with a reviewer markup after each, then 8 held-out cases with memories frozen and no markup. Five loop designs, identical in every respect except what each is handed before it decides and what it keeps afterwards:

| Arm | Handed at decide time | Kept afterwards |
|---|---|---|
| `new_joiner` | the starter manual | nothing. Permanently on day one |
| `notebook` | + every past markup, verbatim, newest first | appends the markup as written (no model call) |
| `written_rules` | + its own house-rule book | a reflection call rewrites the whole book in its own words |
| `precedent` | + the 3 nearest past cases with their correct answers | files this case with its correct answer (no model call) |
| `ask_senior` | may first ask up to 4 questions, answered by a deterministic oracle | nothing. Pays the cost again every case |

Headline metric: **rating distance in ladder steps** (Pref+ 0 · Pref 1 · Std+ 2 · Std 3 · Table 2 4 · Table 4 5 · Table 6 6 · Table 8 7 · Decline 8). Postpone sits off the ladder and costs a fixed 2 when exactly one side postpones. Also scored per case: decision exact match, modifier F1 with the flat-extra band included, driver recall.

Everything the operator sees is the ~985-word starter manual (`data/underwriting/starter_manual.md`) plus the case. The manual carries every number it has and is honest about its gaps — twelve lines saying *refer to underwriting judgement*, none of them saying what fills the gap. House rules, tier labels and goldens never reach a request payload, and `src/underwriting/audit.py` asserts that over every request file a run writes.

Case tiers are **derived, never assigned**: a rule *fires* when switching it off alone changes the scored answer, and the tier is the count. 30 training cases run 9 clean / 13 judgement / 8 compound with the mix held constant across every window of ten, and case 1 is not clean. Each of rules 1–12 fires in at least three training cases in at least two shapes; rules 13 and 14 appear only in the held-out set, so everyone should miss those two.

### Running it (manual mode, five arms, train then held-out)

```bash
python -m src.underwriting.data verify              # re-derives the pack from code and checks the freeze

# training. Arms are independent - these five may run at the same time.
python -m src.underwriting.run --run-id uw_001 --condition new_joiner    --phase train
python -m src.underwriting.run --run-id uw_001 --condition notebook      --phase train
python -m src.underwriting.run --run-id uw_001 --condition written_rules --phase train
python -m src.underwriting.run --run-id uw_001 --condition precedent     --phase train
python -m src.underwriting.run --run-id uw_001 --condition ask_senior    --phase train
#   OPERATOR NEEDED [notebook/train] -> artifacts/uw/uw_001/requests/notebook/train_case01_decide.json
#                    response -> artifacts/uw/uw_001/responses/notebook/train_case01_decide.json
# spawn one fresh underwriter-operator subagent per request (prompt template in
# docs/OPERATOR_PROTOCOL.md), then run the same command again. Repeat until it prints DONE.

# held-out, per arm, only once that arm's training has printed DONE. Memories are frozen here:
# the arm still reads what training left behind and writes nothing back.
python -m src.underwriting.run --run-id uw_001 --condition new_joiner    --phase holdout
python -m src.underwriting.run --run-id uw_001 --condition notebook      --phase holdout
python -m src.underwriting.run --run-id uw_001 --condition written_rules --phase holdout
python -m src.underwriting.run --run-id uw_001 --condition precedent     --phase holdout
python -m src.underwriting.run --run-id uw_001 --condition ask_senior    --phase holdout

python -m src.underwriting.run status --run-id uw_001         # per-arm, per-phase progress
python -m src.underwriting.run audit  --run-id uw_001         # leakage audit over every request file
python scripts/summarize_uw_run.py --run-id uw_001 --json artifacts/uw/uw_001/summary.json
```

Add `--poll` if you would rather the runner waited for each response file than returned. Add `--mode stub --max-cases N` for a dry run with the deterministic stub operator (always labelled stub).

Expected live calls: 38 + 38 + 68 + 38 + 76 = **258** (written_rules adds a reflection per training case; ask_senior asks before it decides).

### Where things are

```text
config/underwriting.yaml        the five arms, the two phases, the operator, the caps
data/underwriting/              starter_manual.md · house_rules.json (never shown) · cases.json · goldens.json
                                + freeze_manifest.json (freeze d95f49f1f930...)
src/underwriting/               tables · manual · house_rules · engine · cases · scorer · markup · memory
                                precedent · senior · state · nodes · graph · run · stub · audit · data
artifacts/uw/<run_id>/          requests/ · responses/ · <arm>/cases.jsonl · notebook/ · written_rules/ · precedent/
scripts/summarize_uw_run.py     per-arm tables, trailing-5 series, the three registered validation checks
.claude/agents/underwriter-operator.md   the stateless operator (model: fable)
archive/experiment-7_stub_smoke/         the stub gate - labelled stub, no model called
tests/underwriting/             119 tests
```

## Experiment 5 in one screen (`config/experiment.yaml`, decision D-24; v1 was D-23)

A **held-out transfer test with the memory frozen**: what did run_006 leave behind, on questions it has never seen?

| Knob | Value | Why |
|---|---|---|
| tasks | `T11, T12, T13` — portfolio deep-dive, high-cost model at the 90th percentile, CFO brief (article tasks 7–9) | each task reuses an earlier task's components verbatim (T2, T7, T8) so every convention the memory carries is on-topic, and each is dense enough (T11 alone exercises six convention families at once) that a naive plan starts near 1.5, not near 3.5 |
| briefs | **blinded**, all three | no convention is stated anywhere in the suite |
| arms | `reflection_only` (cold: checker feedback, no memory) · `feedback_memory` (**warm**: seeded with run_006's 19 raw notes) · `skill_learning` (**warm**: seeded with run_006's two learned skills) | isolates *transfer* of a raw log vs a distilled procedure; no self-review arms (experiment 4 settled that) |
| memory | **frozen for the whole run** (`memory_read_only: true`) — recall still works, nothing is written; `skill_learning` never reflects, proposes or persists | separates "what the memory carries" from "what the run learns on its way through" — the confound that limited v1 |
| seeding | unchanged from v1: `seed_from_run: run_006`, read-only. Memory copied once with **every numeric token redacted to `[n]`** (except task ids and `p90`/`p99`); skills merely *listed* from `skills/evolved/run_006/` and never copied | a warm arm may inherit conventions, never a golden value |
| task numbering | `task_index_offset: 6` — run_008's tasks are indices 6–8, continuing run_006's 0–5 | keeps skills learned after run_006's first tasks eligible from task one |
| leakage audit | `scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13` — **clean**; it also names the one golden value (`12339`, T11's denial-rate denominator) the redaction removed | the no-leakage claim is checkable, not asserted |
| goldens | three new files (`T11_portfolio_deep_dive_metrics.json`, `T12_high_cost_p90_model_contract.json`, `T13_cfo_brief_rubric.yaml`) from parameterised reference code; the ten existing goldens byte-identical apart from `built_at`; new freeze `bab215a5fbcc…` | the earlier pack is untouched |
| winnability check | catalogue defaults score 1.18 / 1.69 / 1.57 on T11/T12/T13; the house conventions score 4.00 / 4.00 / 4.00 | confirms the cold arm actually has room to fall, unlike v1 |
| feedback, attempts, library | unchanged from experiments 3–4: 3 most severe findings, fix withheld, 5 attempts, no foundational skills | only the suite, the starting memory and the freeze change |
| v1 | `run_007` — four easier held-out tasks, memory still learning mid-run — hit a ceiling (cold first attempts 3.09–3.68) and is archived at `archive/experiment-5_run_007_heldout-v1/` | superseded, not deleted; decision D-24 explains why |

## Experiment 4 in one screen (`config/experiment.yaml`, decision D-22)

| Knob | Value | Why |
|---|---|---|
| tasks | `T1, T2, T4, T3, T7, T8` — dataset reconnaissance, describe the book, denials by segment, providers & network, high-cost model, executive brief | opens and closes the suite on tasks whose house rules must also be learned, not just read off the brief |
| briefs | **blinded**, T1 and T8 included — written as a sponsor would ask; no denominators, thresholds, train-only rules, required sections or caveats | the loop has to *learn* the house rules from the checker, start to finish |
| operator | fresh stateless Claude Haiku 4.5 subagent per request, `experiment-operator-blind.md` (no convention list) | a planner that can fail, without leaking the rubric into its prompt |
| feedback | the **3 most severe** failed checks per attempt, literal fix withheld; the rest is a count | so the verification loop has to iterate instead of closing after one retry |
| attempts | up to 5 per task; pass = score ≥ 3.5 and no critical miss | room to watch score-versus-attempt curves |
| library | starts **empty**; only skills learned in the run are retrievable | learned memory vs none, not curated library vs none |
| raw memory | a plain per-condition log — every checker finding shown (`feedback_memory`) or every self-review finding written (`self_refine_memory`) is appended verbatim to `artifacts/memory/<run_id>/<condition>.jsonl` and shown in full (newest first, ≤ 30 items) before planning a later task; no distillation, filtering, ranking or dedup | the cheapest possible memory — isolates *carrying comments forward* from *learning a reusable procedure* |
| arms | `reflection_only` (checker, no memory) · `feedback_memory` (checker + raw log) · `skill_learning` (checker + skills) · `self_refine` (self-review only, never sees the checker) · `self_refine_memory` (self-review + a log of its own past reviews) | a 2×2 (checker vs. self-review) × (memory vs. none) plus the skills arm |
| golden change | none since experiment 3; only `config/tasks.yaml`'s T1/T8 briefs and `task_order` changed | rubric and goldens are byte-identical to experiment 3 |

## The golden-pack step (Phase 1.5) — before any comparative run

1. `uv run python -m src.build_goldens` computes expected metrics, contracts, and checks from the downloaded data with independent pandas code (never the executor's code).
2. `uv run python -m src.build_goldens --check` reproduces them exactly.
3. **The user reviews the golden values** (checkpoint).
4. The lead writes `config/freeze_manifest.json` (SHA-256 of tasks, rubric, goldens, raw data). `init` refuses to start a manual run if any hash drifts, and every evaluation event carries `freeze_sha256`. Experiment 5 v2 freeze: `bab215a5fbcc…` (v1: `74e64e1d38e3…`; experiment 4: `59fb61d35fe8…`; experiment 3: `64b7292e8214…`; experiments 1–2: `1566c5698a50…`).

## Running the experiment (manual mode, experiment 5)

```bash
uv run python -m src.run_experiment run-stub --run-id stub_check --conditions reflection_only,feedback_memory,skill_learning   # pipeline must pass first
uv run python -m src.run_experiment init        --run-id run_008 --conditions reflection_only,feedback_memory,skill_learning --mode manual
uv run python scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13   # no holdout golden number may reach the seeded memory or skills
uv run python -m src.run_experiment advance-all --run-id run_008      # prints the pending request per condition
#   → the lead spawns one fresh operator subagent per request (prompt template in docs/OPERATOR_PROTOCOL.md), then advance-all again
uv run python -m src.run_experiment status      --run-id run_008
uv run python scripts/summarize_run.py --run-id run_008 --json artifacts/reports/run_summaries.json
uv run python scripts/archive_run.py --run-id run_008 --folder <name>   # when a run is superseded
```

Stopping rules: pass → finalise immediately; `max_retries = 4`; the self-review arms stop when the operator says "accept" (not run in `run_008`); skills proposed only for lessons reusable in ≥ 2 remaining tasks, ≤ 1 revision (not exercised in `run_008` — `memory_read_only: true` closes the learn path); the two memory arms cost no extra operator steps (recall/write are file operations); hard cap of 64 operator steps per condition; all arms always run all tasks.

## Running the experiment (rule-learner mode, experiment 2)

```bash
uv run python -m src.run_experiment run-auto --run-id run_007 --mode rule_learner   # deterministic, ~2 minutes, no interrupts, no LLM
```

## Where to look while it runs

| What | Where |
|---|---|
| Build tracker + live experiment status (auto-refreshing static HTML) | `artifacts/dashboard/progress.html` |
| Machine-readable status (current task/node, pending request, steps vs cap, rough ETA) | `logs/experiment_status.json`, `logs/agent_status.json` |
| Learning curve, reliability curve, rubric heatmap, skill accumulation, skill utility | `artifacts/figures/` |
| Article figures (score by attempt, attempts and first-try findings, self-review vs checker) | `articles/loop-engineering-markdown-skills/assets/` |
| LangGraph topology (designed workflow) and observed skill-lifecycle graph (from logs) | `artifacts/graphs/` |
| Per-attempt task outputs (metrics.json, report.md, charts) | `artifacts/tasks/<run_id>/<condition>/<task_id>/attempt_<n>/` |
| Operator transcripts (every request and response) | `artifacts/manual/<run_id>/<condition>/` |
| Learned skills | `skills/evolved/<run_id>/` |
| Write-up material | `docs/writeup.md`, `artifacts/reports/` |

## Documentation

`docs/idea.md` (why) · `docs/spec.md` (what, acceptance criteria, stopping rules) · `docs/plan.md` (interface contract every module codes against) · `docs/tasks.md` (weighted backlog driving the dashboard) · `docs/OPERATOR_PROTOCOL.md` · `docs/security-review.md` · `docs/decision-log.md` (D-01…D-21) · `docs/verification-log.md` (only checks actually run) · `docs/writeup.md`.

## Licence and attribution

- Code: MIT (see `pyproject.toml`).
- Data: **HLT-008 Synthetic Healthcare Claims Dataset — sample**, `xpertsystems/hlt008-sample` on Hugging Face, revision `7309ddb30e67468748b7aa9182d8517fe28c2f9c`, licensed **CC BY-NC 4.0**. Used for non-commercial educational purposes; raw files are not redistributed in this repository. Full details in `data/README.md`.
