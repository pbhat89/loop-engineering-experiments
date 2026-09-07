# claims-skill-loop

An educational, reproducible **LangGraph** experiment in loop engineering: a claims-analysis agent plans a task from a fixed component catalogue, deterministic code executes it, a deterministic evaluator scores the output against a **frozen golden pack and rubric**, the agent reflects on the feedback, distils reusable lessons into **versioned Markdown skills**, and retrieves those skills on later tasks. Three conditions — `baseline`, `reflection_only`, `skill_learning` — run the same eight tasks so the effect of persistent skills can be compared.

## Honest framing

- **Synthetic data only.** HLT-008 synthetic healthcare claims sample (CC-BY-NC-4.0). Nothing here is medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory, or operational evidence.
- **External procedural memory, not training.** The "learning" is Markdown skill files retrieved into the planner's context; no model weights change.
- **No model API calls.** In `manual` mode the graph pauses on a LangGraph interrupt at each decision node and a fresh, **stateless Claude Code subagent** (Claude Fable 5.1) answers one JSON request (experiment 1). In `rule_learner` mode a deterministic convention learner answers instead — no LLM at all (experiment 2). `stub` mode uses trivial fixtures for tests and is always labelled non-LLM simulation. No API key, Agent SDK, headless-CLI bridge, or session-credential reuse of any kind.
- **Illustrative results.** One run per condition; comparisons are reported as illustrative, populated only from the recorded logs.

## Results so far

| Experiment | Planner | Headline (first-attempt rubric score, 0–4, T2–T8) | Where |
|---|---|---|---|
| 1 — `run_001` | stateless Claude Fable 5.1 subagents, briefs stating the conventions | Ceiling: every condition 4.00 first attempt, 0 retries, 0 feedback → 0 grounded skills (null result) | `archive/experiment-1_run_001/` |
| 2 — `run_004` | deterministic rule learner starting from textbook defaults | baseline = reflection_only **1.55** vs skill_learning **2.17**; statistical discipline 0.12 → 0.81, communication 0.23 → 2.43; 6 skills persisted, 22 reuses, 1 never reused; still one retry per task | `docs/writeup.md`, `articles/loop-engineering-markdown-skills/` |

Both are single deterministic or single-operator runs on synthetic data — illustrative, not evidence of anything operational. The article about both experiments (Substack-ready Markdown + a self-contained web version) is in `articles/loop-engineering-markdown-skills/`; read it online at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee.

## Repository layout

```text
config/        experiment.yaml, graph.yaml (A1) · tasks.yaml, rubric.yaml (A3) · freeze_manifest.json (L0, Phase 1.5)
data/          raw/ (git-ignored CSVs) · processed/manifest.json (data contract) · README.md (source, licence, schema)
docs/          idea, spec, plan (interface contract), tasks (backlog), security-review, decision-log, verification-log, writeup
goldens/       golden evaluation pack T1–T8, built once by independent reference code and frozen by hash
skills/        SKILL_SCHEMA.md · foundational/ (6 skills) · evolved/<run_id>/ (learned, immutable) · archived/ · index.json
src/           llm_provider, graph_state, claims_graph, graph_nodes, run_experiment (L0) · download_data, profile_data (A2)
               build_goldens, evaluator (A3) · skill_store, skill_validator (A4) · experiment_logger, dashboard, charts (A5)
               task_runner + analyses/ (A6) · agent_tracker, utils (L0)
tests/         offline pytest suite (stub mode; data-dependent tests skip without data)
scripts/       bootstrap.sh, run_all.sh, verify.sh (+ Python equivalents) — provided by the lead in Phase 2
logs/          agent_status.json, agent_events.jsonl, experiment/graph/skill/feedback JSONL, experiment_status.json, checkpoints/
artifacts/     dashboard/progress.html · figures/ · graphs/ · tasks/<run_id>/… · manual/<run_id>/… · data_profile/ · reports/
.claude/agents/  seven project subagent definitions (A1–A6 builders + the stateless experiment-operator)
```

## Quickstart

```bash
uv sync --extra dev                      # pinned environment (Python 3.12; pandas 3, scikit-learn 1.9, langgraph 1.2)
cp .env.example .env                     # optional — defaults already select manual mode, no key needed
./scripts/bootstrap.sh                   # validate config → one-time dataset download → profile → build goldens   (Phase 2)
uv run --extra dev pytest -q             # offline tests
./scripts/run_all.sh                     # config check → data → profile → topology → run conditions → refresh dashboard/charts → verify (Phase 2)
./scripts/verify.sh                      # tests, log validation, freeze check, security greps                    (Phase 2)
```

Python equivalents: `uv run python -m src.download_data` · `uv run python -m src.profile_data` · `uv run python -m src.build_goldens [--check]` · `uv run python -m src.run_experiment …` · `uv run python -m src.dashboard` · `uv run python -m src.charts --run-id <run_id>`. The `uv run` warning about `VIRTUAL_ENV` is harmless.

