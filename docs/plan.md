# Plan — claims-skill-loop (the HOW: interface contract)

**Status:** Phase 1 SDD document (A1). **Date:** 2026-09-06. **Binding source:** `docs/LEAD_DESIGN_DECISIONS.md` (LEAD §n below). Shapes marked *verbatim* are copied from LEAD; items marked **(A1 formalisation)** fill gaps LEAD leaves open and stand unless L0 overrides them. Agents A2–A6 code against this file; deviations go in their final reports, not into silent changes.

---

## 1. Module architecture and dependency flow

```text
frozen inputs: config/tasks.yaml · config/rubric.yaml · goldens/ · data/processed/manifest.json · config/freeze_manifest.json
        │
run_experiment.py (L0)  outer loop T1…T8 per condition · CLI · freeze check · request/response files · status + dashboard refresh
        │ builds one compiled graph per condition
claims_graph.py (L0)    StateGraph + SqliteSaver + routers
        │ node functions
graph_nodes.py (L0) ────┬── llm_provider.py (L0)        manual interrupt · stub fixtures · anthropic_api (unused)
                        ├── skill_store.py, skill_validator.py (A4)
                        ├── task_runner.py → analyses/t1…t8 (A6)   deterministic execution
                        ├── evaluator.py (A3)  ← rubric.yaml + goldens/  deterministic scoring
                        └── experiment_logger.py (A5) → logs/*.jsonl · logs/experiment_status.json
                                                            └→ dashboard.py · charts.py (A5)   read logs only
utils.py (L0)          paths · hashing · atomic IO — imported by everyone, imports nothing from src/
agent_tracker.py (L0)  → logs/agent_status.json → dashboard.py
download_data.py, profile_data.py (A2) → data/raw, data/processed/manifest.json (one-time, only network user)
build_goldens.py (A3)  → goldens/  (pandas + manifest only)
```

| Module | Owner | Responsibility | May import from `src/` |
|---|---|---|---|
| `utils.py` | L0 | repo paths, `utc_now`, `sha256_file/text`, YAML/JSON/JSONL IO, `atomic_write_*`, `FileLock` | nothing |
| `llm_provider.py` | L0 | `OperatorRequest`, response models, `Provider` protocol, `ManualProvider`, `FixtureProvider`, `AnthropicProvider`, `get_provider()` | utils |
| `graph_state.py` | L0 | `ClaimsState` TypedDict (§4) | — |
| `claims_graph.py` | L0 | `build_claims_skill_graph(condition, checkpointer=None)`, routers (§6) | graph_state, graph_nodes |
| `graph_nodes.py` | L0 | node functions (§5) | llm_provider, skill_store, skill_validator, task_runner, evaluator, experiment_logger, utils |
| `run_experiment.py` | L0 | CLI (§9), outer loop, operator file IO, freeze verification, status/dashboard refresh | claims_graph, llm_provider, experiment_logger, dashboard, charts, utils |
| `download_data.py`, `profile_data.py` | A2 | pinned download + SHA-256; profiling; manifest (§10) | utils |
| `build_goldens.py`, `evaluator.py` | A3 | golden pack (§14); deterministic evaluation (§15) | utils only — **never** task_runner/analyses |
| `task_runner.py`, `analyses/` | A6 | plan validation + dispatch + artifacts (§13) | utils, profile_data (`load_table`) — **never** evaluator/build_goldens/goldens |
| `skill_store.py`, `skill_validator.py` | A4 | skills (§16) | utils |
| `experiment_logger.py`, `dashboard.py`, `charts.py` | A5 | logs, status, dashboard, figures (§17–18) | utils |
| `agent_tracker.py` | L0 | build tracker (exists) | utils, dashboard |

Import rules: `langchain_anthropic` is imported only inside the `anthropic_api` branch of `llm_provider.py`; nothing under `src/` performs network IO except `download_data.py`; charts and dashboard compute from log files only.

## 2. Runtime modes and credential boundaries (LEAD §1)

| Mode | Default | Behaviour |
|---|---:|---|
| `manual` | **yes** | No model calls. LLM-decision nodes call `provider.decide(request)`; the manual provider calls LangGraph `interrupt(request)` and the graph pauses. The lead writes the request file, a stateless `experiment-operator` subagent writes the response file, the lead resumes with `Command(resume=response)`. |
| `stub` | no | `FixtureProvider` answers the same requests deterministically from the request payload (rule-based). Tests and pipeline demos only; always labelled non-LLM simulation. |
| `anthropic_api` | no | Thin adapter around `langchain_anthropic.ChatAnthropic` with structured output; fails closed without `ANTHROPIC_API_KEY`; **not used in this study**. |

Environment: `CLAIMS_SKILL_LOOP_LLM_MODE=manual|stub|anthropic_api` (default `manual`), `CLAIMS_SKILL_LOOP_MODEL` (record-only in manual mode; default `claude-fable-5-1`), `CLAIMS_SKILL_LOOP_OPERATOR` (default `claude-code-subagent`). `ANTHROPIC_API_KEY` is read only in `anthropic_api` mode and never logged.

```python
class OperatorRequest(BaseModel):
    request_id: str        # "<run_id>:<condition>:<task_id>:a<attempt>:<node>:<seq>"
    run_id: str; condition: str; task_id: str; attempt: int; node: str; seq: int
    created_at: str
    instructions: str      # what to decide, in plain language
    payload: dict          # task_spec, manifest_summary, component_catalogue, remaining_task_ids,
                           # + per condition/node: retrieved_skills, prior_plan, evaluation, feedback, reflection,
                           # validation_errors (when re-requesting), proposal (for revise_skill_proposal)
    response_schema: dict  # JSON schema of the expected response model

class Provider(Protocol):
    mode: str              # manual | stub | anthropic_api
    operator: str          # claude-code-subagent | deterministic-fixture | anthropic-api
    model_identifier: str  # claude-fable-5-1 | deterministic-fixture-v1 | <api model id>
    def decide(self, request: OperatorRequest) -> dict: ...
```

