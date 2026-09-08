# Verification log — claims-skill-loop

**Rules.** Append-only. Every entry names the date, who ran it, the exact command, and the observed result. **Never state that a check passed unless it was run.** Per-agent notes live in `docs/verification/<agent>.md`; L0 consolidates them here at each phase boundary. Unchecked boxes are work not yet verified.

---

## Phase 0 — initialise (L0)

- [ ] `uv sync --extra dev` on a clean checkout (L0 to append with output summary)
- [ ] Tracker registration and dashboard v1 render (L0 to append)

## Phase 1 — SDD and data foundation

### 2026-09-06 · A1 · agent tracker totals

- Command: `uv run python -m src.agent_tracker show`
- Result: registered unit totals L0 12 · A1 8 · A2 5 · A3 10 · A4 7 · A5 8 · A6 8 (58). **Passed.**

### 2026-09-06 · A1 · `docs/tasks.md` unit sums equal the tracker

- Command: Python snippet (recorded in `docs/verification/A1-sdd-architect.md`) summing the `Units` column per owner and comparing with `logs/agent_status.json`.
- Result: all seven owners match; 49 task rows; 58 units. **Passed.**

### 2026-09-06 · A1 · configuration files parse and mirror LEAD §12

- Command: `uv run python -c "import yaml;[yaml.safe_load(open(p)) for p in ['config/experiment.yaml','config/graph.yaml']];print('yaml ok')"`
- Result: `yaml ok`. **Passed.**
- Structural check (Python snippet in A1 notes): `experiment.yaml` key list equals LEAD §12 exactly; `dataset` keys are `repo, revision, files`; `conditions` equal the condition set in `graph.yaml`. **Passed.**
- Per-condition edge consistency of `graph.yaml` (same snippet, rerun with UTF-8 stdout): for `baseline` (6 nodes, 6 static edges), `reflection_only` (7, 7), `skill_learning` (12, 9) every edge endpoint is a declared node or `__start__`/`__end__`, every conditional target is a declared node, every router label is declared, every node is entered by some edge and has an exit; `termination.max_retries` and `max_operator_steps_per_condition` equal `experiment.yaml`; `llm_decision_nodes ⊆ nodes`; `skill_learning` uses all 12 nodes. **Passed.** (Equality with the compiled graph is asserted only once `tests/test_graph_routes.py` exists — Phase 2.)

### 2026-09-06 · A1 · stale runtime terminology

- Command: `grep -n -E "manual_or_stub|default anthropic_api|Agent SDK|headless"` over `README.md`, `docs/{idea,spec,plan,tasks,security-review,decision-log,writeup}.md`, `config/experiment.yaml`, `config/graph.yaml`.
- Result: 7 matches, all either prohibition statements ("no Agent SDK, no headless-CLI bridge") or the decision log's historical record of the superseded mode name (D-04). No stale usage in A1-owned files. **Passed.**
- Outside A1 ownership (reported, not edited): `.env.example` lines 6 and 8 and `src/dashboard.py:231` still use the superseded mode name `manual_or_stub`; L0/A5 to update to `manual` / `stub`.

### Data foundation (A2) — to be appended

- [ ] Dataset metadata and licence inspected; five files downloaded at the pinned revision; SHA-256 recorded
- [ ] `uv run python -m src.profile_data` output; manifest shape; `sample_values ≤ 50` chars
- [ ] `uv run --extra dev pytest tests/test_data_contract.py -q`

## Phase 1.5 — golden evaluation pack freeze

- [ ] `uv run python -m src.build_goldens` then `--check` reproduces the committed files (A3)
- [ ] **User review of golden values** — date, what was reviewed, outcome (L0; gate G3)
- [ ] `config/freeze_manifest.json` written; `freeze_sha256` recorded here (L0; gate G4)
- [ ] `init` in manual mode refuses a deliberately modified golden (L0)

## Phase 2 — LangGraph and infrastructure

- [ ] `uv run --extra dev pytest tests/test_llm_provider.py -q` (fail-closed live mode; default `manual`)
- [ ] `uv run --extra dev pytest tests/test_graph_routes.py -q` (compiles per condition; `graph.yaml` mirror; routers)
- [ ] `uv run --extra dev pytest tests/test_skill_store.py -q` (six foundational skills validate)
- [ ] `uv run --extra dev pytest tests/test_logging.py tests/test_dashboard.py -q`
- [ ] Topology rendered to `artifacts/graphs/langgraph_topology.png`

## Phase 3 — execution, evaluation, tests

- [ ] `uv run --extra dev pytest tests/test_evaluator.py -q`
- [ ] `uv run --extra dev pytest tests/test_task_runner.py -q`
- [ ] `uv run --extra dev pytest -q` (whole suite) — failures documented verbatim if any
- [ ] Stub end-to-end: `uv run python -m src.run_experiment run-stub --run-id stub_001` (gate G5); `validate_logs()` clean; dashboard + figures render

## Phase 4 — comparative runs

- [ ] `run_001` `init` (freeze verified) and per-condition `advance`/`resume` cycles; operator steps used vs cap per condition; any `operator_cap` events
- [ ] `logs/experiment_status.json` observed updating during the run; dashboard auto-refresh confirmed
- [ ] Charts regenerated from logs; each figure names its source logs and run ids

## Phase 5 — review and ship

- [ ] `bash scripts/verify.sh` (tests, log validation, freeze check, security greps from `docs/security-review.md` §5)
- [ ] Every chart cross-checked against its source log (A5/L0)
- [ ] Security review items S1–S16 verified or documented as not verified
- [ ] `uv run python -m src.agent_tracker gates --passed` only after all `docs/spec.md` §10 gates hold

---

## Limitations

### 2026-09-06 · Build session — project agent types not loaded

The project-level `.claude/agents` subagent types were **not loaded** in the build session. A1–A6 therefore ran as general-purpose agents that read their definition files (`.claude/agents/<name>.md`) and adopted them as operating instructions, restricting themselves to the tools listed there. The `experiment-operator` role in manual runs is likewise performed by general-purpose subagents given the operator definition and exactly one request/response path pair. File ownership, tool discipline, and lifecycle tracking were preserved by instruction rather than enforced by the harness; the lead's review is the check on that.

### 2026-09-06 · Study design (from `docs/spec.md` §14)

One run per condition (illustrative comparisons); one operator model; catalogue-bounded analysis choices; `skill_learning` bundles foundational access with evolved-skill accumulation; deterministic structural checks for prose; synthetic data only.

