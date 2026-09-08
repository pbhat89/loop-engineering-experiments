# Operator protocol for manual-mode runs (L0)

How the lead drives a comparative run without any model API call. Every LLM-decision step is answered by a **fresh, stateless Claude Code subagent** that sees exactly one request file and writes exactly one response file. The Python runtime never calls a model; it pauses on a LangGraph interrupt and resumes when the response file exists.

Two operator definitions exist:

| Definition | Used in | Model | Carries analytical conventions? |
|---|---|---|---|
| `.claude/agents/experiment-operator.md` | experiment 1 (`run_001`) | Claude Fable 5.1 (session model) | yes — a list of analytical standards (denominators, train-only fitting, leakage exclusions, caveats) |
| `.claude/agents/experiment-operator-blind.md` | experiments 3 (`run_005`), 4 (`run_006`) and 5 (`run_007`) | Claude Haiku 4.5 (`model: haiku`) | **no** — house rules must come from the request: feedback, retrieved skills, recorded past comments, or its own review |

The second definition exists because the first, combined with briefs that stated the conventions, produced the experiment-1 ceiling (every task 4.00 first attempt, nothing to learn). Experiment 3 blinds the briefs *and* the operator, caps the feedback to the three most severe findings per attempt with the literal fix withheld, and allows five attempts (decision D-21).

Experiment 4 (`run_006`, decision D-22) keeps all of that and changes two things: the suite is **six tasks** with T1 and T8 blinded as well, and there are **five arms** — the three from experiment 3 plus two *raw-memory* arms. A memory arm carries a plain log of past findings, appended verbatim after each task to `artifacts/memory/<run_id>/<condition>.jsonl` and shown in full (most recent first, at most 30 items) in the `past_feedback` key of later `plan_task` / `revise_plan` requests. Nothing is distilled, filtered for relevance or turned into a skill; the request itself says the comments come from earlier tasks and may or may not apply.

Experiment 5 (`run_007`, decision D-23) is a **held-out transfer test**: three arms — `reflection_only` (cold: checker feedback, no memory), `feedback_memory` (warm: seeded with run_006's 19 raw notes) and `skill_learning` (warm: seeded with run_006's two learned skills) — over **four tasks none of them has attempted**, in the order **T9 → T10 → T5 → T6** (article tasks 7–10). T9 "Denial hotspots" and T10 "Specialty spend and denials" are new tasks built on T4's and T3's components and conventions but different questions; T5 and T6 are the two tasks no run has ever reached, blinded here for the first time. No self-review arms.

