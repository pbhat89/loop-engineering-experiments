# claims-skill-loop

An educational, reproducible **LangGraph** experiment in loop engineering on synthetic healthcare claims: a claims-analysis agent plans a task from a fixed component catalogue, deterministic code executes it, a deterministic evaluator scores the output against a **frozen golden pack and rubric**, the agent reflects on the (capped) feedback and retries, distils reusable lessons into **versioned Markdown skills**, and retrieves those skills on later tasks. Three arms run the same tasks so the effect of the verifier and of persistent skills can be compared.

## Honest framing

- **Synthetic data only.** HLT-008 synthetic healthcare claims sample (CC-BY-NC-4.0). Nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory, or operational evidence.
- **External procedural memory, not training.** The "learning" is Markdown skill files retrieved into the planner's context; no model weights change.
- **No model API calls.** In `manual` mode the graph pauses on a LangGraph interrupt at each decision node and a fresh, **stateless Claude Code subagent** answers one JSON request (experiment 1: Claude Fable 5.1; experiment 3: Claude Haiku 4.5). In `rule_learner` mode a deterministic convention learner answers instead — no LLM at all (experiment 2). `stub` mode uses trivial fixtures for tests and is always labelled non-LLM simulation. No API key, Agent SDK, headless-CLI bridge, or session-credential reuse of any kind.
- **Illustrative results.** One run per arm; comparisons are reported as illustrative, populated only from the recorded logs.

## Results so far

| Experiment | Planner | Suite | Headline | Where |
|---|---|---|---|---|
| 1 — `run_001` | stateless Claude Fable 5.1 subagents, briefs stating the conventions | 8 tasks, 3 attempts, full feedback | Ceiling: every condition 4.00 first attempt, 0 retries, 0 feedback → 0 grounded skills (null result) | `archive/experiment-1_run_001/` |
| 2 — `run_004` | deterministic rule learner from textbook defaults | 8 tasks, 3 attempts, full feedback with literal fixes | baseline = reflection_only **1.55** vs skill_learning **2.17** first-attempt mean (T2–T8); 6 skills, 22 reuses; but every task converged after exactly one retry | `archive/experiment-2_run_004/` |
| 3 — `run_005` | stateless **Claude Haiku 4.5** subagents, **blinded** briefs and operator, feedback capped to the 3 most severe findings with the fix withheld, 5 attempts, empty starting library | 4 tasks: T2 → T4 → T3 → T7 | **Checker, no memory:** 10 attempts to pass 4 tasks (3, 3, 2, 2), 29 failed checks on first tries. **Checker + skills:** 8 attempts (2, 2, 2, 2), 22 failed checks; one learned skill (adjudicated-claims denominator), applied on 2 of 3 later tasks. **Self-review only:** declared every task done; the frozen checker failed 3 of the 4 (2.89, 3.14, 1.61), passed T7 at 3.60 after the agent caught its own leakage | `archive/experiment-3_run_005/` (writeup at `archive/experiment-3_run_005/docs/writeup_run_005.md`) |
| 4 — `run_006` | stateless **Claude Haiku 4.5** subagents, **blinded** briefs (T1 and T8 blinded too) and operator, feedback capped to the 3 most severe findings, 5 attempts, **five arms** — two of them a plain raw-memory log instead of the checker/self-review split | 6 tasks: T1 → T2 → T4 → T3 → T7 → T8 | **Checker, no memory:** 14 attempts to pass 6 tasks, 39 first-try failures. **Checker + raw log:** 11 attempts, 20 failures — passed T3 first try with 9 past notes already logged. **Checker + skills:** 13 attempts, 28 failures; 2 learned skills, 5 reuses. **Self-review only:** declared 6/6 done, checker passed 1/6 (T7 only); revised a checker-passing T8 attempt into a fail. **Self-review + raw log:** same pattern; a memory of its own past verdicts did not help (lowest mean final score of all five arms, 2.89) | `docs/writeup.md`, `articles/loop-engineering-markdown-skills/` |

