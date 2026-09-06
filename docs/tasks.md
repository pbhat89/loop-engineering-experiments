# Tasks — dependency-aware backlog

**Owner:** A1. **Date:** 2026-09-06. Work units are the weights the tracker uses for overall completion and the rough ETA (`uv run python -m src.agent_tracker show`). Per-owner totals here **must equal** the tracker's registered totals: **L0 12 · A1 8 · A2 5 · A3 10 · A4 7 · A5 8 · A6 8 = 58**. Agents call `complete-unit --agent <id> --artifact <path>` once per finished, verified unit; the lead marks `done` at acceptance.

Phases: **0** initialise · **1** SDD + data foundation · **1.5** golden pack freeze (user checkpoint) · **2** LangGraph + infrastructure · **3** execution + evaluation + tests · **4** comparative runs + observability · **5** review + ship. Statuses: `todo`, `in_progress`, `review`, `done`, `blocked`. Every verification command runs from the repo root; tests use `uv run --extra dev pytest …`.

## L0 — lead (12 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| L0-1 | 0 | done | 1 | Scaffold: `pyproject.toml` (uv, pinned ranges, `uv.lock`), `.env.example`, `.gitignore`, directory tree, `src/utils.py` | `uv sync --extra dev && uv run python -c "import src.utils"` | — |
| L0-2 | 0 | done | 1 | `src/agent_tracker.py` + `src/dashboard.py` v1; A1–A6 registered with unit totals | `uv run python -m src.agent_tracker show` | L0-1 |
| L0-3 | 0 | done | 1 | Seven `.claude/agents/*.md` definitions + `docs/LEAD_DESIGN_DECISIONS.md` | files exist; contract §1–§15 present | L0-1 |
| L0-4 | 2 | todo | 1.5 | `src/llm_provider.py`: `OperatorRequest`, `PlanResponse`/`ReflectionResponse`/`SkillProposalResponse`, `ManualProvider` (interrupt), `FixtureProvider`, fail-closed `AnthropicProvider`, `get_provider()`; `tests/test_llm_provider.py` | `uv run --extra dev pytest tests/test_llm_provider.py -q` | A1-2 |
| L0-5 | 2 | todo | 2 | `src/graph_state.py` (all fields, plan §4) + `src/claims_graph.py` (`build_claims_skill_graph(condition)`, four routers, `SqliteSaver`); `tests/test_graph_routes.py` incl. `config/graph.yaml` mirror assertion | `uv run --extra dev pytest tests/test_graph_routes.py -q` | A1-6, L0-4 |
| L0-6 | 2 | todo | 1.5 | `src/graph_nodes.py`: twelve nodes, re-execution-safe interrupts, validation re-request (≤ 2), operator cap rule, logging hooks | stub end-to-end case in `tests/test_graph_routes.py` passes | L0-4, A4-2, A5-1 |
| L0-7 | 2 | todo | 1 | `src/run_experiment.py` (`init`, `advance`, `resume`, `status`, `run-stub`; freeze check; request/response files; status + dashboard refresh) + `scripts/bootstrap.sh`, `run_all.sh`, `verify.sh` and Python equivalents | `uv run python -m src.run_experiment --help && bash scripts/verify.sh` | L0-5, L0-6 |
| L0-8 | 1.5 | todo | 1 | Golden pack freeze: `build_goldens --check` clean; **user reviews golden values (checkpoint G3)**; `config/freeze_manifest.json` written; files committed | `uv run python -m src.build_goldens --check`; freeze verification passes in `init` | A3-5 |
| L0-9 | 3 | todo | 0.5 | Stub end-to-end gate (G5): `run-stub` completes 3 conditions × 8 tasks without interrupts; `validate_logs()` clean; dashboard + seven figures render | `uv run python -m src.run_experiment run-stub --run-id stub_001 && bash scripts/verify.sh` | L0-7, L0-8, A3-7, A4-5, A5-7, A6-6 |
| L0-10 | 4 | todo | 1 | Manual runs (G6): `run_001`, three conditions, one stateless `experiment-operator` subagent per request; cap and stopping rules observed; `experiment_status.json` + dashboard live throughout | `uv run python -m src.run_experiment status --run-id run_001` shows 8/8 tasks per condition | L0-9 |
| L0-11 | 5 | todo | 0.5 | Consolidate `docs/verification-log.md` from `docs/verification/*.md`; `verify.sh` green or failures documented; security sign-off; `gates --passed` only when all spec §10 gates hold; final handoff report | `bash scripts/verify.sh`; `uv run python -m src.agent_tracker show` | L0-10, A1-8 |