Seeding happens once, at `init`, and is read-only with respect to `run_006`. The memory arm's log is copied from `artifacts/memory/run_006/feedback_memory.jsonl` into `artifacts/memory/run_007/feedback_memory.jsonl` with **every numeric token in each record's `text` and `detail` replaced by `[n]`** (except task ids `T\d+` and the quantile names `p90` / `p99`), each record stamped `seeded_from: run_006`; 19 records, 24 tokens redacted. The skills arm needs no copy at all — the store simply also lists `skills/evolved/run_006/*.md` read-only, so ids such as `evolved_run_006_001` show up in run_007's `skills_retrieved` while new skills still persist under `skills/evolved/run_007/`. `task_index_offset: 6` continues run_006's task numbering (its indices 0–5, run_007's 6–9), which is what keeps a skill learned after run_006's index 0 or 1 eligible from the very first held-out task. The whole provenance is in `logs/runs/run_007.json` under `"seeding"`, and `uv run python scripts/seed_audit.py --run-id run_007 --holdout T9,T10,T5,T6` re-checks it: it exits 1 if any number from a holdout golden is reachable from the seeded notes or skill files (it reported **clean**, and named the four golden values the redaction removed). A seeded skill file is never edited — a genuine leak would be handled by adding its id to `seed_skill_exclude` in `config/experiment.yaml`.

## Preconditions (Phase 1.5 gates)

1. `goldens/` built by `src/build_goldens.py`, reviewed by the user via `artifacts/reports/golden_review.md`.
2. `config/tasks.yaml` and `config/rubric.yaml` final.
3. `uv run python -m src.run_experiment freeze` → `config/freeze_manifest.json` (hashes of data, goldens, tasks, rubric). Comparative runs refuse to start if any hash drifts. Experiment 4 freeze: `59fb61d35fe8…` (experiment 3: `64b7292e8214…`; experiments 1–2: `1566c5698a50…`). Only the T1 and T8 briefs and `task_order` changed between 3 and 4; goldens and rubric are untouched.
4. A full `stub` run has passed end-to-end: `uv run python -m src.run_experiment run-stub --run-id stub_004 --conditions reflection_only,feedback_memory,skill_learning,self_refine,self_refine_memory` (experiment 4: `archive/experiment-4_stub_004_smoke/`).

## The loop

```bash
# once per run
uv run python -m src.run_experiment init --run-id run_006 --conditions reflection_only,feedback_memory,skill_learning,self_refine,self_refine_memory --mode manual

# repeat until every condition reports done
uv run python -m src.run_experiment advance-all --run-id run_006     # resumes conditions whose response file exists, then prints pending requests
#   OPERATOR NEEDED [reflection_only]    -> artifacts/manual/run_006/reflection_only/T1_a1_plan_task_1.request.json
#   OPERATOR NEEDED [feedback_memory]    -> artifacts/manual/run_006/feedback_memory/T1_a1_plan_task_1.request.json
#   OPERATOR NEEDED [skill_learning]     -> artifacts/manual/run_006/skill_learning/T1_a1_plan_task_1.request.json
#   OPERATOR NEEDED [self_refine]        -> artifacts/manual/run_006/self_refine/T1_a1_plan_task_1.request.json
#   OPERATOR NEEDED [self_refine_memory] -> artifacts/manual/run_006/self_refine_memory/T1_a1_plan_task_1.request.json
# for each pending request: spawn one operator subagent (prompt below), which writes the matching .response.json
# then advance-all again
uv run python -m src.run_experiment status --run-id run_006            # per-condition tasks, scores, steps used, rough ETA
```

`logs/experiment_status.json` and `artifacts/dashboard/progress.html` update after every node; the dashboard shows the pending request per condition and how long it has waited.

Conditions are independent threads: up to five operator subagents run at the same time (one per condition). A subagent never sees another condition's files, and never the other conditions' memory logs.

## Operator subagent prompt (verbatim template, experiments 3 and 4 — unchanged)

Spawned with the Agent tool, `model: haiku`, one per request file:

> You are the **experiment operator** for one manual-mode step of the claims-skill-loop experiment. Adopt `d:/Projects/SkillRL/claims-skill-loop/.claude/agents/experiment-operator-blind.md` as your operating instructions (read it first). Then read exactly one file — the request `<REQUEST_PATH>` — and write exactly one file — the response `<RESPONSE_PATH>` — as JSON conforming to the `response_schema` embedded in the request. Use only component ids and parameter options that appear in the request's `component_catalogue`; base every decision solely on the request contents; do not read or write any other file, run code, or use the network. Finish with one line naming the file you wrote and the decision you made.

Experiment 1 used the same template with `experiment-operator.md` and the session model.

Rules the lead follows:

- One subagent per request file, never reused, never given conversation context, never told which condition or task number it is beyond what the request contains.
- The lead never edits a response. A response that fails validation is logged (`operator_validation_error`) and the runner issues a new request with `validation_errors`; the lead spawns a new subagent for it.
- The lead does not read request or response contents during the run except to confirm a file exists (to avoid steering later steps); the files are inspected only after all conditions finish.
- If the session hits a rate limit mid-run, nothing is lost: checkpoints and request/response files are on disk; `advance-all` resumes after the reset.

## What the operator is shown (experiment 4, five arms)

| Arm | `plan_task` | after `evaluate_output` | `revise_plan` | `past_feedback` (cross-task memory) | after a pass |
|---|---|---|---|---|---|
| `reflection_only` | brief, catalogue, manifest summary | the 3 most severe failed checks (no literal fix) + scorecard + count of further failures | prior plan, those 3 findings, its reflection | — | — |
| `feedback_memory` | same | same | same | **yes** — every checker finding it was shown on earlier tasks, verbatim, newest first, ≤ 30 | — |
| `skill_learning` | + retrieved skills (learned in this run only; the library starts empty) | same | + retrieved skills | — (skills instead) | reflect over the whole task → propose ≤ 1 skill → validate → persist |
| `self_refine` | brief, catalogue, manifest summary | **nothing** — the operator reviews its own report and metrics (`self_evaluate`) and decides accept / revise | prior plan, its own findings | — | — |
| `self_refine_memory` | same | same (still nothing from the checker) | same | **yes** — its own review findings from earlier tasks, with each review's verdict and summary, newest first, ≤ 30 | — |

The frozen evaluator scores every attempt of every arm identically; only what is *shown* differs. The two memory logs live at `artifacts/memory/<run_id>/<condition>.jsonl`, one line per finding, written by `finalize_task` and read by `load_context`; they are committed with the run and archived by `scripts/archive_run.py`. `self_refine_memory` never sees a checker finding in its memory — only what it told itself.

## What gets recorded

- `logs/graph_events.jsonl`: `operator_request` (request path), `operator_response` (response path, SHA-256), `operator_validation_error`, plus every node transition (for `self_evaluate`: the verdict next to the frozen score it did not see).
- `logs/experiment_events.jsonl`: one `attempt` record per evaluation (`n_failed_checks`, `n_feedback_shown`, `critical_failures`, `skills_applied`) and one `done` record per task with `attempts_to_pass`, `score_by_attempt`, `self_declared_pass`, `past_feedback_count`, `stop_reason` (`passed` | `retry_budget_exhausted` | `self_accepted` | `operator_cap`), provider metadata and `freeze_sha256`.
- `logs/skill_events.jsonl`: for the memory arms, `memory_retrieved` (how many past comments were recalled before planning) and `memory_written` (how many findings the task added), alongside the skill lifecycle events.
- `artifacts/manual/<run_id>/<condition>/*.request.json|*.response.json`: the complete operator transcript, committed with the run.

## Budget expectations (recorded, not promised)

Per condition and task, five attempts at most: `plan_task` (1) + up to 4 × (`reflect_on_feedback` + `revise_plan`) for reflection_only / feedback_memory / skill_learning, or 4 × (`self_evaluate` + `revise_plan`) for self_refine / self_refine_memory; skill_learning adds `reflect_on_feedback` + `propose_skill` (+ ≤ 1 `revise_skill_proposal`) after each task. The memory arms cost no extra operator steps — recall and write are pure file operations. Hard cap `max_operator_steps_per_condition = 64` (the fixture smoke run used 24–41 over six tasks). The realised counts appear in `experiment_status.json` and the write-up.