Credential boundary: the runtime never reads, proxies, or reuses Claude Code session credentials, OAuth tokens, browser cookies, or subscription state; there is no Agent SDK and no headless-CLI bridge. The operator is a subagent spawned by the lead **inside** the Claude Code session, communicating with the runtime only through JSON files on disk.

## 3. Operator protocol

**Files** (LEAD §1): `artifacts/manual/<run_id>/<condition>/<task_id>_a<attempt>_<node>_<seq>.request.json` and the matching `.response.json`. The response file is the response-model object itself (no envelope); the runner pairs files by name **(A1 formalisation)**.

**Sequence per interrupt** (lead session):

1. `advance` runs the graph until `__interrupt__` appears in the result; the runner writes the interrupt value (the `OperatorRequest`) to the request file, logs `operator_request`, sets condition status `waiting_operator` with `pending_request`, prints the path, exits.
2. The lead spawns one fresh `experiment-operator` subagent with the request path and the response path. The subagent reads only the request and writes only the response.
3. `resume --response <path>` reads the file (JSON only, ≤ 256 KB, `.response.json` suffix under `artifacts/manual/`), computes its SHA-256, logs `operator_response`, and calls `graph.invoke(Command(resume=response), config)`.
4. Inside the node, the response is validated against the response model. On failure the node logs `operator_validation_error` (not an execution error) and calls `interrupt()` again with `seq + 1` and `validation_errors` in the payload. At most **2 re-requests per node call**; after that the node falls back to the catalogue default for that decision and records an `errors` entry of type `operator_fallback` **(A1 formalisation)**.
5. The lead never edits a response. Every logged event records `provider_mode`, `operator`, `model_identifier`, and `response_sha256`.

**Re-execution rule (LangGraph semantics):** on resume LangGraph re-runs the node from its start; `interrupt()` calls return earlier resume values in order. Therefore nodes must build requests deterministically and perform logging and state mutation **after** the last `interrupt()` returns; `seq` is the 1-based index of the `interrupt()` call within the node execution. `operator_steps_used` is incremented by the number of requests issued once the node completes; the cap is checked before each request (§7).

**Payload per node** (`payload` keys; `task_spec` is the catalogue entry, `manifest_summary` is tables → rows/columns/dtypes/date ranges with `sample_values` ≤ 50 chars, `component_catalogue` is `task_spec.components`, `remaining_task_ids` are the tasks after the current one):

| Node | Response model | Payload additions |
|---|---|---|
| `plan_task` | `PlanResponse` | `retrieved_skills` (skill_learning only, from `render_for_operator`) |
| `revise_plan` | `PlanResponse` | `prior_plan`, `evaluation`, `feedback`, `reflection` (reflection_only, skill_learning), `retrieved_skills` (skill_learning) |
| `reflect_on_feedback` | `ReflectionResponse` | `prior_plan`, `evaluation`, `feedback`, `retrieved_skills` (skill_learning), `retry_budget_left: bool` |
| `propose_skill` | `SkillProposalResponse` | `reflection`, `feedback`, `existing_skills` (id, name, objective, tags of every eligible skill — for duplicate awareness) |
| `revise_skill_proposal` | `SkillProposalResponse` | `proposal`, `validation` (failed checks), `existing_skills` |

**Response models** (LEAD §4, §8 — *verbatim* field sets):

```json
PlanResponse: {"steps": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
               "skills_applied": ["foundational_003"], "rationale": "...", "changes_summary": "only for revise_plan"}

ReflectionResponse: {"reusable_lessons": [{"lesson": "...", "applicable_task_ids": ["T3", "T4"], "source_feedback_ids": ["T2-denial_rate_value"]}],
                     "current_task_corrections": [{"feedback_id": "T2-denial_rate_value", "correction": "..."}]}

SkillProposalResponse: {"proposal": null | {"name": "...", "tags": [], "trigger": "...", "objective": "...", "procedure": ["..."],
                                            "required_checks": ["..."], "expected_artifacts": ["..."], "failure_modes": ["..."],
                                            "example": "...", "applicable_task_ids": ["..."], "source_feedback_ids": ["..."]},
                        "reason_if_null": "string or null"}
```

Plan validation (LEAD §4): known component; `params ⊆` declared params; option values valid; missing params → declared defaults; duplicate components rejected; a revised plan is a **full plan**, not a diff. `skills_applied` ids not present in `retrieved_skills` are dropped and noted in the `operator_response` event as `skills_applied_dropped` (no re-request) **(A1 formalisation)**.

**Stub provider** answers from the payload only: `plan_task` → all `default_selected` components with default params (plus any component listed in `task_spec.required_components`, if A3 defines such a key); `revise_plan` → prior plan with each feedback item's `related_components` applied; `reflect_on_feedback` → lessons derived from `reusable: true` feedback; `propose_skill` → a proposal when ≥ 2 `applicable_task_ids` remain, else `null`; `revise_skill_proposal` → proposal with failed structural checks filled. Its `model_identifier` is `deterministic-fixture-v1`.

## 4. LangGraph state schema (`src/graph_state.py`)

`ClaimsState(TypedDict, total=False)`; lists marked *append* use an `operator.add` reducer, everything else is last-write-wins. `attempt = retry_count + 1` (derived, not stored).