## A1 — SDD architect (8 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| A1-1 | 1 | done | 1 | `docs/idea.md` + `docs/spec.md` (research question, hypotheses, conditions, acceptance criteria, validated-useful-skill definition, stopping rules, limitations) | files exist; spec §10 lists all 13 brief gates + golden + manual gates | L0-3 |
| A1-2 | 1 | done | 1 | `docs/plan.md` interface contract (state, nodes, routes, routers, operator protocol, all data shapes, event schemas, config, tests, security) | shapes match `LEAD_DESIGN_DECISIONS.md` §1–§15 | A1-1 |
| A1-3 | 1 | done | 1 | `docs/tasks.md` with per-owner totals equal to the tracker | unit sums: L0 12, A1 8, A2 5, A3 10, A4 7, A5 8, A6 8 | A1-2 |
| A1-4 | 1 | done | 1 | `docs/security-review.md` (brief list + credential boundary, JSON-only operator IO, injection hygiene, executor confinement, timeouts, no network, PHI, licence) | every item names its mechanism, owner, and Phase 5 check | A1-2 |
| A1-5 | 1 | done | 1 | `docs/decision-log.md` (dataset, six skills, LangGraph + interrupts + SQLite, runtime boundary, golden pack, deterministic evaluator, run-scoped skills, roster, stopping rules, uv stack) | each entry has alternatives, rationale, impact | A1-2 |
| A1-6 | 1 | done | 1 | `config/experiment.yaml` (exactly LEAD §12 keys) + `config/graph.yaml` (nodes, per-condition edges, routers, termination) | `uv run python -c "import yaml;[yaml.safe_load(open(p)) for p in ['config/experiment.yaml','config/graph.yaml']];print('yaml ok')"` | A1-2 |
| A1-7 | 1 | done | 1 | `README.md` (framing, layout, quickstart, modes, golden step, licence) + `docs/writeup.md` outline + `docs/verification-log.md` skeleton | files exist; README quickstart matches plan §9 | A1-6 |
| A1-8 | 1 | done | 1 | Consistency pass: no stale runtime terms in A1 docs; YAML parses; `docs/verification/A1-sdd-architect.md` written; `review` recorded | grep for stale terms returns only intentional historical/prohibition mentions | A1-7 |

## A2 — data steward (5 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| A2-1 | 1 | todo | 1 | Licence/metadata inspected and recorded; `src/download_data.py` downloads the five CSVs individually at revision `7309ddb3…`, verifies SHA-256, exposes `load_manifest()`; the only network use in the repo | `uv run python -m src.download_data && ls data/raw` | L0-1 |
| A2-2 | 1 | todo | 1 | `src/profile_data.py`: per-file rows, dtypes, missingness, duplicates, candidate keys, date ranges, cross-file relationship checks; `load_table(name)` | `uv run python -m src.profile_data` | A2-1 |
| A2-3 | 1 | todo | 1 | `data/processed/manifest.json` in plan §10 shape; `sample_values` ≤ 50 chars; relationships with unmatched counts + denominators | `uv run python -c "import json;m=json.load(open('data/processed/manifest.json'));print(sorted(m['tables']))"` | A2-2 |
| A2-4 | 1 | todo | 1 | `data/README.md` (source, retrieval date, licence + attribution, expected vs received files, sizes, rows, schema, limitations, revision) + `artifacts/data_profile/` JSON and Markdown | files exist and cite the revision SHA | A2-3 |
| A2-5 | 1 | todo | 1 | `tests/test_data_contract.py` (skips with reason when `data/raw` is empty; fails loudly on drift) | `uv run --extra dev pytest tests/test_data_contract.py -q` | A2-3 |

