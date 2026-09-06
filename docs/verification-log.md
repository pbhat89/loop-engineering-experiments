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