| Field | Type | Reducer | Set by |
|---|---|---|---|
| `run_id` | `str` | — | runner |
| `condition` | `str` | — | runner |
| `task_id` | `str` | — | runner |
| `task_index` | `int` (0-based position in `task_order`) | — | runner |
| `remaining_task_ids` | `list[str]` (tasks after this one) | — | runner |
| `task_spec` | `dict` (the `tasks.yaml` entry) | — | `load_context` |
| `dataset_manifest` | `dict` | — | `load_context` |
| `available_skills` | `list[dict]` (all eligible skills; `[]` outside skill_learning) | — | `retrieve_skills` |
| `retrieved_skills` | `list[dict]` (top-k with `score`, `matched_terms`) | — | `retrieve_skills` |
| `analysis_plan` | `dict \| None` (validated `PlanResponse`) | — | `plan_task`, `revise_plan` |
| `plan_history` | `list[dict]` | append | `plan_task`, `revise_plan` |
| `execution_result` | `dict \| None` (§13) | — | `execute_task` |
| `evaluation` | `dict \| None` (§15) | — | `evaluate_output` |
| `evaluation_history` | `list[dict]` | append | `evaluate_output` |
| `feedback` | `list[dict]` (latest attempt) | — | `evaluate_output` |
| `reflection` | `dict \| None` (`ReflectionResponse`) | — | `reflect_on_feedback` |
| `skill_proposal` | `dict \| None` | — | `propose_skill`, `revise_skill_proposal` |
| `skill_validation` | `dict \| None` (§16) | — | `validate_skill` |
| `skills_created` | `list[str]` | append | `persist_skill` |
| `retry_count` | `int` | — | `revise_plan` (+1) |
| `max_retries` | `int` (2) | — | runner |
| `route_history` | `list[str]` (node names; routers append `"route_after_x:<label>"`) | append | every node/router |
| `artifacts` | `list[str]` (latest attempt, repo-relative) | — | `execute_task` |
| `errors` | `list[dict]` (`{type, component, message, attempt, node}`) | append | `execute_task`, LLM nodes |
| `status` | `str` ∈ `running \| waiting_operator \| passed \| failed \| done` | — | nodes |
| `provider_mode` | `str` | — | runner |
| `model_identifier` | `str` | — | runner |
| `operator` | `str` | — | runner |
| `operator_steps_used` | `int` (condition running total, seeded by the runner) | — | LLM nodes |
| `max_operator_steps` | `int` (40) | — | runner |
| `pass_threshold` | `float` (3.5) | — | runner |
| `golden_path` | `str` | — | `load_context` |
| `freeze_sha256` | `str` | — | runner |
| `output_dir` | `str` (`artifacts/tasks/<run_id>/<condition>/<task_id>/attempt_<n>`) | — | `execute_task` |
| `seed` | `int` (42) | — | runner |
| `stop_reason` | `str \| None` ∈ `passed \| retry_budget_exhausted \| operator_cap` | — | `finalize_task` |

Brief deviation: the brief typed `analysis_plan` as `str | None`; LEAD §4 makes the plan structured JSON, so it is `dict | None` (`docs/decision-log.md`). No secrets, raw prompts, or dataset rows are ever placed in state.

## 5. Nodes (`src/graph_nodes.py`)

| Node | Interrupts (manual) | Reads | Writes | Logs |
|---|:-:|---|---|---|
| `load_context` | no | `tasks.yaml`, manifest, rubric/golden paths, config | `task_spec`, `dataset_manifest`, `golden_path`, `status=running` | `node_transition` |
| `retrieve_skills` (skill_learning only) | no | `SkillStore(root, run_id).retrieve(task_spec, task_index, k)` | `available_skills`, `retrieved_skills` | `skill_retrieved` × k |
| `plan_task` | **yes** | catalogue, manifest summary, `retrieved_skills` | `analysis_plan`, `plan_history`, `operator_steps_used` | `operator_request/response`, `skill_reused` for `skills_applied` |
| `execute_task` | no | `task_runner.execute(task_spec, plan, run_context)` | `execution_result`, `artifacts`, `errors`, `output_dir` | `node_transition` |
| `evaluate_output` | no | `evaluator.evaluate(task_spec, execution_result, rubric, golden)` | `evaluation`, `evaluation_history`, `feedback`, `status=passed\|failed` | `feedback_issued` × n, attempt record in `experiment_events` |
| `reflect_on_feedback` | **yes** | plan, evaluation, feedback | `reflection` | operator events |
| `revise_plan` | **yes** | prior plan, evaluation, feedback, reflection | `analysis_plan` (full), `plan_history`, `retry_count += 1` | operator events, `feedback_update` (incorporated) |
| `propose_skill` | **yes** | reflection, feedback, existing skills, remaining tasks | `skill_proposal` (may be `None`) | `skill_proposed` |
| `validate_skill` | no | `skill_validator.validate(proposal, existing, task_id, remaining)` | `skill_validation` | `skill_validated` / `skill_rejected` |
| `revise_skill_proposal` | **yes** | proposal + failed checks | `skill_proposal` | operator events, `skill_proposed` (`revision: 1`) |
| `persist_skill` | no | `SkillStore.persist(proposal, provenance)` | `skills_created` | `skill_persisted` |
| `finalize_task` | no | everything | `stop_reason`, `status=done` | final `experiment_events` record, status snapshot, dashboard + charts refresh |

Every LLM node applies the cap rule (§7) before requesting: when `operator_steps_used ≥ max_operator_steps` it uses the catalogue default instead of interrupting.

## 6. Routes per condition and routers (`src/claims_graph.py`)

`build_claims_skill_graph(condition: str, checkpointer=None) -> CompiledStateGraph` compiles **one graph per condition**; `config/graph.yaml` mirrors the nodes and edges below and `tests/test_graph_routes.py` asserts equality of node and edge sets per condition.

**baseline**

```text
START → load_context → plan_task → execute_task → evaluate_output
      → [completed: finalize_task]
      → [retry, within budget: revise_plan → execute_task]
      → END
```

**reflection_only**

```text
START → load_context → plan_task → execute_task → evaluate_output
      → [completed: finalize_task]
      → [retry, within budget: reflect_on_feedback → revise_plan → execute_task]
      → END
```

**skill_learning**