## A3 — evaluation engineer (10 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| A3-1 | 1 | todo | 1.5 | `config/tasks.yaml` T1–T4: objectives (no golden hints), tags, input tables, golden file, required artifacts, component catalogue with `params/options/default/default_selected/produces` | `uv run python -c "import yaml;yaml.safe_load(open('config/tasks.yaml'))"` | A2-3, A1-2 |
| A3-2 | 1 | todo | 1.5 | `config/tasks.yaml` T5–T8: leakage exclusion lists, split/threshold options, small-group thresholds, caveat sets, brief structure components | same; every task has ≥ 3 genuinely different choices | A3-1 |
| A3-3 | 1 | todo | 1.5 | `config/rubric.yaml`: `rubric_version`, `pass_threshold: 3.5`, five dimensions, per-task checks (`check_id, dimension, weight, critical, kind, target, related_components, remediation, reusable, applicable_task_ids`) | yaml parses; every check target key appears in some `produces` (script in verification notes) | A3-2 |
| A3-4 | 1.5 | todo | 1.5 | `src/build_goldens.py` (pandas + manifest only; deterministic; `--check`) + goldens T1–T5 | `uv run python -m src.build_goldens && uv run python -m src.build_goldens --check` | A2-3, A3-2 |
| A3-5 | 1.5 | todo | 1 | Goldens T6/T7 contracts (split, prohibited fields, metric ranges, train-percentile threshold) + `T8_executive_brief_rubric.yaml`; list of golden values for the user's review | `uv run python -m src.build_goldens --check` | A3-4 |
| A3-6 | 3 | todo | 2 | `src/evaluator.py`: all eight check kinds, scoring formula, critical logic, `observed: null` on missing metrics, structured feedback with `related_components` | `uv run --extra dev pytest tests/test_evaluator.py -q` | A3-3, A3-5 |
| A3-7 | 3 | todo | 1 | `tests/test_evaluator.py` (fixtures for each kind; data-dependent cases skip without data) | same | A3-6 |

## A4 — skill-system engineer (7 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| A4-1 | 2 | todo | 1.5 | `skills/SKILL_SCHEMA.md` (brief schema + `tags`) and the six foundational skills with concrete procedures and generic examples | `uv run python -c "from src.skill_store import SkillStore;print(len(SkillStore('skills').list_skills()))"` prints 6 | A1-2 |
| A4-2 | 2 | todo | 1.5 | `src/skill_store.py`: parse, `list_skills`, deterministic `retrieve` (scoring + eligibility by task index and run), `render_for_operator` | `uv run --extra dev pytest tests/test_skill_store.py -q -k retriev` | A4-1 |
| A4-3 | 2 | todo | 1 | `src/skill_store.py`: `persist` (run-scoped immutable files, `evolved_<run_id>_<nnn>`), `skills/index.json`, `record_reuse`, `archive` | `uv run --extra dev pytest tests/test_skill_store.py -q -k persist` | A4-2 |
| A4-4 | 2 | todo | 2 | `src/skill_validator.py`: schema, safety, generality, provenance, applicability (≥ 2 remaining), duplicate (Jaccard ≥ 0.6), `retry_revision` once | `uv run --extra dev pytest tests/test_skill_store.py -q -k validat` | A4-2 |
| A4-5 | 2 | todo | 1 | `tests/test_skill_store.py` complete (six skills validate; determinism; immutability; thresholds) | `uv run --extra dev pytest tests/test_skill_store.py -q` | A4-3, A4-4 |

## A5 — observability engineer (8 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| A5-1 | 2 | todo | 1.5 | `src/experiment_logger.py`: typed writers/readers for the four JSONL logs (plan §17) + `validate_logs()` with `file:line` diagnostics | `uv run --extra dev pytest tests/test_logging.py -q -k log` | A1-2 |
| A5-2 | 2 | todo | 1 | `update_status(...)` → atomic `logs/experiment_status.json` with per-condition ETA rules | `uv run --extra dev pytest tests/test_logging.py -q -k status` | A5-1 |
| A5-3 | 2 | todo | 1.5 | `src/dashboard.py` v2: per-condition progress, pending operator steps + waiting-since, score grid, retries/errors, skill counts, embedded figures; graceful when empty | `uv run python -m src.dashboard` writes `artifacts/dashboard/progress.html` | A5-2 |
| A5-4 | 4 | todo | 1 | `src/charts.py`: learning curve, reliability curve, rubric heatmap (from logs only; missing shown as missing) | `uv run python -m src.charts --run-id stub_001` | A5-1 |
| A5-5 | 4 | todo | 1 | `src/charts.py`: skill accumulation, skill utility (reuse + illustrative deltas), observed lifecycle graph (`artifacts/graphs/skill_lifecycle_graph.html`) | same | A5-1 |
| A5-6 | 2 | todo | 0.5 | `charts.render_topology()` → `artifacts/graphs/langgraph_topology.png` labelled "designed workflow" | file exists after `uv run python -c "from src.charts import render_topology;render_topology()"` | L0-5 |
| A5-7 | 3 | todo | 1.5 | `tests/test_logging.py` + `tests/test_dashboard.py` (schemas, validator, ETA rules, empty/populated render, no 100 % before gates) | `uv run --extra dev pytest tests/test_logging.py tests/test_dashboard.py -q` | A5-3, A5-5 |

