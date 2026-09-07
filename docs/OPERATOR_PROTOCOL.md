# Operator protocol for manual-mode runs (L0)

How the lead drives a comparative run without any model API call. Every LLM-decision step is answered by a **fresh, stateless Claude Code subagent** that sees exactly one request file and writes exactly one response file. The Python runtime never calls a model; it pauses on a LangGraph interrupt and resumes when the response file exists.

Two operator definitions exist:

| Definition | Used in | Model | Carries analytical conventions? |
|---|---|---|---|
| `.claude/agents/experiment-operator.md` | experiment 1 (`run_001`) | Claude Fable 5.1 (session model) | yes — a list of analytical standards (denominators, train-only fitting, leakage exclusions, caveats) |
| `.claude/agents/experiment-operator-blind.md` | experiment 3 (`run_005`) | Claude Haiku 4.5 (`model: haiku`) | **no** — house rules must come from the request: feedback, retrieved skills, or its own review |

The second definition exists because the first, combined with briefs that stated the conventions, produced the experiment-1 ceiling (every task 4.00 first attempt, nothing to learn). Experiment 3 blinds the briefs (`config/tasks.yaml`, four tasks) *and* the operator, caps the feedback to the three most severe findings per attempt with the literal fix withheld, and allows five attempts (`config/experiment.yaml`, decision D-21).

## Preconditions (Phase 1.5 gates)

1. `goldens/` built by `src/build_goldens.py`, reviewed by the user via `artifacts/reports/golden_review.md`.
2. `config/tasks.yaml` and `config/rubric.yaml` final.
3. `uv run python -m src.run_experiment freeze` → `config/freeze_manifest.json` (hashes of data, goldens, tasks, rubric). Comparative runs refuse to start if any hash drifts. Experiment 3 freeze: `64b7292e8214…` (experiments 1–2: `1566c5698a50…`; the briefs of T2/T3/T4/T7 and the T7 ROC-AUC band changed, nothing else).
4. A full `stub` run has passed end-to-end: `uv run python -m src.run_experiment run-stub --run-id stub_003 --conditions reflection_only,skill_learning,self_refine`.

## The loop

```bash
# once per run
uv run python -m src.run_experiment init --run-id run_005 --conditions reflection_only,skill_learning,self_refine --mode manual

# repeat until every condition reports done
uv run python -m src.run_experiment advance-all --run-id run_005     # resumes conditions whose response file exists, then prints pending requests
#   OPERATOR NEEDED [reflection_only] -> artifacts/manual/run_005/reflection_only/T2_a1_plan_task_1.request.json
#   OPERATOR NEEDED [skill_learning]  -> artifacts/manual/run_005/skill_learning/T2_a1_plan_task_1.request.json
#   OPERATOR NEEDED [self_refine]     -> artifacts/manual/run_005/self_refine/T2_a1_plan_task_1.request.json
# for each pending request: spawn one operator subagent (prompt below), which writes the matching .response.json
# then advance-all again
uv run python -m src.run_experiment status --run-id run_005            # per-condition tasks, scores, steps used, rough ETA
```

`logs/experiment_status.json` and `artifacts/dashboard/progress.html` update after every node; the dashboard shows the pending request per condition and how long it has waited.

Conditions are independent threads: up to three operator subagents run at the same time (one per condition). A subagent never sees another condition's files.

## Operator subagent prompt (verbatim template, experiment 3)

Spawned with the Agent tool, `model: haiku`, one per request file:

> You are the **experiment operator** for one manual-mode step of the claims-skill-loop experiment. Adopt `d:/Projects/SkillRL/claims-skill-loop/.claude/agents/experiment-operator-blind.md` as your operating instructions (read it first). Then read exactly one file — the request `<REQUEST_PATH>` — and write exactly one file — the response `<RESPONSE_PATH>` — as JSON conforming to the `response_schema` embedded in the request. Use only component ids and parameter options that appear in the request's `component_catalogue`; base every decision solely on the request contents; do not read or write any other file, run code, or use the network. Finish with one line naming the file you wrote and the decision you made.

Experiment 1 used the same template with `experiment-operator.md` and the session model.

Rules the lead follows:

- One subagent per request file, never reused, never given conversation context, never told which condition or task number it is beyond what the request contains.
- The lead never edits a response. A response that fails validation is logged (`operator_validation_error`) and the runner issues a new request with `validation_errors`; the lead spawns a new subagent for it.
- The lead does not read request or response contents during the run except to confirm a file exists (to avoid steering later steps); the files are inspected only after all conditions finish.
- If the session hits a rate limit mid-run, nothing is lost: checkpoints and request/response files are on disk; `advance-all` resumes after the reset.

## What the operator is shown (experiment 3)

| Step | reflection_only | skill_learning | self_refine |
|---|---|---|---|
| `plan_task` | brief, catalogue, manifest summary | + retrieved skills (learned in this run only; the library starts empty) | brief, catalogue, manifest summary |
| after `evaluate_output` | the 3 most severe failed checks (no literal fix) + scorecard + count of further failures | same | **nothing** — the operator reviews its own report and metrics (`self_evaluate`) and decides accept / revise |
| `revise_plan` | prior plan, those 3 findings, its reflection | + retrieved skills | prior plan, its own findings |
| after a pass | — | reflect over the whole task → propose ≤ 1 skill → validate → persist | — |

The frozen evaluator scores every attempt of every condition identically; only what is *shown* differs.

## What gets recorded

- `logs/graph_events.jsonl`: `operator_request` (request path), `operator_response` (response path, SHA-256), `operator_validation_error`, plus every node transition (for `self_evaluate`: the verdict next to the frozen score it did not see).
- `logs/experiment_events.jsonl`: one `attempt` record per evaluation (`n_failed_checks`, `n_feedback_shown`, `critical_failures`, `skills_applied`) and one `done` record per task with `attempts_to_pass`, `score_by_attempt`, `self_declared_pass`, `stop_reason` (`passed` | `retry_budget_exhausted` | `self_accepted` | `operator_cap`), provider metadata and `freeze_sha256`.
- `artifacts/manual/<run_id>/<condition>/*.request.json|*.response.json`: the complete operator transcript, committed with the run.

## Budget expectations (recorded, not promised)

Per condition and task, five attempts at most: `plan_task` (1) + up to 4 × (`reflect_on_feedback` + `revise_plan`) for reflection_only / skill_learning, or 4 × (`self_evaluate` + `revise_plan`) for self_refine; skill_learning adds `reflect_on_feedback` + `propose_skill` (+ ≤ 1 `revise_skill_proposal`) after each task. Hard cap `max_operator_steps_per_condition = 64`. The realised counts appear in `experiment_status.json` and the write-up.