```text
START → load_context → retrieve_skills → plan_task → execute_task → evaluate_output
      → [retry, within budget: reflect_on_feedback → revise_plan → execute_task]
      → [learn (pass, or fail with no retry left): reflect_on_feedback → propose_skill]
            propose_skill → [proposal null: finalize_task]
                          → [proposal: validate_skill]
            validate_skill → [accepted: persist_skill → finalize_task]
                           → [rejected: finalize_task]
                           → [retry_revision: revise_skill_proposal → validate_skill]
      → END
```

**Routers** (pure functions of state; each appends `route_after_x:<label>` to `route_history` via the node that precedes it):

```python
def route_after_evaluation(state) -> Literal["completed", "retry", "learn"]:
    passed = state["evaluation"]["passed"]
    budget_left = state["retry_count"] < state["max_retries"]
    if not passed and budget_left:
        return "retry"                      # baseline → revise_plan; others → reflect_on_feedback
    return "learn" if state["condition"] == "skill_learning" else "completed"   # learn → reflect_on_feedback

def route_after_reflection(state) -> Literal["retry", "learn"]:      # skill_learning only; reflection_only has a static edge → revise_plan
    passed = state["evaluation"]["passed"]
    return "retry" if (not passed and state["retry_count"] < state["max_retries"]) else "learn"   # retry → revise_plan; learn → propose_skill

def route_after_proposal(state) -> Literal["validate", "skip"]:      # skip when proposal is None → finalize_task
def route_after_validation(state) -> Literal["accepted", "rejected", "retry_revision"]:   # persist_skill | finalize_task | revise_skill_proposal
```

`route_after_reflection`, `route_after_proposal`, and `route_after_validation` are **(A1 formalisation)** of LEAD §2's routes; the decision logic is LEAD's.

## 7. Retry, termination, and stopping rules (Addendum B, LEAD §2)

1. Pass (`evaluation.passed`) → finalize immediately (`stop_reason = passed`).
2. `max_retries = 2`; `revise_plan` increments `retry_count`; attempt `n` writes to `attempt_<n>`. Budget exhausted → `stop_reason = retry_budget_exhausted`.
3. `propose_skill` may return `proposal: null`; validation is skipped. `retry_revision` is possible only once (validator returns it only on the first attempt).
4. Operator cap: `operator_steps_used` counts every request file written (re-requests included) and is seeded per task from the condition total. When `operator_steps_used ≥ max_operator_steps` no request is issued: `plan_task` uses catalogue defaults, `revise_plan` keeps the prior plan, `reflect_on_feedback` returns an empty reflection, `propose_skill` returns `null`; routing is unchanged; the task's `stop_reason` is `operator_cap` and the cap event is logged (`graph_events` `route_reason = operator_cap`).
5. All conditions run all eight tasks; the runner never skips a task.
6. Per-attempt execution deadline `execution_timeout_seconds` (`config/graph.yaml`, default 300): the executor checks the deadline between components and returns `status: partial` with an `errors` entry of type `timeout`; the runner treats it like any other execution result **(A1 formalisation; security requirement)**.

## 8. Checkpointing, interrupts, and threads (LEAD §2)

- Checkpointer: `SqliteSaver` on `logs/checkpoints/<run_id>.sqlite` (context-managed per CLI invocation).
- One graph invocation per task; `config = {"configurable": {"thread_id": f"{run_id}:{condition}:{task_id}"}}`.
- Initial state per task is built by the runner from config + condition totals (`operator_steps_used`); **nothing else crosses tasks in state**. The only cross-task memory is skill files (skill_learning).
- Interrupt/resume: `ManualProvider.decide()` = `interrupt(request.model_dump())`; the runner resumes with `Command(resume=response_dict)`. A thread that has finished (`END`) is never re-invoked.
- Conditions may be advanced independently (three threads, at most three operator subagents in flight); the recommended pattern is round-robin from the lead session to avoid SQLite write contention. `database is locked` errors are retried with back-off by the runner.
- Recovery: `status` reads checkpoints + `experiment_status.json`; a crashed `advance` is safely re-run because the last checkpoint precedes the interrupt.

## 9. Runner CLI and outer loop (LEAD §9)

```text
uv run python -m src.run_experiment init     --run-id run_001 --conditions baseline,reflection_only,skill_learning [--mode manual|stub]
uv run python -m src.run_experiment advance  --run-id run_001 --condition skill_learning   # runs until the next interrupt or the condition finishes; prints the pending request path
uv run python -m src.run_experiment resume   --run-id run_001 --condition skill_learning --response <path>
uv run python -m src.run_experiment status   --run-id run_001
uv run python -m src.run_experiment run-stub --run-id stub_001                              # full stub run, no interrupts
```

`init` (manual mode) verifies `config/freeze_manifest.json` against the files on disk and refuses on drift; it writes `logs/runs/<run_id>.json` (mode, conditions, config snapshot, `freeze_sha256`, `model_identifier`, `operator`) **(A1 formalisation)** and the initial `experiment_status.json`. `advance` loops tasks in `task_order` for the condition; after every node and task the runner updates `experiment_status.json` and refreshes the dashboard (§18). `run-stub` is `init --mode stub` followed by `advance` for every condition; it must complete without any interrupt.

## 10. Data manifest (LEAD §13, *verbatim* shape; A2)

```json
{"source": {"repo": "xpertsystems/hlt008-sample", "revision": "7309ddb3…", "license": "cc-by-nc-4.0", "retrieved_at": "..."},
 "tables": {"medical_claims": {"path": "data/raw/medical_claims.csv", "sha256": "...", "bytes": 3525830, "rows": 12800,
            "columns": [{"name": "claim_id", "dtype": "object", "null_count": 0, "n_unique": 12800, "sample_values": ["..."]}],
            "candidate_keys": ["claim_id"], "date_columns": ["service_date_from", "..."], "date_ranges": {"service_date_from": ["2021-01-01", "2023-12-31"]}}},
 "relationships": [{"from": "medical_claims.member_id", "to": "members.member_id", "cardinality": "many_to_one", "unmatched_from": 0, "unmatched_from_denominator": 12800}]}
```

