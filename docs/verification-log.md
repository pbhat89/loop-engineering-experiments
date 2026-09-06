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
