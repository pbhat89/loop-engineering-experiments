# Operator protocol for manual-mode runs (L0)

How the lead drives a comparative run without any model API call. Every LLM-decision step is answered by a **fresh, stateless Claude Code subagent** that sees exactly one request file and writes exactly one response file (`.claude/agents/experiment-operator.md`). The Python runtime never calls a model; it pauses on a LangGraph interrupt and resumes when the response file exists.

## Preconditions (Phase 1.5 gates)

1. `goldens/` built by `src/build_goldens.py`, reviewed by the user via `artifacts/reports/golden_review.md`.
2. `config/tasks.yaml` and `config/rubric.yaml` final.
3. `uv run python -m src.run_experiment freeze` → `config/freeze_manifest.json` (hashes of data, goldens, tasks, rubric). Comparative runs refuse to start if any hash drifts.
4. A full `stub` run has passed end-to-end: `uv run python -m src.run_experiment run-stub --run-id stub_check`.

## The loop

```bash
# once per run
uv run python -m src.run_experiment init --run-id run_001 --conditions baseline,reflection_only,skill_learning --mode manual

# repeat until every condition reports done
uv run python -m src.run_experiment advance-all --run-id run_001     # resumes conditions whose response file exists, then prints pending requests
#   OPERATOR NEEDED [baseline]       -> artifacts/manual/run_001/baseline/T1_a1_plan_task_1.request.json
#   OPERATOR NEEDED [skill_learning] -> artifacts/manual/run_001/skill_learning/T1_a1_plan_task_1.request.json
# for each pending request: spawn one operator subagent (prompt below), which writes the matching .response.json
# then advance-all again
uv run python -m src.run_experiment status --run-id run_001            # per-condition tasks, scores, steps used, rough ETA
```

`logs/experiment_status.json` and `artifacts/dashboard/progress.html` update after every node; the dashboard shows the pending request per condition and how long it has waited.

Conditions are independent threads: up to three operator subagents run at the same time (one per condition). A subagent never sees another condition's files.

## Operator subagent prompt (verbatim template)

> You are the **experiment operator** for one manual-mode step of the claims-skill-loop experiment. Adopt `d:/Projects/SkillRL/claims-skill-loop/.claude/agents/experiment-operator.md` as your operating instructions (read it first). Then read exactly one file — the request `<REQUEST_PATH>` — and write exactly one file — the response `<RESPONSE_PATH>` — as JSON conforming to the `response_schema` embedded in the request. Use only component ids and parameter options that appear in the request's `component_catalogue`; base every decision solely on the request contents; do not read or write any other file, run code, or use the network. Finish with one line naming the file you wrote and the decision you made.

Rules the lead follows:

- One subagent per request file, never reused, never given conversation context, never told which condition or task number it is beyond what the request contains.
- The lead never edits a response. A response that fails validation is logged (`operator_validation_error`) and the runner issues a new request with `validation_errors`; the lead spawns a new subagent for it.
- The lead does not read request or response contents during the run except to confirm a file exists (to avoid steering later steps); the files are inspected only after all conditions finish.
- If the session hits a rate limit mid-run, nothing is lost: checkpoints and request/response files are on disk; `advance-all` resumes after the reset.

## What gets recorded

- `logs/graph_events.jsonl`: `operator_request` (request path), `operator_response` (response path, SHA-256), `operator_validation_error`, plus every node transition.
- `logs/experiment_events.jsonl`: one `attempt` record per evaluation and one `done` record per task with `provider_mode: manual`, `operator: claude-code-subagent`, `model_identifier: claude-fable-5-1`, `operator_steps_used`, `stop_reason`, `freeze_sha256`.
- `artifacts/manual/<run_id>/<condition>/*.request.json|*.response.json`: the complete operator transcript, committed with the run.

## Budget expectations (recorded, not promised)

Per condition and task: `plan_task` (1) + up to 2 retries × (`reflect_on_feedback` + `revise_plan`, or `revise_plan` alone for baseline) + for `skill_learning` `reflect_on_feedback` + `propose_skill` (+ ≤ 1 `revise_skill_proposal`). Hard cap `max_operator_steps_per_condition = 64`. The realised counts appear in `experiment_status.json` and the write-up.