`sample_values` are truncated to 50 characters (prompt-injection hygiene: dataset text never reaches an operator request except as short samples). `profile_data.load_table(name) -> DataFrame` and `download_data.load_manifest() -> dict` are the read APIs. Numbers above are LEAD's examples; A2's manifest is authoritative.

## 11. Task suite and plan-component catalogue (LEAD §3, *verbatim*; A3 `config/tasks.yaml`)

```yaml
suite_version: "1"
task_order: [T1, T2, T3, T4, T5, T6, T7, T8]
tasks:
  - task_id: T2
    title: Claims portfolio description
    objective: >-            # the analyst brief as a person would receive it; fair, no hints about golden choices
      ...
    tags: [descriptive, rates, trends, financial]
    input_tables: [medical_claims]
    golden_file: goldens/T2_portfolio_metrics.json
    required_artifacts: [claims_status_distribution.png, monthly_claim_volume.png, financial_summary.csv, report.md, metrics.json]
    components:
      - id: denial_rate
        description: Denial rate with explicit numerator and denominator.
        default_selected: false          # what an unguided/stub baseline plan includes
        params:
          denominator:
            description: Which claims form the denominator.
            options: [all_claims, adjudicated_claims, paid_and_denied]
            default: all_claims          # the naive choice, never automatically the golden choice
        produces:                        # metric keys the executor writes to metrics.json
          - key: denial_rate
            shape: {value: float, numerator: int, denominator: int, numerator_definition: str, denominator_definition: str}
```

Rules: component ids are snake_case; shared components across tasks are allowed (`load_tables`, `join_check`, `write_report`, `save_metrics_json`, …); every metric key referenced by a golden or a rubric check must appear in some component's `produces`; the catalogue must offer genuinely different analytical choices (denominators, date columns, exclusion lists, threshold sources, small-group thresholds, caveat sets). The `objective` text is what the operator sees; it must not hint at golden choices.

## 12. Plan schema (LEAD §4)

```json
{"steps": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
 "skills_applied": ["foundational_003"], "rationale": "...", "changes_summary": "only for revise_plan"}
```

`plan_sha256 = sha256_text(json.dumps(plan, sort_keys=True))` identifies a plan in logs and `metrics.json`. `skills_applied` (skill ids the operator says it used) is how "reuse" is counted.

## 13. Execution result (LEAD §5; A6 `src/task_runner.execute(task_spec, plan, run_context) -> dict`)

`run_context = {run_id, condition, task_id, attempt, seed, output_dir, manifest_path, data_dir, timeout_seconds}` (`timeout_seconds` **A1 formalisation**, optional, default 300).

```json
{"status": "ok|partial|error", "task_id": "T2", "attempt": 1,
 "output_dir": "artifacts/tasks/run_001/baseline/T2/attempt_1",
 "artifacts": ["artifacts/tasks/.../claims_status_distribution.png", "..."],
 "metrics_path": ".../metrics.json", "report_path": ".../report.md",
 "metrics": {"...": "same content as metrics.json"},
 "components_executed": ["load_tables", "denial_rate"], "components_failed": [],
 "errors": [{"type": "unknown_component|invalid_param|missing_column|runtime_error|timeout", "component": "...", "message": "..."}],
 "seed": 42, "duration_seconds": 1.2}
```

`metrics.json` top level: `task_id, run_id, condition, attempt, seed, generated_at, plan_sha256, tables: {name: {rows, columns}}` plus one entry per produced metric key in the declared shape. `report.md` cites artifacts by relative path and contains a `## Caveats` section when the `write_report` component's `caveats` param is non-empty. Plan problems never raise — they become `errors`; `status: error` only when nothing could run. No `eval`/`exec`/shell/network; writes confined to `output_dir`; matplotlib uses the Agg backend.

## 14. Golden pack and freeze manifest (LEAD §6, §7; A3 + L0)

Golden file (*verbatim* shape):

```json
{"task_id": "T2", "golden_version": "1", "built_at": "...", "builder": "src/build_goldens.py",
 "dataset_revision": "7309ddb30e67468748b7aa9182d8517fe28c2f9c", "data_sha256": {"medical_claims.csv": "..."},
 "expected_exact": {"total_medical_claims": 12800},
 "expected_metrics": {"denial_rate": {"value": 0.1003, "tolerance": 0.0001,
                                      "definition": {"numerator": "claim_status == 'Denied'", "denominator": "claim_status in {Paid, Denied, Adjusted}"}}},
 "required_artifacts": ["claims_status_distribution.png", "monthly_claim_volume.png", "financial_summary.csv"],
 "required_caveats": [{"id": "synthetic_data", "any_of": ["synthetic", "simulated"]}],
 "prohibited_fields": ["fraud_pattern_type"],
 "contracts": {"split": {"test_size": 0.25, "stratify": "fraud_label", "seed": 42}, "threshold": {"source": "train", "percentile": 95}},
 "metric_ranges": {"roc_auc": {"min": 0.5, "max": 1.0}}}
```

Files: `goldens/T1_data_contract.json`, `T2_portfolio_metrics.json`, `T3_provider_network_metrics.json`, `T4_denial_analysis_metrics.json`, `T5_fraud_exploration_metrics.json`, `T6_fraud_model_contract.json`, `T7_high_cost_model_contract.json`, `T8_executive_brief_rubric.yaml` (required findings as metric references, caveat keywords, forbidden causal phrasings, artifact-reference requirements). `build_goldens.py` uses pandas + the manifest only, is deterministic, has `--check` (recompute and diff against committed files), and never imports executor code.

Freeze manifest `config/freeze_manifest.json` (L0, Phase 1.5; shape **A1 formalisation**):

```json
{"freeze_version": "1", "frozen_at": "2026-09-06T00:00:00+00:00", "dataset_revision": "7309ddb30e67468748b7aa9182d8517fe28c2f9c",
 "files": {"config/tasks.yaml": "<sha256>", "config/rubric.yaml": "<sha256>",
           "goldens/T1_data_contract.json": "<sha256>", "...": "...", "goldens/T8_executive_brief_rubric.yaml": "<sha256>",
           "data/raw/members.csv": "<sha256>", "...": "...", "data/raw/adherence.csv": "<sha256>"}}
```