---

## L0 consolidation · 2026-09-07 · Phases 0–3, 1.5 and the manual run to date

All results below were observed by the lead in the build session (agent-reported counts are marked as such and were re-run inside the full suite).

### Phase 0 — initialise
- 2026-09-06 · `uv sync --extra dev --extra anthropic` → environment created; `imports OK | pandas 3.0.5 | sklearn 1.9.0`; langgraph 1.2.11, langgraph-checkpoint-sqlite 3.1.1 added later the same day. **Passed.**
- 2026-09-06 · tracker registered L0 + A1–A6 (58 weighted units); `artifacts/dashboard/progress.html` rendered by `src/agent_tracker.py` after every status change and opened in the user's browser. **Passed.**
- Limitation: project-level `.claude/agents` types were not loaded in the session; A1–A6 and every operator step ran as general-purpose agents adopting the definition files. The night of 2026-09-06 all four running agents were terminated by the Claude session rate limit; they were relaunched staggered on 2026-09-07.

### Phase 1 — data foundation
- 2026-09-06 · A2 · `uv run --extra dev pytest tests/test_data_contract.py -q` → 54 passed (A2 report; included in the lead's full-suite run below). Manifest at `data/processed/manifest.json`, profile under `artifacts/data_profile/`, five CSVs at revision `7309ddb3…` with SHA-256 recorded. **Passed.**

### Phase 1.5 — golden pack freeze
- 2026-09-07 · L0 · `uv run python -m src.build_goldens` → 8 golden files + `artifacts/reports/golden_review.md` (52 values, 0 sanity failures); `--check` → `golden pack check clean: 8 files match the recomputation (built_at ignored)`. **Passed.**
- 2026-09-07 · **User review**: golden values presented (denial rate 0.104222 = 1286/12339; fraud prevalence 0.050370; T7 threshold 3198.99 train-only vs 3161.93 all-data; 36 months of 302–405 claims). User answer: *Approve and freeze*; conditions: the brief's three; one run per condition. **Gate G3 passed.**
- 2026-09-07 · L0 · `uv run python -m src.run_experiment freeze` → `frozen 15 files -> config/freeze_manifest.json | freeze_sha256 1566c5698a50ba82e2df5e94e6da37b5fa738e53281f19283f3f9431334566ab`. **Gate G4 passed.**
- 2026-09-07 · L0 · drift gate: appended one byte to `goldens/T1_data_contract.json`, ran `init --run-id drift_check --mode manual` — see the result line appended directly below this section (recorded from the actual command); file restored byte-identical from backup and `verify_freeze()` re-checked.

### Phase 2 — LangGraph and infrastructure
- 2026-09-07 · L0 · `uv run --extra dev pytest tests/test_llm_provider.py tests/test_graph_routes.py tests/test_run_experiment.py -q` → 22 passed (default mode `manual`; `anthropic_api` fails closed without a key; per-condition routes incl. `foundational_only`; manual interrupt → invalid response re-request → resume; operator cap; `graph.yaml` mirrors `designed_topology()`; runner pause/response/resume across runner instances). **Passed.**
- 2026-09-07 · A4 · `tests/test_skill_store.py` → 26 passed (A4 report). A5 · `tests/test_logging.py` + `tests/test_dashboard.py` → 17 passed (A5 report). Topology rendered to `artifacts/graphs/langgraph_topology.png` (lead ran `render_topology(designed_topology())` → 97,857 B; A5's regeneration → 101,500 B). **Passed.**

### Phase 3 — execution, evaluation, tests
- 2026-09-07 · A3 · `tests/test_evaluator.py` → 24 passed; A6 · `tests/test_task_runner.py` → 22 passed in 68.44 s (agent reports).
- 2026-09-07 · L0 · `uv run --extra dev pytest -q` (whole suite, before freeze) → **165 passed**. Re-run after D-16/test fix: `tests/test_run_experiment.py` 4 passed. **Passed.**
- 2026-09-07 · L0 · `uv run python -m src.run_experiment run-stub --run-id stub_001` → baseline/reflection_only/skill_learning done, 3 × 8 tasks in 2 m 09 s; final scores 4.00 everywhere after one feedback-driven revision per task; first-attempt means baseline 1.62 · reflection_only 1.57 · skill_learning 1.61; 5 evolved skills persisted under `skills/evolved/stub_001/`; `validate_logs()` → 0 problems; operator steps 16 / 24 / 38 of 40 (→ D-15 raised the cap to 64). **Gate G5 passed — deterministic simulation, not an LLM result.**

### Phase 4 — manual comparative run `run_001` (in progress at the time of writing)
- 2026-09-07 · L0 · `init --run-id run_001 --conditions baseline,reflection_only,skill_learning --mode manual` → freeze verified (`1566c569…`). Operator loop per `docs/OPERATOR_PROTOCOL.md`: one fresh general-purpose subagent per request file; the lead never read or edited operator files during the run.
- baseline: **done 8/8**, every task 4.00 on the first attempt, 8 operator steps, 0 retries, 0 `operator_cap` events.
- reflection_only: **done 8/8**, identical (the reflection node only runs on a retry and none occurred).
- skill_learning: 7/8 at 19 steps when this entry was written, all first-attempt passes; proposals T1–T5 rejected by `skill_validator` (empty `source_feedback_ids`; T1/T2 also an ungrounded "guarantee" claim); T6/T7 reflections returned no lessons so the proposal step was skipped; 0 evolved skills persisted. Protocol change D-16 (task titles in requests) applied after T1 in every condition.
- `logs/experiment_status.json` and the dashboard updated after every node; figures regenerated after each completed task via `Runner._refresh_figures`.
- Drift gate result (actual output): freeze check failed - comparative runs need a frozen golden pack:   changed or added: goldens/T1_data_contract.json 
- Post-restore check: freeze intact 1566c5698a50

### 2026-09-06T23:50:03+00:00 — `scripts/pipeline.py verify` (103s, 0 failure(s))
- PASS — required file README.md
- PASS — required file pyproject.toml
- PASS — required file .env.example
- PASS — required file config/experiment.yaml
- PASS — required file config/tasks.yaml
- PASS — required file config/rubric.yaml
- PASS — required file config/graph.yaml
- PASS — required file data/README.md
- PASS — required file data/processed/manifest.json
- PASS — required file skills/SKILL_SCHEMA.md
- PASS — required file docs/spec.md
- PASS — required file docs/plan.md
- PASS — required file docs/tasks.md
- PASS — required file docs/security-review.md
- PASS — required file docs/decision-log.md
- PASS — required file docs/writeup.md
- PASS — required file artifacts/dashboard/progress.html
- PASS — six foundational skills present — 01_data_contract.md, 02_safe_claims_joins.md, 03_descriptive_summary.md, 04_categorical_numeric_analysis.md, 05_reproducible_python_analysis.md, 06_evaluation_and_charting.md
- PASS — golden pack reproduces from data (build_goldens --check) — golden pack check clean: 8 files match the recomputation (built_at ignored)
- PASS — freeze manifest matches data/goldens/tasks/rubric — 1566c5698a50
- PASS — JSONL logs valid
- PASS — agent tracker maintained — 7 agents, gates passed=False
- PASS — LangGraph compiles and matches designed topology
- PASS — pytest -q — .....................                                                    [100%]

## L0 · 2026-09-07 · Phase 4 complete and Phase 5 checks

### Manual run `run_001` — final
- `uv run python -m src.run_experiment status --run-id run_001` → baseline done 8/8 (8 steps), reflection_only done 8/8 (8 steps), skill_learning done 8/8 (21 steps); every task 4.00; retries 0; `operator_cap` events 0; operator validation errors 0. 37 request/response pairs under `artifacts/manual/run_001/` (24 plan, 8 reflect, 5 propose). **Run complete.**
- `uv run python scripts/summarize_run.py --run-id run_001 --run-id stub_001 --json artifacts/reports/run_summaries.json` → numbers used in `docs/writeup.md` (skill_learning: 47 retrievals, 27 citations, 5 proposals all rejected on provenance — T1/T2 also generality — 3 skipped, 0 persisted).
- `validate_logs()` on the real `logs/` → 0 problems.

### Figures cross-checked against source logs (lead, by inspection of the PNGs)
- `learning_curve.png`: all six run/condition series flat at 4.00; run_001 markers filled (first-attempt pass), stub_001 hollow (retry) — matches `experiment_events.jsonl`. **Consistent.**
- `reliability_curve.png`: execution errors 0 for every series ("every observed count is 0"); retries = 1 per task for stub_001 only — matches. **Consistent.**
- `skill_lifecycle_graph.png`: five stub_001 evolved skills with source feedback and later retrieval/reuse edges; no run_001 evolved skills (none persisted) — matches `skill_events.jsonl`. **Consistent.**
- `rubric_heatmap.png`: 4.00 in every cell for both runs; `foundational_only` shown as "no observations". **Consistent.**
- `langgraph_topology.png` is labelled as the designed workflow. Charts were regenerated by `uv run python -m src.charts` after the run.

### Phase 5
- `uv run python scripts/pipeline.py verify` → 24 PASS / 0 FAIL (required files, six foundational skills, `build_goldens --check` clean, freeze manifest matches `1566c5698a50`, JSONL logs valid, tracker maintained, LangGraph compiles and matches designed topology, `pytest -q` passed). Full outcome list appended automatically above.
- `docs/writeup.md` populated from logs/artifacts only; states synthetic data, illustrative single run, no API calls, operator = Claude Code subagents, and the ceiling-effect null result.
- Security review items: no secrets in repo (`.env` ignored; no key ever set); operator files are JSON only; executor has no `eval`/`exec`/shell/network (A6 note); network used once for the pinned download (A2 note); dataset attribution in `data/README.md`.

## L0 · 2026-09-07 · Experiment 2 — rule learner (`rule_learner` mode), reported run `run_004`

- Repo reset: experiment 1 moved to `archive/experiment-1_run_001/` with git history (`git mv`, 454 paths). Goldens, suite, rubric, freeze manifest untouched (`verify_freeze()` → intact `1566c569…`).
- New code: `src/rule_learner.py` (+ `rule_learner` mode in `src/llm_provider.py`, `run-auto` in `src/run_experiment.py`, `remaining_tasks`/`plan_history`/existing-skill `required_checks` in operator payloads). Tests: `tests/test_rule_learner.py` 7 passed; `tests/test_evaluator_caveat_scope.py` 4 passed; core suites re-run green (50 tests in the last combined run).
- Fairness bug found and fixed (D-19): `run_002` showed baseline > reflection_only on T7's first attempt with identical plans; cause = caveat keyword "baseline" matched the condition name in the report (paths, then the Summary line). `EVALUATOR_VERSION` 1.0 → 1.1 scopes caveat matching to caveat/limitation sections and strips run ids, condition names, paths and citations. Learner v1.1 learns list removals only from exclusion-type feedback. `run_002` and `run_003` archived under `archive/experiment-2_run_00{2,3}_pre-fix/`; rubric/goldens/freeze unchanged.
- `uv run python -m src.run_experiment run-auto --run-id run_004 --mode rule_learner` → three conditions × eight tasks in about two minutes; freeze verified at init; every evaluation event `evaluator_version 1.1`; `validate_logs()` → 0 problems.
- Results (`scripts/summarize_run.py --run-id run_004`, `artifacts/reports/run_summaries.json`): final scores 4.00 everywhere after one revision per task (8 retries per condition, 0 execution errors). **First-attempt mean: baseline 1.53 = reflection_only 1.53 (identical plans, as required) vs skill_learning 2.07; T2–T8: 1.55 vs 2.17.** By dimension (T2–T8): statistical discipline 0.12 → 0.81, communication 0.23 → 2.43, completeness 1.49 → 1.65, correctness 2.47 → 2.47, reproducibility 3.45 → 3.45. Operator steps 16 / 24 / 38 of 64. Skills: 6 proposed, 6 accepted and persisted (`skills/evolved/run_004/`), 61 retrievals, 22 reuse events; reuse counts 7 / 5 / 5 / 0 / 3 / 2 — `evolved_run_004_004` (T4 denial segments) never reused (bloat candidate). No first-attempt pass in any condition: task-specific scope is not a convention.
- Figures regenerated: `uv run python -m src.charts` (6 figures + topology), `uv run python -m src.dashboard`; article figures from the same logs via `articles/loop-engineering-markdown-skills/assets/make_figures.py`.

- 2026-09-07 · L0 · Article written with the pb-writer skill (`D:/Projects/writer/skills/pb-writer`) from `docs/writeup.md` and the logs: `articles/loop-engineering-markdown-skills/article.md`, figures regenerated by `assets/make_figures.py`, web build `build_html.py` → `article.html`; published as a private artifact at https://claude.ai/code/artifact/541293ef-bde3-4a40-95ff-11449a825aee and linked from the article, the write-up and the README.

## L0 · 2026-09-07 · Experiment 3 — blinded four-task suite, Haiku operator, capped feedback, `self_refine` arm (reported run `run_005`)

- Repo reset: `run_004` moved to `archive/experiment-2_run_004/` with `scripts/archive_run.py` (72 / 105 / 246 / 446 JSONL lines, run manifest, checkpoint, task artifacts, 6 evolved skills + index entries, figures, write-up v2 copied as `docs/writeup_run_004.md`, article v1 + assets). Skill index empty afterwards.
- Code: graph v3 (`self_evaluate` node, `route_after_self_evaluation`, `self_refine` condition), feedback cap (`select_feedback`, `operator_feedback_view`, `evaluation_summary` itemising only the shown checks), `SkillStore(include_foundational=False)`, new experiment record fields, evaluator 1.2 (condition-name strip only), fixture rule for `self_evaluate`, `experiment-operator-blind.md`. Tests: `uv run --extra dev pytest -q` → **108 passed** (4 new: self_refine routing with fixture, manual self_refine requests carry no evaluator information, feedback cap/hidden fixes, capped feedback through reflect/revise).
- Golden pack: briefs of T2/T3/T4/T7 blinded in `config/tasks.yaml`; T7 `models.*.roc_auc` range → `[0.60, 0.95]` in `goldens/T7_high_cost_model_contract.json` and `src/build_goldens.py`; `uv run python -m src.build_goldens --check` → clean (8 files); `uv run python -m src.run_experiment freeze` → `64b7292e8214…` (previous `1566c5698a50…`).
- Stub gate: `run-stub --run-id stub_003 --conditions reflection_only,skill_learning,self_refine` → 3 × 4 tasks done; reflection_only/skill_learning 9 retries each with the 3-finding cap (fixture applies literal fixes), self_refine stops after its one fixture revision; `validate_logs()` → 0 problems; archived to `archive/experiment-3_stub_003_smoke/`.
- Manual run `run_005` (`init` verified the freeze): 46 operator request/response pairs (reflection_only 16, skill_learning 18, self_refine 12 steps of 64), **0 operator validation errors**, 0 execution errors; every event carries `provider_mode manual`, `operator claude-code-subagent`, `model_identifier claude-haiku-4-5-20251001`, `evaluator_version 1.2`, `freeze_sha256 64b7292e…`. Lead did not read any request/response until all arms were done. `validate_logs()` → 0 problems.
- Results (`scripts/summarize_run.py --run-id run_005 --json artifacts/reports/run_summaries.json`, per-attempt detail from `experiment_events.jsonl`):
  - reflection_only: attempts to pass 3 / 3 / 2 / 2 (T2, T4, T3, T7), first-attempt scores 2.16 / 2.07 / 2.34 / 2.75 (mean 2.33), failed checks on attempt 1: 8 / 8 / 8 / 5 = 29; final 4.00 / 3.84 / 3.87 / 3.60.
  - skill_learning: attempts 2 / 2 / 2 / 2, first-attempt 2.83 / 3.31 / 2.09 / 3.15 (mean 2.85), failed checks on attempt 1: 5 / 3 / 10 / 4 = 22; final 3.80 / 4.00 / 3.51 / 3.80; 1 skill proposed after T2 (revision requested once for `optional_sections`, then accepted, persisted as `evolved_run_005_001` "correct denial-rate denominator selection"), retrieved on T4, T3, T7, cited in the plans of T4 and T3 (`skill_reused` × 2), not cited on T7; proposals skipped on T4/T3/T7 ("no lesson reusable in ≥ 2 remaining tasks").
  - self_refine: verdict "accept" on T2 attempt 1 (frozen 2.89, fail), T4 attempt 1 (3.14, fail), T3 attempt 2 after one self-requested revision (1.61, fail), T7 attempt 2 after one self-requested revision that removed the leaking amount features and moved the threshold to train-only (3.60, pass). `self_declared_pass` true for 4 / 4, checker pass 1 / 4.
- Figures regenerated from the logs: `uv run python -m src.charts` (6 figures + topology), `uv run python -m src.dashboard`; article figures via `articles/loop-engineering-markdown-skills/assets/make_figures.py` (hero, loop diagram, score by attempt, attempts and first-try findings, self-review vs checker), each inspected as a PNG before publication.
- Caveat recorded for the write-up: the two checker arms drew different first plans from a stochastic operator (skill_learning's T2 first attempt scored 2.83 with an empty library vs reflection_only's 2.16), so part of the first-attempt gap is operator variance, not memory; the cleanest memory signal is T4 (skill cited, 3 failed checks vs 8) and the attempts-to-pass pattern.

## L0 · 2026-09-08 · Experiment 4 — six-task suite, raw-memory arms, five conditions (reported run `run_006`)

- Repo reset: `run_005` moved to `archive/experiment-3_run_005/` with `scripts/archive_run.py` (36 / 64 / 223 / 15 JSONL lines — experiment/feedback/graph/skill events —, run manifest, checkpoint, task and manual artifacts, 1 evolved skill + index entry, figures, write-up copied as `docs/writeup_run_005.md`). Goldens, suite, rubric untouched.
- Code: new module `src/feedback_memory.py`; graph v4 (`config/graph.yaml` gains a `memory:` block; `feedback_memory` travels the `reflection_only` route, `self_refine_memory` the `self_refine` route — no new nodes); evaluator 1.3 (the two new condition names join the list stripped from a report before caveat keywords are matched; scoring, rubric and goldens unchanged); `Services.memory_factory`; new skill-event names `memory_retrieved` / `memory_written`; `past_feedback_count` on every done record. Tests: `uv run --extra dev pytest -q` → **185 passed** (5 new, per decision D-22: memory-arm routing, `past_feedback`/`past_feedback_note` payload keys, `memory_retrieved`/`memory_written` events, condition-name stripping in evaluator 1.3).
- Golden pack: goldens and rubric are **unchanged** from experiment 3; only `config/tasks.yaml` changed — T1 and T8 briefs blinded and `task_order` set to `[T1, T2, T4, T3, T7, T8]`. `uv run python -m src.build_goldens --check` → clean (8 files). `uv run python -m src.run_experiment freeze` → `59fb61d35fe8…` (previous `64b7292e8214…`).
- Stub gate: `run-stub --run-id stub_004 --conditions reflection_only,feedback_memory,skill_learning,self_refine,self_refine_memory` → 5 × 6 tasks done; `validate_logs()` → 0 problems; archived to `archive/experiment-4_stub_004_smoke/`.
- Manual run `run_006` (`init` verified the freeze): **115 operator request/response pairs** across the five conditions (reflection_only 23, feedback_memory 16, skill_learning 31, self_refine 21, self_refine_memory 24 steps of 64), **2 operator validation errors** (1 in reflection_only, 1 in self_refine, both re-requested and resolved), 0 execution errors; every event carries `provider_mode manual`, `operator claude-code-subagent`, `model_identifier claude-haiku-4-5-20251001`, `evaluator_version 1.3`, `freeze_sha256 59fb61d35fe8…`. `uv run python -c "from src.experiment_logger import validate_logs; print(len(validate_logs()))"` → **0 problems**. The lead did not read any request/response until all arms were done; an orchestrator subagent spawned the operators (rather than the lead spawning each one directly, as in earlier runs).
- Results (`scripts/summarize_run.py --run-id run_006 --json artifacts/reports/run_summaries.json`, per-attempt detail from `experiment_events.jsonl`, task order T1/T2/T4/T3/T7/T8):
  - reflection_only: attempts to pass 2/2/2/3/2/3 (14 total), first-attempt scores 3.02/2.83/2.81/1.35/2.75/1.29 (mean 2.34), failed checks on attempt 1: 3/5/5/12/5/9 = 39; final 4.00/3.80/4.00/3.87/3.60/3.91; 6/6 passed.
  - feedback_memory: attempts to pass 2/2/2/1/2/2 (11 total), first-attempt scores 3.20/2.83/3.19/3.87/3.15/2.78 (mean 3.17), failed checks on attempt 1: 2/5/3/1/4/5 = 20; final 4.00/3.80/4.00/3.87/3.80/3.64; 6/6 passed; T3 passed on the first attempt with 9 past checker findings already in its log (`memory_retrieved` counts by task: T1 0, T2 2, T4 6, T3 9, T7 10, T8 14); memory file `artifacts/memory/run_006/feedback_memory.jsonl` — 19 notes at run end.
  - skill_learning: attempts to pass 2/3/1/2/3/2 (13 total), first-attempt scores 3.20/2.43/3.64/2.45/2.20/2.86 (mean 2.80), failed checks on attempt 1: 2/7/2/8/7/2 = 28; final 4.00/4.00/3.64/3.64/4.00/4.00; 6/6 passed; 2 skills proposed, both initially rejected on `example_present` ("example has 0 characters; needs at least 10") and persisted after one revision each — `evolved_run_006_001` "include synthetic data caveat in reports" (after T1, feedback id `T1-caveat_synthetic`, applicable T2/T3/T4/T7/T8, cited on T3/T7/T8) and `evolved_run_006_002` "denial-rate denominator standardization" (after T2, feedback ids `T2-denial_rate_value`/`T2-denial_rate_denominator`, applicable T3/T4, cited on T4/T3); 7 retrievals, 5 reuse events; proposals skipped on T4/T3/T7/T8 ("no lesson applicable to ≥ 2 remaining tasks").
  - self_refine: verdict "accept" on T1 attempt 1 (3.29, fail), T2 attempt 1 (2.83, fail), T4 attempt 2 after one self-requested revision (3.14, fail), T3 attempt 1 (1.97, fail), T7 attempt 2 after one self-requested revision that removed the leaking amount features and moved the threshold to train-only (3.60, **pass**), T8 attempt 1 (3.64, a frozen **pass**) followed by a self-requested revision that the operator itself asked for anyway, landing at attempt 2 (3.38, fail) — it revised its way out of a pass. `self_declared_pass` true 6/6, checker pass 1/6.
  - self_refine_memory: verdict "accept" on T1 attempt 1 (3.20, fail), T2 attempt 2 (2.69, fail), T4 attempt 2 (2.98, fail), T3 attempt 1 (2.07, fail), T7 attempt 2 (3.80, **pass**), T8 attempt 4 after three self-requested revisions (2.59, fail). `self_declared_pass` true 6/6, checker pass 1/6; `memory_retrieved` counts by task: T1 0, T2 0, T4 2, T3 4, T7 4, T8 7; memory file `artifacts/memory/run_006/self_refine_memory.jsonl` — 10 notes at run end; the memory of its own past verdicts did not raise its first-attempt mean (2.37) above plain self_refine's (2.92).
  - By-dimension means (first attempt → final, `evaluator_score_by_dimension`, computed over the six tasks): correctness 2.34→4.00 / 3.33→4.00 / 2.81→4.00 / 2.34→2.70 / 2.29→2.85; completeness 3.11→3.93 / 3.55→3.70 / 3.39→3.83 / 3.26→3.04 / 3.11→3.33; reproducibility 3.52→4.00 / 3.52→4.00 / 4.00→4.00 / 4.00→4.00 / 3.52→4.00; statistical discipline 1.28→3.83 / 2.90→3.83 / 1.81→3.81 / 2.14→2.57 / 1.24→2.10; communication 1.45→3.55 / 2.53→3.72 / 1.97→3.76 / 2.87→2.87 / 1.69→2.17 (order: reflection_only, feedback_memory, skill_learning, self_refine, self_refine_memory).
  - Means (`run_summaries.json`): mean final score 3.863 / 3.852 / 3.880 / 3.035 / 2.888; mean first-attempt score 2.342 / 3.170 / 2.797 / 2.922 / 2.372 (same order).
- Figures regenerated from the logs: `uv run python -m src.charts` (6 figures + topology), `uv run python -m src.dashboard`; article figures via `articles/loop-engineering-markdown-skills/assets/make_figures.py --run-id run_006` (`results_grid.png`, `loop_diagram.png`, plus hero/score-by-attempt/self-review-vs-checker), inspected as PNGs before publication.
- Caveat recorded for the write-up: the three checker arms drew different first plans from the same stochastic operator on T1, before any of them had accumulated anything (reflection_only 3.02 vs feedback_memory 3.20 vs skill_learning 3.20), so part of every gap reported is operator variance, not the memory mechanism under test.
- Note on a discrepancy: an earlier verbal summary of this run cited "152 operator requests" and "32 orchestration rounds"; `logs/graph_events.jsonl` records exactly 115 `operator_request` events (matching the per-condition `operator_steps_used` in `run_summaries.json`, which sum to 115) and 2 `operator_validation_error` events for `run_006`, and no field in any log records an "orchestration round" count. The write-up and this entry use the log-verified 115 and omit the unverifiable round count.

### 2026-09-08T07:32:40+00:00 — `scripts/pipeline.py verify` (82s, 0 failure(s))
- PASS — required file README.md
- PASS — required file pyproject.toml
- PASS — required file .env.example
- PASS — required file config/experiment.yaml
- PASS — required file config/tasks.yaml
- PASS — required file config/rubric.yaml
- PASS — required file config/graph.yaml
- PASS — required file data/README.md
- PASS — required file data/processed/manifest.json
- PASS — required file skills/SKILL_SCHEMA.md
- PASS — required file docs/spec.md
- PASS — required file docs/plan.md
- PASS — required file docs/tasks.md
- PASS — required file docs/security-review.md
- PASS — required file docs/decision-log.md
- PASS — required file docs/writeup.md
- PASS — required file artifacts/dashboard/progress.html
- PASS — six foundational skills present — 01_data_contract.md, 02_safe_claims_joins.md, 03_descriptive_summary.md, 04_categorical_numeric_analysis.md, 05_reproducible_python_analysis.md, 06_evaluation_and_charting.md
- PASS — golden pack reproduces from data (build_goldens --check) — golden pack check clean: 10 files match the recomputation (built_at ignored)
- PASS — freeze manifest matches data/goldens/tasks/rubric — 74e64e1d38e3
- PASS — JSONL logs valid
- PASS — agent tracker maintained — 7 agents, gates passed=True
- PASS — LangGraph compiles and matches designed topology
- PASS — pytest -q — ............................................                             [100%]

## L0 · 2026-09-08 · Experiment 5 — held-out transfer test, three arms, two seeded warm (reported run `run_007`)

- `run_006` is **not** archived (decision D-23): the article's figures read both runs. No repo reset for this experiment.
- Code: `src/feedback_memory.py` gains `redact_numbers`, `redact_record`, `number_tokens`, `FeedbackMemory.seed`; `src/skill_store.py` gains `seed_run_ids` / `exclude_skill_ids` (lists `skills/evolved/run_006/*.md` read-only, never copies them); `src/run_experiment.py` gains the three new config keys and `Runner._seed_memory` plus the task-index offset; `src/build_goldens.py` gains `build_t9`/`build_t10`; `src/analyses/catalogue.py` hoists T4's and T3's component objects into named constants shared by T9/T10; `src/task_runner.py` maps `T9 → t4_denials`, `T10 → t3_providers`; new `scripts/seed_audit.py`; `config/experiment.yaml` (`seed_from_run: run_006`, `task_index_offset: 6`, `seed_skill_exclude: []`); `config/graph.yaml` gains a `seeding:` note block only — **no topology change**, graph v4 stands. Tests: `uv run --extra dev pytest -q` (verified live in this session) → **188 passed** (72 + 72 + 44 across the three collected chunks; 3 new tests per decision D-23).
- Golden pack: two new files `goldens/T9_denial_hotspots_metrics.json` and `goldens/T10_specialty_spend_metrics.json`, built by independent reference code (`build_t9`, `build_t10`) that never imports the executor; T9 keeps T4's conventions (code shares scoped to denied claims, denominator = adjudicated claims, `min_group_size` 30) on the three segments `place_of_service`/`auth_required_flag`/`network_status`, plus a new tolerance check on the largest place-of-service segment (`22`: 545/4,946 = 0.1101900525677315 ± 1e-6); T10 keeps T3's conventions with `provider_ranking` re-parametrised to `metric: paid_amount_sum, top_n: 10, min_claims: 30` and `paid_amount_mean` added to the per-specialty contract. `uv run python -m src.build_goldens --check` (verified live) → `golden pack check clean: 10 files match the recomputation (built_at ignored)` — the eight goldens carried over from experiments 3–4 are byte-identical apart from `built_at`. `uv run python -m src.run_experiment freeze` → new freeze `74e64e1d38e3888fd54a9c02e64dd6fcee389bee7b6aba14cdfa7c86729f8b58` (previous `59fb61d35fe8…`), confirmed live against `config/freeze_manifest.json`.
- Stub gate: `run-stub --run-id stub_005 --conditions reflection_only,feedback_memory,skill_learning` → 3 × 4 tasks done; `validate_logs()` → 0 problems; archived to `archive/experiment-5_stub_005_smoke/`.
- Seeding, verified live: `logs/runs/run_007.json`'s `"seeding"` block records `source_run: run_006`, the redaction rule (every numeric token in a seeded note's `text`/`detail` replaced by `[n]`, except `T\d+`, `p90`, `p99`), `feedback_memory: {records_read: 19, records_seeded: 19, numbers_redacted: 24}`, and `skills: {files: [evolved_run_006_001_v1.md, evolved_run_006_002_v1.md], excluded_skill_ids: [], mode: "read-only ... never copied, never edited"}`.
- Leakage audit, re-run live in this session: `uv run python scripts/seed_audit.py --run-id run_007 --holdout T9,T10,T5,T6` → **seed audit clean** — 181 material golden numbers (≥ 3 significant digits) in 1,833 string forms (plain, thousands-separated, rounded 2–6 dp) compared against 58 numeric tokens surviving in 2 seeded skill files and 38 seeded note fields; 0 reachable. Informational: before redaction the seed run carried 24 numeric tokens across those same note fields, of which 4 would have reached a holdout golden — all four are T9 values from `run_006`'s T4 note (`denial_code_ranking.codes[0].n = 241`, `.share = 0.187402799377916`, `.codes[1].n = 206`, `.share = 0.16018662519440124`) and the redaction rule removed all four before seeding. `seed_skill_exclude` remains empty — neither skill file needed editing.
- Manual run `run_007` (`init` verified the freeze): **28 operator request/response pairs** across the three conditions (reflection_only 10, feedback_memory 6, skill_learning 12 steps of 64 — confirmed live: 28 `.request.json` files under `artifacts/manual/run_007/`), **0 operator validation errors**, 0 execution errors; every event carries `provider_mode manual`, `operator claude-code-subagent`, `model_identifier claude-haiku-4-5-20251001`, `evaluator_version 1.3`, `freeze_sha256 74e64e1d38e3…`. `uv run python -c "from src.experiment_logger import validate_logs; print(len(validate_logs()))"` (verified live) → **0 problems**. The lead did not read any request/response until all arms were done.
- Results (`artifacts/reports/run_summaries.json`, per-attempt detail from `logs/experiment_events.jsonl`, `logs/feedback_events.jsonl` and `logs/skill_events.jsonl`, task order T9/T10/T5/T6):
  - reflection_only (cold): attempts to pass 2/2/2/1 (7 total), first-attempt scores 3.26/3.09/3.28/3.68 (mean 3.327), failed checks on attempt 1: 3/5/3/2 = 13 (`T9.segment_rates`/`T9.largest_place_of_service_denial_rate`/`T9.segment_denominator`; `T10.groups_specialty`/`T10.top_spend_specialty_denial_rate`/`T10.group_denominator`; `T5.no_leaking_features`/`T5.caveat_synthetic`/`T5.caveat_no_operational_use`; `T6.caveat_synthetic`/`T6.caveat_no_operational_use`); final 4.00/3.69/4.00/3.68; 4/4 passed; 10 operator steps.
  - feedback_memory (warm, seeded 19 notes): attempts to pass 1/1/2/1 (5 total), first-attempt scores 3.52/3.64/3.44/3.68 (mean 3.57), failed checks on attempt 1: 2/2/2/1 = 7 (`T9.show_denominators`/`T9.caveat_synthetic`; `T10.provider_ranking_min_claims`/`T10.join_check_rendering_npi`; `T5.no_leaking_features`/`T5.caveat_no_operational_use`; `T6.caveat_model_limitations`); final 4.00/3.64/4.00/3.68; 4/4 passed; `memory_retrieved`/`memory_written` counts by task confirm the note count grows 19→25 over the run; 6 operator steps.
  - skill_learning (warm, seeded 2 skills from `run_006`): attempts to pass 1/1/2/1 (5 total), first-attempt scores 3.77/3.51/3.28/3.84 (mean 3.60), failed checks on attempt 1: 1/3/3/1 = 8 (`T9.min_group_size`; `T10.provider_ranking_min_claims`/`T10.join_check_rendering_npi`/`T10.caveat_association`; `T5.no_leaking_features`/`T5.caveat_synthetic`/`T5.caveat_no_operational_use`; `T6.caveat_no_operational_use`); final 3.77/3.51/4.00/3.84; 4/4 passed; 1 new skill proposed after T9 (`evolved_run_007_001`, "min-group-size threshold for segmented rates", feedback id `T9-min_group_size`), rejected once on `example_present` (0-character example) exactly as both `run_006` skills were, persisted after one revision; `skill_retrieved` 7, `skill_reused` 5 — T9 cites `evolved_run_006_002` (denominator); T10 retrieves and reuses all three (`evolved_run_006_001`, `evolved_run_006_002`, `evolved_run_007_001`); T5 retrieves `evolved_run_007_001` but does not cite it; T6 retrieves `evolved_run_007_001` and `evolved_run_006_001`, reuses `evolved_run_006_001` (synthetic caveat); 12 operator steps.
  - Means (`run_summaries.json`, confirmed live): mean final score 3.843 / 3.71 / 3.78; mean first-attempt score 3.327 / 3.57 / 3.6 (order: reflection_only, feedback_memory, skill_learning).
  - Reading recorded for the write-up: on every held-out task both warm arms opened at or above the cold arm's first attempt (never below); the cold arm alone failed the adjudicated-claims-denominator convention on T9 and T10 while neither warm arm did; on T5 (fraud exploration) all three arms failed the leakage check (`no_leaking_features`, `caveat_no_operational_use`) — a convention no training task had taught, exactly as the transfer hypothesis predicts.
- Figures regenerated from the logs (confirmed live via `artifacts/figures/figures_manifest.json`, `generated_at 2026-09-08T07:51:22+00:00`, `run_ids` including both `run_006` and `run_007`): `uv run python -m src.charts` (6 figures + topology), `uv run python -m src.dashboard`; article figures via `articles/loop-engineering-markdown-skills/assets/make_figures.py` — `transfer_curve.png` and an extended `results_grid.png` regenerated from both runs (both files present, dated 2026-09-08 15:54, after the manual run completed).
- Not independently verified in this session: an informal count of "13 orchestration rounds" for `run_007` was supplied for the write-up; as with `run_006`'s "32 orchestration rounds" (noted above), no log field records a round count — only the 28 `operator_request`-equivalent files under `artifacts/manual/run_007/` and the per-condition `operator_steps_used` (10/6/12, summing to 28) are log-verified. The round count is omitted from `docs/writeup.md`.

## L0 · 2026-09-08 · Experiment 5 v2 — convention-dense held-out test, memory frozen (reported run `run_008`)

- `run_007` **archived** (decision D-24) to `archive/experiment-5_run_007_heldout-v1/` — confirmed on disk: logs, checkpoints, task artifacts, operator transcripts, its memory log (25 notes at task end) and its one learned skill (`evolved_run_007_001`). `run_006` remains unarchived (its material is read by the article's figures and by `run_008`'s seeding).
- Code: `src/build_goldens.py` gains `_build_portfolio(..., paid_trend=)` and `_build_high_cost(..., percentile=, reference_model=)` (so T11 cannot drift from T2 nor T12 from T7) plus `build_t11`/`build_t12`/`build_t13`, `month_amount_series`, `reference_roc_auc`, `ROC_AUC_BAND`; `src/analyses/catalogue.py` hoists shared component constants (`PORTFOLIO_COMPONENTS`, `HIGH_COST_COMPONENTS`, `BRIEF_SECTIONS`); `src/task_runner.py` maps `T11 → t2_portfolio`, `T12 → t7_high_cost`, `T13 → t8_brief`; `src/analyses/t8_brief.py` gains `SOURCE_FAMILY`; `src/graph_nodes.py` gains `Services.memory_read_only`, the `completed` route, `memory_write_skipped`; `src/run_experiment.py` gains `RunConfig.memory_read_only`; `src/experiment_logger.py` gains the `memory_write_skipped` event name. **No graph topology change** — graph v4 stands, `config/graph.yaml` untouched. Tests re-run live in this session: `uv run --extra dev pytest -q` → **192 passed** (collected count confirmed per-file: 72+72+48, matching the 4-new-tests-from-188 claim in D-24).
- Golden pack, confirmed live: `uv run python -m src.build_goldens --check` → `golden pack check clean: 13 files match the recomputation (built_at ignored)` — the ten goldens carried over from experiments 3–4/v1 are byte-identical apart from `built_at`; three new files `T11_portfolio_deep_dive_metrics.json`, `T12_high_cost_p90_model_contract.json`, `T13_cfo_brief_rubric.yaml`. T12's golden fits its own leakage-free reference `LogisticRegression(max_iter=2000, random_state=42)` on train-only one-hot + standardised features and asserts the held-out ROC-AUC lands in the `[0.60, 0.95]` band before writing the pack; recorded value (from the golden's `reference.leakage_free_reference.roc_auc_test`) **0.9164886520817476**. `uv run python -c "from src.run_experiment import verify_freeze; print(verify_freeze())"` → `('bab215a5fbccbd60a7108f7417d3b8a2a40a05e06f6353221b40d800f788bbdd', [])` — freeze intact, no drift.
- Winnability check (recorded in decision D-24 and `docs/OPERATOR_PROTOCOL.md`, **not independently rerun in this session** — no script under `scripts/` reproduces it and none was found): catalogue defaults score **1.18 / 1.69 / 1.57** on T11/T12/T13 against the frozen evaluator; the house conventions score **4.00 / 4.00 / 4.00**.
- Stub gate `archive/experiment-5_stub_006_smoke/README.md` (confirmed on disk): "fixture operator over T11 -> T12 -> T13 with the memory frozen; all three arms reached 4.00, validate_logs() clean, the seeded 19-note log untouched and no skill persisted" — moved 39 experiment-event lines, 13 skill-event lines, 132 graph-event lines, 126 feedback-event lines; `skills/index.json` moved 0 entries (kept 2, the two `run_006` skills' index entries untouched).
- Seeding, verified live from `logs/runs/run_008.json`'s `"seeding"` block: `source_run: run_006`, `memory_read_only: true`, `feedback_memory: {records_read: 19, records_seeded: 19, numbers_redacted: 24}`, `skills: {files: [evolved_run_006_001_v1.md, evolved_run_006_002_v1.md], excluded_skill_ids: [], mode: "read-only ... never copied, never edited"}`.
- Leakage audit, re-run live in this session: `uv run python scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13` → **seed audit clean** — 95 material golden numbers (≥ 3 significant digits) in 981 string forms compared against 58 numeric tokens in the seeded material (2 skill files, 38 seeded note fields); 0 reachable. Informational: before redaction the seed run carried 24 numeric tokens across those note fields, of which 1 would have reached a holdout golden — `artifacts/memory/run_006/feedback_memory.jsonl:3 [detail]`, token `12339`, matching `goldens/T11_portfolio_deep_dive_metrics.json`'s `expected_exact.denial_rate.denominator = 12339.0`. `seed_skill_exclude` remains empty.
- Manual run `run_008` (`init` verified the freeze): **19 operator request/response pairs** across the three conditions (reflection_only 9, feedback_memory 5, skill_learning 5 — confirmed live: 9/5/5 `.request.json` files under `artifacts/manual/run_008/<condition>/`, matching `operator_steps_used` in both `logs/runs/run_008.json` and `artifacts/reports/run_summaries.json`), **0 operator validation errors**, 0 execution errors; every event carries `provider_mode manual`, `operator claude-code-subagent`, `model_identifier claude-haiku-4-5-20251001`, `evaluator_version 1.3`, `freeze_sha256 bab215a5fbcc…`, `memory_read_only true`. `uv run python -c "from src.experiment_logger import validate_logs; print(len(validate_logs()))"` (verified live) → **0 problems**.
- Results (`artifacts/reports/run_summaries.json`, confirmed live; task order T11/T12/T13):
  - reflection_only (cold): score_by_attempt T11 [2.85, 3.73], T12 [3.15, 3.80], T13 [2.44, 4.00] — 6 attempts total; first_attempt_passed false/false/false (0/3); mean_first_attempt_score 2.813, mean_final_score 3.843; 3/3 passed; 9 operator steps, stop_reason `passed` on all three.
  - feedback_memory (warm, seeded 19 notes, frozen): score_by_attempt T11 [3.87], T12 [4.00], T13 [2.86, 4.00] — 4 attempts total; first_attempt_passed true/true/false (2/3); mean_first_attempt_score 3.577, mean_final_score 3.957; 3/3 passed; `skill_events: {memory_retrieved: 3, memory_write_skipped: 3}` (no `memory_written` — confirms the freeze held for all three tasks); 5 operator steps.
  - skill_learning (warm, seeded 2 skills from `run_006`, frozen): score_by_attempt T11 [3.60], T12 [2.95, 3.80], T13 [4.00] — 4 attempts total; first_attempt_passed true/false/true (2/3); mean_first_attempt_score 3.517, mean_final_score 3.8; 3/3 passed; `skill_events: {skill_retrieved: 4, skill_reused: 3}`, `skills_created: []` (nothing persisted, as the frozen memory requires); 5 operator steps.
  - First-try failed-check counts, from `logs/experiment_events.jsonl` (cross-checked against the write-up's per-task findings): reflection_only 6/4/4 = 14; feedback_memory 1/0/2 = 3; skill_learning 4/4/0 = 8.
- Figures regenerated from the logs (confirmed live via `artifacts/figures/figures_manifest.json`, `generated_at 2026-09-08T09:57:28+00:00`, `run_ids` now including `run_004`, `run_005`, `run_006`, `run_007`, `run_008`, `stub_003`–`stub_006`): `uv run python -m src.charts` (6 figures + topology), `uv run python -m src.dashboard`; article figures via `articles/loop-engineering-markdown-skills/assets/make_figures.py` regenerate `transfer_curve.png` and `results_grid.png` from `run_006` and `run_008` (the manifest's `task_ids` list now runs T1–T13).
- Caveat recorded for the write-up: the winnability figures (catalogue-defaults 1.18/1.69/1.57 and house-conventions 4.00/4.00/4.00) come from decision D-24 and `docs/OPERATOR_PROTOCOL.md`, both consistent with each other; no standalone script reproducing that pre-run check was found in `scripts/` in this session, so it is cited as documented, not independently re-derived.