## Runtime modes

| Mode | Default | What happens | Credentials |
|---|:-:|---|---|
| `manual` | **yes** | graph pauses at each LLM-decision node; request JSON written under `artifacts/manual/`; a stateless `experiment-operator` subagent writes the response; the lead resumes | none |
| `rule_learner` | | a deterministic **convention learner** (`src/rule_learner.py`) answers every decision: textbook catalogue defaults, changed only by evaluator feedback or by a retrieved skill's `param:/list:/component:` tokens, generalised by parameter name; requires the frozen golden pack; experiment 2 | none |
| `stub` | | deterministic fixtures answer every decision; tests and pipeline demos; labelled non-LLM simulation | none |
| `anthropic_api` | | thin fail-closed adapter around `langchain-anthropic`; refuses to start without `ANTHROPIC_API_KEY`; **not used in this study** | separate Anthropic Console billing, never the Claude Code subscription |

Set with `CLAIMS_SKILL_LOOP_LLM_MODE`; see `.env.example` and `docs/plan.md` §2.

## The golden-pack step (Phase 1.5) — before any comparative run

1. `uv run python -m src.build_goldens` computes expected metrics, contracts, and checks from the downloaded data with independent pandas code (never the executor's code).
2. `uv run python -m src.build_goldens --check` reproduces them exactly.
3. **The user reviews the golden values** (checkpoint).
4. The lead writes `config/freeze_manifest.json` (SHA-256 of tasks, rubric, goldens, raw data). `init` refuses to start a manual run if any hash drifts, and every evaluation event carries `freeze_sha256`.

## Running the experiment (manual mode)

```bash
uv run python -m src.run_experiment run-stub --run-id stub_001                       # full stub run must pass first
uv run python -m src.run_experiment init    --run-id run_001 --conditions baseline,reflection_only,skill_learning
uv run python -m src.run_experiment advance --run-id run_001 --condition skill_learning   # prints the pending request path
#   → lead spawns one fresh experiment-operator subagent with that request path and the matching .response.json path
uv run python -m src.run_experiment resume  --run-id run_001 --condition skill_learning --response artifacts/manual/run_001/skill_learning/T1_a1_plan_task_1.response.json
uv run python -m src.run_experiment status  --run-id run_001
```

Stopping rules: pass → finalise immediately; `max_retries = 2`; skills proposed only for lessons reusable in ≥ 2 remaining tasks, ≤ 1 revision; hard cap of 64 operator steps per condition; all conditions always run all eight tasks.

## Running the experiment (rule-learner mode, experiment 2)

```bash
uv run python -m src.run_experiment run-auto --run-id run_005 --mode rule_learner   # three conditions, ~2 minutes, no interrupts, no LLM
uv run python scripts/summarize_run.py --run-id run_005                             # the numbers the write-up cites
uv run python -m src.charts && uv run python -m src.dashboard                       # figures + dashboard from the logs
```

Superseded runs and experiment 1 live under `archive/` with their own READMEs; the goldens, suite, rubric and freeze manifest were never changed between experiments.

## Where to look while it runs

| What | Where |
|---|---|
| Build tracker + live experiment status (auto-refreshing static HTML) | `artifacts/dashboard/progress.html` |
| Machine-readable status (current task/node, pending request, steps vs cap, rough ETA) | `logs/experiment_status.json`, `logs/agent_status.json` |
| Learning curve, reliability curve, rubric heatmap, skill accumulation, skill utility | `artifacts/figures/` |
| LangGraph topology (designed workflow) and observed skill-lifecycle graph (from logs) | `artifacts/graphs/` |
| Per-attempt task outputs (metrics.json, report.md, charts) | `artifacts/tasks/<run_id>/<condition>/<task_id>/attempt_<n>/` |
| Learned skills | `skills/evolved/<run_id>/` |
| Write-up material | `docs/writeup.md`, `artifacts/reports/` |

## Documentation

`docs/idea.md` (why) · `docs/spec.md` (what, acceptance criteria, stopping rules) · `docs/plan.md` (interface contract every module codes against) · `docs/tasks.md` (weighted backlog driving the dashboard) · `docs/security-review.md` · `docs/decision-log.md` · `docs/verification-log.md` (only checks actually run) · `docs/writeup.md`.

## Licence and attribution

- Code: MIT (see `pyproject.toml`).
- Data: **HLT-008 Synthetic Healthcare Claims Dataset — sample**, `xpertsystems/hlt008-sample` on Hugging Face, revision `7309ddb30e67468748b7aa9182d8517fe28c2f9c`, licensed **CC BY-NC 4.0**. Used for non-commercial educational purposes; raw files are not redistributed in this repository. Full details in `data/README.md`.