`freeze_sha256 = sha256_file("config/freeze_manifest.json")`. Verification recomputes every listed file; any mismatch or missing file lists the drifted paths and aborts `init` in manual mode. Phase 1.5 order: build goldens → `--check` → **user reviews values** → freeze → commit.

## 15. Rubric and evaluation (LEAD §7; A3)

- `config/rubric.yaml`: `rubric_version`, `pass_threshold: 3.5`, five dimensions, per-task `checks: [{check_id, dimension, weight, critical, kind, target, related_components, remediation, reusable, applicable_task_ids}]`, `kind ∈ {exact, tolerance, artifact_exists, field_excluded, contract, caveat_keywords, metric_range, report_structure}`.
- Scoring: dimension = `4 × Σ(weight·passed) / Σ(weight)` (2 dp); total = mean of the five (2 dp); `passed = all critical checks passed and total ≥ pass_threshold`. A missing metric fails its check with `observed: null`. A dimension with no checks for a task scores `null` and is excluded from the mean **(A1 formalisation)**.
- `evaluate(task_spec, execution_result, rubric, golden) -> dict` (*verbatim*):

```json
{"evaluator_version": "1.0", "rubric_version": "1", "rubric_sha256": "...", "golden_sha256": "...", "freeze_sha256": "...",
 "scores": {"correctness": 3.2, "completeness": 4.0, "reproducibility": 4.0, "statistical_discipline": 2.0, "communication": 3.0},
 "score_total": 3.24, "passed": false,
 "checks": [{"check_id": "T2.denial_rate_value", "dimension": "correctness", "weight": 2, "critical": true, "passed": false,
             "observed": 0.0871, "expected": 0.1003, "detail": "denominator all_claims includes Pended"}],
 "feedback": [{"feedback_id": "T2-denial_rate_value", "criterion": "correctness", "issue_type": "wrong_denominator", "severity": "high",
               "remediation": "Use adjudicated claims (Paid, Denied, Adjusted) as the denominator and state it.",
               "related_components": [{"component": "denial_rate", "params": {"denominator": "adjudicated_claims"}}],
               "reusable": true, "applicable_task_ids": ["T3", "T4"]}]}
```

Feedback is emitted only for failed checks; `feedback_id = "<task_id>-<check name>"`. Feedback `incorporated` (§17) is true when the next attempt's plan contains every `related_components` entry with the stated params; `resolved` is true when the same `check_id` passes on the next attempt **(A1 formalisation)**.

## 16. Skills (LEAD §8; A4)

- Layout: `skills/SKILL_SCHEMA.md`; `skills/foundational/01_data_contract.md … 06_evaluation_and_charting.md` (ids `foundational_001…006`); `skills/evolved/<run_id>/<skill_id>_v<version>.md` (**run-scoped**; ids `evolved_<run_id>_<nnn>`); `skills/archived/`; `skills/index.json` (mutable: reuse counts, status, per skill; skill files themselves are immutable). Frontmatter = brief schema + extension field `tags: []`.
- `Skill`: frontmatter fields (`skill_id, name, version, status, kind, created_after_task, source_feedback_ids, created_at, reuse_count`) + `tags` + `sections: dict[str, str]` (Trigger, Objective, Procedure, Required checks, Expected artifacts, Failure modes, Example, Provenance) + `path`.
- `SkillStore(root, run_id=None)`: `list_skills() -> list[Skill]`; `retrieve(task_spec, current_task_index, k=6) -> list[dict]` (each `skill_id, name, version, kind, path, score, matched_terms`); `render_for_operator(skills) -> list[dict]` (id, name, kind, trigger, objective, procedure, required_checks, failure_modes — bounded text); `persist(proposal, provenance) -> Skill`; `record_reuse(skill_id, task_id)`; `archive(skill_id, reason)`.
- Retrieval is deterministic: `score = 2 × |tags ∩| + |keywords ∩|` between the task's objective/tags and the skill's trigger/objective/tags (lower-cased tokens, stop-words removed); foundational always eligible; evolved eligible only when `created_after_task` index `< current_task_index` (and same `run_id`); ties broken by `skill_id`; top-`k` with `score > 0` returned, foundational with score 0 excluded **(A1 formalisation of "top-k")**.
- `validate(proposal, existing_skills, task_id, remaining_task_ids) -> {"decision": "accepted|rejected|retry_revision", "checks": [{check_id, passed, detail}], "duplicate_of": null, "similarity": 0.31}`. Checks: schema/required sections; safety (no shell, network, credential, code-execution instructions); generality (not a single-task restatement, no hard-coded numeric findings, no ungrounded claims); provenance (task id + ≥ 1 feedback id from the request); applicability (`|applicable_task_ids ∩ remaining_task_ids| ≥ 2`); duplicate = token-Jaccard over objective + procedure `≥ 0.6` against any existing skill. `retry_revision` only for fixable structural issues on the first attempt; duplicates and safety failures are `rejected`.
- Provenance recorded on persist: `run_id, condition, task_id, attempt, source_feedback_ids, proposal_sha256, response_sha256, created_after_task`.
- Skill events (via A5 logger): `skill_proposed, skill_validated, skill_persisted, skill_rejected, skill_retrieved, skill_reused, skill_archived`.

## 17. Event schemas (A5 `src/experiment_logger.py`)

Common fields on **every** record in the four JSONL logs: `run_id, condition, task_id, attempt, timestamp, provider_mode, operator, model_identifier, freeze_sha256`. Timestamps are `utc_now()`. Writers append with `append_jsonl`; readers use `read_jsonl`; `validate_logs() -> list[str]` returns `file:line: problem` strings and is used by `scripts/verify.sh`.

