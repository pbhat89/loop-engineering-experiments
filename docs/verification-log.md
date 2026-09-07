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