## A6 — analysis engineer (8 units)

| ID | Phase | Status | Units | Definition of done | Verification | Depends on |
|---|:-:|---|--:|---|---|---|
| A6-1 | 3 | todo | 1.5 | `src/task_runner.py`: plan validation against catalogue + manifest (structured errors, never raises), dispatch, `metrics.json`/`report.md` writers, result shape (plan §13), cooperative timeout, `output_dir` confinement | `uv run --extra dev pytest tests/test_task_runner.py -q -k runner` | A3-2, A2-3 |
| A6-2 | 3 | todo | 1.5 | `src/analyses/t1_recon.py`, `t2_portfolio.py` (all catalogue components and options) | `uv run --extra dev pytest tests/test_task_runner.py -q -k "t1 or t2"` | A6-1 |
| A6-3 | 3 | todo | 1.5 | `t3_provider_network.py`, `t4_denials.py` (group sizes, small-group flags, denial-code ranking, missing-code quantification) | `… -k "t3 or t4"` | A6-1 |
| A6-4 | 3 | todo | 1.5 | `t5_fraud_exploration.py`, `t6_fraud_model.py` (stratified split, train-only preprocessing, exclusions, LR + tree model, metrics JSON) | `… -k "t5 or t6"` | A6-1 |
| A6-5 | 3 | todo | 1 | `t7_high_cost.py` (train-percentile threshold, ranking metrics), `t8_brief.py` (metric-backed Markdown brief with caveats and artifact references) | `… -k "t7 or t8"` | A6-1 |
| A6-6 | 3 | todo | 1 | `tests/test_task_runner.py` (determinism, error shapes, confinement, no network, leakage exclusions) | `uv run --extra dev pytest tests/test_task_runner.py -q` | A6-5 |

## Gates (no work units; recorded in `docs/verification-log.md`)

| Gate | What must be true | Evidence | Blocks |
|---|---|---|---|
| G1 SDD accepted | lead reviews A1-1…A1-8; deviations resolved or logged | `agent_tracker done --agent A1` | nothing (A2–A6 may start on the draft) |
| G2 data contract | manifest exists; `test_data_contract` passes | A2-5 | A3-1, A6-1 |
| G3 golden review (**user checkpoint**) | user has seen and approved the golden values list | note in verification log with date | L0-8 freeze |
| G4 freeze | `config/freeze_manifest.json` committed; `init` verifies hashes | L0-8 | any comparative run |
| G5 stub end-to-end | `run-stub` completes; logs validate; dashboard + figures render | L0-9 | L0-10 |
| G6 manual runs complete | 3 × 8 tasks finalised; cap events (if any) logged | L0-10 | write-up |
| G7 acceptance | all spec §10 gates hold; `gates --passed` set | L0-11 | declaring completion |

## Critical path and parallelism

`A2-1 → A2-3 → A3-1 → A3-2 → A3-3 → A3-4 → A3-5 → L0-8 (G3, G4) → L0-9 (G5) → L0-10 (G6) → L0-11 (G7)`.
In parallel: A1 (now), A4 and A5 (no data needed), L0-4 → L0-7 (against plan §2–§9), A6 once A3-2 lands. At most five agents run concurrently; no two agents edit the same file.

## Unit totals (must match the tracker)

| Owner | Units here | Tracker |
|---|--:|--:|
| L0 | 12 | 12 |
| A1 | 8 | 8 |
| A2 | 5 | 5 |
| A3 | 10 | 10 |
| A4 | 7 | 7 |
| A5 | 8 | 8 |
| A6 | 8 | 8 |
| **Total** | **58** | **58** |