**`logs/experiment_events.jsonl`** — one record per task attempt (brief shape + LEAD §10 fields):

```json
{"run_id": "run_001", "condition": "skill_learning", "task_id": "T3", "attempt": 1, "timestamp": "ISO-8601",
 "provider_mode": "manual", "operator": "claude-code-subagent", "model_identifier": "claude-fable-5-1", "freeze_sha256": "...",
 "rubric_version": "1", "evaluator_version": "1.0", "input_hash": "...", "plan_sha256": "...",
 "files_used": ["data/raw/medical_claims.csv"], "skills_retrieved": ["foundational_003"], "skills_reused": ["foundational_003"], "skills_created": [],
 "graph_route": ["load_context", "retrieve_skills", "plan_task", "execute_task", "evaluate_output"],
 "execution_attempts": 1, "execution_errors": 0, "execution_status": "ok",
 "evaluator_score_total": 3.4, "evaluator_score_by_dimension": {"correctness": 3.2, "completeness": 4.0, "reproducibility": 4.0, "statistical_discipline": 2.0, "communication": 3.0},
 "passed": false, "critical_failed": ["T3.join_check"], "artifact_paths": ["artifacts/tasks/run_001/skill_learning/T3/attempt_1/report.md"],
 "operator_steps_used": 5, "operator_validation_errors": 0, "duration_seconds": 41.0,
 "status": "retrying", "stop_reason": null}
```

`status ∈ {retrying, done}`; `stop_reason` is non-null only on the final record of a task. `input_hash = sha256_text(json.dumps({"task_id", "plan", "seed", "freeze_sha256"}, sort_keys=True))`.

**`logs/graph_events.jsonl`** — `event_type ∈ {node_transition, operator_request, operator_response, operator_validation_error}`:

```json
{"...common": "...", "event_type": "node_transition", "source_node": "evaluate_output", "destination_node": "reflect_on_feedback",
 "route_reason": "route_after_evaluation:retry", "retry_count": 0, "status": "failed", "operator_steps_used": 5}
{"...common": "...", "event_type": "operator_request", "node": "revise_plan", "seq": 1, "request_id": "run_001:skill_learning:T3:a1:revise_plan:1",
 "request_path": "artifacts/manual/run_001/skill_learning/T3_a1_revise_plan_1.request.json", "operator_steps_used": 6}
{"...common": "...", "event_type": "operator_response", "node": "revise_plan", "seq": 1, "request_id": "...", "response_path": "...response.json",
 "response_sha256": "...", "valid": true, "skills_applied_dropped": []}
{"...common": "...", "event_type": "operator_validation_error", "node": "revise_plan", "seq": 1, "request_id": "...", "response_path": "...",
 "response_sha256": "...", "validation_errors": ["steps[1].params.denominator: 'pended' is not one of [...]"]}
```

`route_reason` values: `route_after_evaluation:<completed|retry|learn>`, `route_after_reflection:<retry|learn>`, `route_after_proposal:<validate|skip>`, `route_after_validation:<accepted|rejected|retry_revision>`, `static`, `operator_cap`.

**`logs/skill_events.jsonl`** — `event_type ∈ {skill_proposed, skill_validated, skill_persisted, skill_rejected, skill_retrieved, skill_reused, skill_archived}` plus `skill_id, name, version, kind, path` (null where not yet known) and per type: `skill_retrieved: rank, score, matched_terms` · `skill_reused: plan_sha256` · `skill_proposed: proposal_sha256, response_sha256, applicable_task_ids, source_feedback_ids, revision (0|1), reason_if_null` · `skill_validated / skill_rejected: decision, checks, duplicate_of, similarity, revision` · `skill_persisted: sha256, created_after_task, source_feedback_ids, provenance` · `skill_archived: reason`.

**`logs/feedback_events.jsonl`** — append-only; readers take the latest record per `feedback_id`:

```json
{"...common": "...", "event_type": "feedback_issued", "feedback_id": "T3-join_check", "check_id": "T3.join_check", "criterion": "statistical_discipline",
 "issue_type": "missing_join_check", "severity": "high", "remediation": "...", "related_components": [{"component": "join_check", "params": {}}],
 "reusable": true, "applicable_task_ids": ["T4", "T5"], "incorporated": null, "incorporated_in_attempt": null, "resolved": null}
{"...common": "...", "event_type": "feedback_update", "feedback_id": "T3-join_check", "incorporated": true, "incorporated_in_attempt": 2, "resolved": true}
```

**`logs/experiment_status.json`** (atomic; LEAD §10 *verbatim*):

```json
{"updated_at": "...", "runs": {"run_001": {"mode": "manual", "conditions": {"baseline": {
  "status": "queued|running|waiting_operator|done", "current_task": "T3", "attempt": 2, "current_node": "revise_plan",
  "pending_request": "artifacts/manual/run_001/baseline/T3_a2_revise_plan_1.request.json", "waiting_since": "...",
  "tasks_completed": 2, "tasks_total": 8, "scores": {"T1": 3.6, "T2": 2.8}, "first_attempt_pass": {"T1": true, "T2": false},
  "retries": 1, "execution_errors": 0, "skills_created": 0, "skills_retrieved": 0,
  "operator_steps_used": 5, "operator_steps_cap": 40, "median_seconds_per_task": 412.0, "eta_minutes": 41.2, "eta_label": "rough ETA ≈ 41 min"}}}}}
```

ETA rule: `eta_minutes = remaining tasks × median observed seconds per completed task`; `eta_label = "ETA unavailable — insufficient completed work"` until two tasks of that condition have completed.

## 18. Dashboard refresh strategy and charts (A5)

| Trigger | Action |
|---|---|
| any `agent_tracker` event | `dashboard.render()` (existing v1 behaviour) |
| every node transition (runner) | `experiment_logger.update_status(...)` → `dashboard.render()` |
| every `finalize_task` | + `charts.render_all(run_id)` (learning curve, reliability curve, rubric heatmap, skill accumulation, skill utility, lifecycle graph) |
| end of a condition / `run-stub` | `charts.render_all` + `charts.render_topology()` |
| browser | `<meta http-equiv="refresh">` every `dashboard_refresh_seconds` (30) |