All four are single runs on synthetic data — illustrative, not evidence of anything operational. The article about the experiments (Substack-ready Markdown + a self-contained web version) is in `articles/loop-engineering-markdown-skills/`; read it online at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee.

## Repository layout

```text
config/        experiment.yaml, graph.yaml (A1) · tasks.yaml, rubric.yaml (A3) · freeze_manifest.json (L0, Phase 1.5)
data/          raw/ (git-ignored CSVs) · processed/manifest.json (data contract) · README.md (source, licence, schema)
docs/          idea, spec, plan (interface contract), tasks (backlog), security-review, decision-log, verification-log, writeup, OPERATOR_PROTOCOL
goldens/       golden evaluation pack T1–T8, built once by independent reference code and frozen by hash
skills/        SKILL_SCHEMA.md · foundational/ (6 curated skills, not used in experiment 3) · evolved/<run_id>/ (learned, immutable) · archived/ · index.json
src/           llm_provider, graph_state, claims_graph, graph_nodes, run_experiment (L0) · download_data, profile_data (A2)
               build_goldens, evaluator (A3) · skill_store, skill_validator (A4) · experiment_logger, dashboard, charts (A5)
               task_runner + analyses/ (A6) · rule_learner (experiment 2) · agent_tracker, utils (L0)
tests/         offline pytest suite (stub mode; data-dependent tests skip without data)
scripts/       bootstrap.sh, run_all.sh, verify.sh (+ Python equivalents) · summarize_run.py · archive_run.py
logs/          agent_status.json, agent_events.jsonl, experiment/graph/skill/feedback JSONL, experiment_status.json, checkpoints/
artifacts/     dashboard/progress.html · figures/ · graphs/ · tasks/<run_id>/… · manual/<run_id>/… (operator transcripts) · memory/<run_id>/<condition>.jsonl (raw-memory arms) · data_profile/ · reports/
archive/       experiments 1 and 2 and the pre-fix / smoke runs, each with a README
.claude/agents/  the builder subagents plus the two stateless operators (experiment-operator, experiment-operator-blind)
```

## Quickstart

```bash
uv sync --extra dev                      # pinned environment (Python 3.12; pandas 3, scikit-learn 1.9, langgraph 1.2)
cp .env.example .env                     # optional — defaults already select manual mode, no key needed
./scripts/bootstrap.sh                   # validate config → one-time dataset download → profile → build goldens
uv run --extra dev pytest -q             # offline tests (185)
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
4. The lead writes `config/freeze_manifest.json` (SHA-256 of tasks, rubric, goldens, raw data). `init` refuses to start a manual run if any hash drifts, and every evaluation event carries `freeze_sha256`. Experiment 3 freeze: `64b7292e8214…` (experiments 1–2: `1566c5698a50…`).

## Running the experiment (manual mode, experiment 4)

```bash
uv run python -m src.run_experiment run-stub --run-id stub_check --conditions reflection_only,feedback_memory,skill_learning,self_refine,self_refine_memory   # pipeline must pass first
uv run python -m src.run_experiment init        --run-id run_007 --conditions reflection_only,feedback_memory,skill_learning,self_refine,self_refine_memory --mode manual
uv run python -m src.run_experiment advance-all --run-id run_007      # prints the pending request per condition
#   → the lead spawns one fresh operator subagent per request (prompt template in docs/OPERATOR_PROTOCOL.md), then advance-all again
uv run python -m src.run_experiment status      --run-id run_007
uv run python scripts/summarize_run.py --run-id run_007 --json artifacts/reports/run_summaries.json
uv run python scripts/archive_run.py --run-id run_007 --folder <name>   # when a run is superseded
```

Stopping rules: pass → finalise immediately; `max_retries = 4`; the self-review arms stop when the operator says "accept"; skills proposed only for lessons reusable in ≥ 2 remaining tasks, ≤ 1 revision; the two memory arms cost no extra operator steps (recall/write are file operations); hard cap of 64 operator steps per condition; all arms always run all tasks.

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