Rules: static HTML, no server, no external assets; every figure names its source log(s) and run ids; missing observations render as missing; the overall bar never shows 100 % until `acceptance_gates_passed`; stub runs are labelled "non-LLM simulation"; topology is labelled "designed workflow".

Skill-utility metric (illustrative): for each evolved skill, `delta_score = mean(score_total of tasks where it appears in skills_applied) − mean(score_total of the same task ids in reflection_only)`, likewise `delta_retries`; `reuse_count` from `skill_reused` events.

## 19. Directory conventions (LEAD §11)

`artifacts/tasks/<run_id>/<condition>/<task_id>/attempt_<n>/` (task outputs) · `artifacts/manual/<run_id>/<condition>/` (operator files) · `logs/checkpoints/<run_id>.sqlite` · `logs/runs/<run_id>.json` (run metadata) · `artifacts/figures/` (charts) · `artifacts/graphs/` (topology + observed lifecycle) · `artifacts/reports/` (write-up material) · `artifacts/dashboard/progress.html` · `data/processed/manifest.json` · `skills/evolved/<run_id>/`. All paths in logs are repo-relative POSIX (`utils.rel`).

## 20. Configuration (LEAD §12; A1)

`config/experiment.yaml` keys: `seed, conditions, task_order, max_retries, pass_threshold, max_operator_steps_per_condition, retrieval_k, duplicate_similarity_threshold, dataset {repo, revision, files}, freeze_manifest, default_mode, model_identifier, operator, dashboard_refresh_seconds`. `config/graph.yaml`: `nodes`, `llm_decision_nodes`, per-condition `entry`, `edges`, `conditional_edges` (router + label → target), and `termination` rules; `tests/test_graph_routes.py` asserts it matches each compiled graph. `pass_threshold` in `rubric.yaml` must equal `experiment.yaml` (test).

## 21. Testing strategy (LEAD §14)

| Test file | Owner | Asserts | Data |
|---|---|---|---|
| `tests/test_llm_provider.py` | L0 | default mode `manual`; `anthropic_api` fails closed without key and never imports `langchain_anthropic` otherwise; fixture answers validate against response models; request/response file naming | none |
| `tests/test_graph_routes.py` | L0 | each condition compiles; node/edge sets equal `graph.yaml`; `route_after_*` decisions for pass / retry / budget exhausted / cap; nothing crosses tasks; stub end-to-end on a tiny frame | in-memory |
| `tests/test_data_contract.py` | A2 | manifest shape; per-file SHA-256; row counts; keys; relationships; `sample_values ≤ 50` chars | skips with reason if `data/raw` empty |
| `tests/test_evaluator.py` | A3 | scoring formula; critical logic; each `kind`; missing metric → `observed: null`; feedback shape; `build_goldens --check` (skips without data) | fixtures + optional data |
| `tests/test_skill_store.py` | A4 | six foundational skills parse and validate; deterministic retrieval and eligibility by task index; persist immutability + ids; duplicate threshold; safety/generality rejections; `retry_revision` once | none |
| `tests/test_task_runner.py` | A6 | unknown component/param → structured error; result shape; determinism; writes only inside `output_dir`; no network; prohibited fields excluded when planned | tiny frames + optional data |
| `tests/test_logging.py`, `tests/test_dashboard.py` | A5 | schemas; `validate_logs` catches bad lines with `file:line`; status snapshot + ETA rules; dashboard renders with empty and populated logs; no 100 % before gates | synthetic logs |

All tests run in `stub` mode, offline: `uv run --extra dev pytest -q`.

## 22. Security strategy

Summarised here, detailed in `docs/security-review.md`: no credential reuse of any kind; `.env` git-ignored and never logged; operator IO is JSON only and schema-validated; dataset text reaches requests only as ≤ 50-char samples; executor has no `eval`/`exec`/shell/network and writes only inside `output_dir`; per-attempt timeout; no network after the one-time download; synthetic data, no PHI; CC-BY-NC-4.0 attribution.

## 23. Ownership and sequencing (LEAD §15)

| Owner | Files | Depends on |
|---|---|---|
| L0 | `src/llm_provider.py`, `graph_state.py`, `claims_graph.py`, `graph_nodes.py`, `run_experiment.py`, `utils.py`, `agent_tracker.py`, `scripts/`, `tests/test_graph_routes.py`, `tests/test_llm_provider.py`, freeze manifest, `docs/verification-log.md` consolidation | everyone |
| A1 | `docs/*` (not LEAD), `config/experiment.yaml`, `config/graph.yaml`, `README.md` | brief + LEAD |
| A2 | `src/download_data.py`, `src/profile_data.py`, `data/README.md`, `data/processed/manifest.json`, `artifacts/data_profile/`, `tests/test_data_contract.py` | §10 |
| A3 | `config/tasks.yaml`, `config/rubric.yaml`, `src/build_goldens.py`, `goldens/`, `src/evaluator.py`, `tests/test_evaluator.py` | A2 manifest |
| A4 | `skills/`, `src/skill_store.py`, `src/skill_validator.py`, `tests/test_skill_store.py` | §16 |
| A5 | `src/experiment_logger.py`, `src/dashboard.py` (extends v1), `src/charts.py`, `tests/test_logging.py`, `tests/test_dashboard.py` | §17 |
| A6 | `src/task_runner.py`, `src/analyses/`, `tests/test_task_runner.py` | A3 catalogue, A2 manifest |

Order: A1 and A2 start immediately; A3, A4, A5, A6 start when A2's manifest exists (A4 and A5 may start earlier). Phase 1.5 (goldens review by the user → freeze) precedes any comparative run. A full `stub` run must pass end-to-end before the first `manual` run.
