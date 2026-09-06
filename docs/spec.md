# Specification — claims-skill-loop (the WHAT)

**Status:** Phase 1 SDD document (A1). **Date:** 2026-09-06. **Binding inputs:** the brief incl. Addendum A and Addendum B (addenda win on conflict); `docs/LEAD_DESIGN_DECISIONS.md` §1–§15. The HOW is in `docs/plan.md`.

## 1. Research question

Does giving a claims-analysis agent **persistent, validated, reusable skills** (external procedural memory in versioned Markdown) improve the **reliability** (fewer retries, more first-attempt passes, fewer execution errors) and **quality** (rubric score against a frozen golden pack) of later tasks, compared with (a) no memory at all (`baseline`) and (b) within-task reflection only (`reflection_only`)?

## 2. Hypotheses

- **H1 (quality):** on later tasks (T4–T8) the mean rubric score is higher under `skill_learning` than under `reflection_only` and `baseline`.
- **H2 (reliability):** on later tasks `skill_learning` needs fewer retries and has a higher first-attempt pass rate.
- **H0:** no difference between conditions.

With one run per condition the study can only report **illustrative** directional evidence; no statistical significance is claimed (§14).

## 3. Scope and non-goals

**In scope**

- Eight fixed claims-analysis tasks (T1–T8) on one synthetic dataset snapshot, run under three conditions with identical configuration.
- A typed LangGraph `StateGraph` with interrupt-based manual operation, SQLite checkpointing, deterministic execution, deterministic evaluation against a frozen golden pack, and a validated skill lifecycle.
- Structured JSONL logging, an atomic experiment-status snapshot, a static dashboard, seven log-derived visuals, and a write-up populated only from logs.

**Non-goals**

- No model training, fine-tuning, RL, or weight updates of any kind.
- No live model API calls from the Python runtime; no Agent SDK; no headless-CLI bridge; no reuse of Claude Code session credentials (`docs/security-review.md`).
- No LLM-as-judge in the main evaluator.
- No model-generated code execution: the executor interprets structured plans against a fixed component catalogue.
- No claims about real-world healthcare, fraud, actuarial, or operational questions.
- No statistically powered comparison; no hyper-parameter search; no additional datasets.

## 4. Dataset and licence constraints

| Item | Requirement |
|---|---|
| Source | Hugging Face `xpertsystems/hlt008-sample` (HLT-008 Synthetic Healthcare Claims Dataset — sample) |
| Revision | pinned: `7309ddb30e67468748b7aa9182d8517fe28c2f9c` (recorded in `data/processed/manifest.json` and `config/experiment.yaml`) |
| Files | `members.csv`, `providers.csv`, `medical_claims.csv`, `pharmacy_claims.csv`, `adherence.csv` — downloaded **individually** (different schemas; never loaded as one combined table) |
| Licence | **CC-BY-NC-4.0**: attribution in `data/README.md`, `README.md`, and the write-up; non-commercial, educational use only; raw CSVs are git-ignored and re-downloadable, not redistributed |
| Integrity | SHA-256 per file in the manifest and in `config/freeze_manifest.json`; comparative runs refuse to start if any hash drifts |
| Network | one-time download only (A2); **no network access during experiment runs**, tests, evaluation, or chart generation |
| Nature | synthetic; contains no PHI; nothing derived from it is real-world evidence |
| Failure | if the dataset cannot be retrieved, record it in `docs/verification-log.md` and **stop**; never substitute a dataset without asking the user |

## 5. Protocol shared by every condition

| Parameter | Value | Source |
|---|---|---|
| Task order | T1, T2, T3, T4, T5, T6, T7, T8 | `config/tasks.yaml` |
| Seed | 42 | `config/experiment.yaml` |
| Retry budget | `max_retries = 2` (three attempts per task) | Addendum B |
| Pass criterion | all `critical` checks pass **and** `score_total ≥ pass_threshold (3.5)` | `config/rubric.yaml` |
| Operator cap | `max_operator_steps_per_condition = 40` | Addendum B |
| Rubric / goldens / tasks / data | identical frozen files, verified by `freeze_sha256` on every evaluation event | `config/freeze_manifest.json` |
| Operator | fresh, stateless Claude Code subagent per step (`experiment-operator`), model `claude-fable-5-1` | Addendum B |
| Executor | deterministic component code (`src/task_runner.py`); same plan + same data → identical outputs | LEAD §5 |

## 6. Condition definitions

All conditions share §5. Per LEAD §2 **nothing crosses tasks in graph state**; every task is a fresh graph invocation. The operator never has memory of other steps. The only difference is the route and what information may reach the operator.

| | `baseline` | `reflection_only` | `skill_learning` |
|---|---|---|---|
| Route | `load_context → plan_task → execute_task → evaluate_output → …` | same as baseline | `load_context → retrieve_skills → plan_task → …` |
| Skills shown to the planner | none | none | foundational skills + evolved skills persisted by **earlier tasks of the same run** |
| On failed attempt with retries left | `revise_plan` (sees prior plan, evaluation, feedback) | `reflect_on_feedback → revise_plan` (adds the reflection's `current_task_corrections`) | same as `reflection_only` |
| After the final attempt (pass or budget exhausted) | `finalize_task` | `finalize_task` | `reflect_on_feedback → propose_skill → (validate_skill → persist_skill)? → finalize_task` |
| **May carry across attempts** (within one task) | prior plan(s), evaluation(s), feedback, retry count | as baseline **plus** the reflection for the current task | as `reflection_only` |
| **May carry across tasks** | nothing | nothing | **only** skill files under `skills/evolved/<run_id>/` (and `skills/index.json` reuse counts); a skill persisted after task *n* is retrievable from task *n+1* |
| **May not carry** | any analysis content between tasks; any skill | any reflection or lesson beyond the current task; any skill | plans, evaluations, reflections, feedback, or operator prose between tasks; skills persisted **during** the current task |
| Skill proposal / persistence | never | never | only via validation; at most one proposal revision per task |

Notes:

- The `operator_steps_used` counter is threaded through state per condition so that the cap can be enforced; it is a scalar budget, carries no analytical content, and is not "memory".
- `skill_learning` bundles two treatments: access to the six foundational skills from T1 and the accumulation of evolved skills. Differences on T1–T3 mainly reflect the former; the learning claim rests on **evolved-skill reuse** on later tasks (§11, §14).

## 7. Task suite (fixed)

T1 dataset reconnaissance · T2 claims portfolio description · T3 provider and network patterns · T4 denial analysis · T5 fraud-pattern exploration · T6 baseline fraud model · T7 high-cost claim identification · T8 executive brief (full objectives in the brief and `config/tasks.yaml`). For every task the operator selects **plan components** and **parameter options** from a fixed catalogue that offers genuinely different analytical choices (denominators, date columns, exclusion lists, threshold sources, small-group thresholds, caveat sets). Catalogue defaults are the naive choices, never automatically the golden ones.

## 8. Evaluation

- Five dimensions scored 0–4: correctness, completeness, reproducibility, statistical discipline, communication. Dimension score = `4 × Σ(weight·passed) / Σ(weight)` (2 dp); total = mean of the five; pass = all critical checks pass and total ≥ 3.5.
- Every check is deterministic (`exact`, `tolerance`, `artifact_exists`, `field_excluded`, `contract`, `caveat_keywords`, `metric_range`, `report_structure`) and compares executor output with the frozen golden file. **No LLM judge.**
- Two different things are measured: claims **models** (predictions vs synthetic labels on held-out data, inside T6/T7) and **the agent** (its analysis vs the pre-built golden). Only the latter is the experiment's outcome.
- Every evaluation event records `evaluator_version`, `rubric_version`, `rubric_sha256`, `golden_sha256`, and `freeze_sha256`.

## 9. Stopping rules (Addendum B, binding)

1. An attempt that meets the pass criterion is finalised immediately — no further retries or plan revisions for that task.
2. `max_retries = 2` per task (three attempts).
3. In `skill_learning` a skill is proposed only when the reflection identifies a lesson reusable in **at least two remaining tasks**; otherwise the operator returns `proposal: null` and validation is skipped. At most **one** proposal revision.
4. Hard cap `max_operator_steps_per_condition = 40` (every request file written counts, re-requests included). Once reached, no further operator requests are made: remaining decisions use catalogue defaults, and affected tasks record `stop_reason = operator_cap`; the cap event appears in the write-up.
5. All three conditions always run all eight tasks — stopping rules bound the loop, never the suite.

## 10. Acceptance criteria

**A. Quality gates from the brief**

1. Dataset source, retrieval details, attribution, and licence are documented (`data/README.md`).
2. Six foundational skills exist and pass the validator.
3. The LangGraph topology compiles for each condition, routes correctly (tests), and is rendered.
4. Frozen tasks and rubric exist before comparative execution.
5. The three conditions share identical task definitions and configuration (asserted by test and by `freeze_sha256` in every event).
6. All JSONL logs are valid and carry the required metadata (`validate_logs()` passes).
7. The agent tracker is maintained throughout the build.
8. Dashboard and figures are generated from logs with no hard-coded outcomes.
9. Joins check cardinality, unmatched keys, and row-count changes.
10. Predictive tasks enforce train/test isolation and exclude ID and target-derived leakage fields.
11. Tests pass, or failures are documented without claiming success.
12. `anthropic_api` mode cannot start without an explicit `ANTHROPIC_API_KEY` (fail-closed test).
13. The final write-up states that data and findings are synthetic and illustrative.

**B. Golden-pack gates (Addendum A)**

14. Goldens are built by independent reference code (`src/build_goldens.py`, pandas + manifest only, no import of executor code) and are deterministic (`--check` reproduces them).
15. Golden values are **reviewed by the user** (Phase 1.5 checkpoint) before freezing.
16. `config/freeze_manifest.json` hashes `tasks.yaml`, `rubric.yaml`, every golden file, and every raw data file **before** any comparative run; `init` in manual mode refuses to start on drift.

**C. Manual-mode gates (Addendum B)**

17. Default mode is `manual`; the runtime makes no model calls in `manual` or `stub` mode (`langchain_anthropic` is imported only inside the `anthropic_api` branch).
18. Operator files are JSON, validated against the response schema; invalid responses are logged as `operator_validation_error` and re-requested, never silently edited.
19. Every event records `provider_mode`, `operator`, `model_identifier`, and the response file SHA-256.
20. A full `stub` run passes end-to-end (all conditions, all tasks) before the first `manual` run.
21. `logs/experiment_status.json` and the dashboard show live progress (current task/node, pending request, steps used vs cap, rough ETA) during manual runs.

**D. Documentation gates**

22. `docs/verification-log.md` contains only checks that were actually run; limitations are stated.
23. The write-up's numbers trace to named log files and artifacts.

## 11. Definition of a "validated useful skill"

A skill is **validated** when `skill_validator.validate()` returns `accepted` (schema and required sections present, safe guidance, general rather than a task restatement, provenance citing task and feedback IDs, token-Jaccard similarity to every existing skill < 0.6, applicable to ≥ 2 remaining tasks) and it is persisted immutably under `skills/evolved/<run_id>/`.

A validated skill is **useful** when, on at least one **later** task of the same run, it was retrieved (`skill_retrieved`) **and** listed in that task's plan `skills_applied` (`skill_reused`, `record_reuse`). Reuse counts come only from these events.

Illustrative utility deltas per skill (reported, never proven): mean `score_total` and retries on the tasks where the skill was applied versus the same tasks in `reflection_only`. A persisted skill that is never retrieved is reported as **potential bloat**; skill count is never a success metric.

## 12. Outcome measures (computed only from logs)

Per condition and task: final `score_total` and dimension scores; `passed`; first-attempt pass; retries; execution errors; operator steps used; `stop_reason`. Per run: skills proposed / accepted / rejected / persisted / retrieved / reused; skill-utility deltas; operator validation errors. Later-task aggregates (T4–T8) drive H1/H2.

## 13. What this experiment is — and is not

- It demonstrates **external procedural memory in Markdown**, retrieved into the planner's context. It is **not** model self-training, weight updates, or AGI.
- The Python runtime makes **no model API calls**. LLM decision steps are performed by **stateless Claude Code subagents** (Claude Fable 5.1) in manual mode inside the author's Claude Code session; the runtime pauses on interrupts and resumes from checkpoints. Write-up wording (Addendum B): *"LLM steps were performed by Claude (Fable 5.1) subagents inside the author's Claude Code session in a human/agent-in-the-loop manual mode; the Python runtime made no model API calls."*
- `stub` mode is a deterministic non-LLM simulation used for tests and pipeline demos; its results are never reported as LLM results.
- All data and findings are **synthetic and illustrative**.

## 14. Limitations

- One run per condition unless repeated; comparisons are illustrative, not significant.
- The operator is a single model (Claude Fable 5.1); results say nothing about other models.
- The catalogue bounds what the agent can do: quality differences reflect *choices*, not free-form analysis.
- `skill_learning` also grants foundational-skill access (§6 note); a `foundational_only` control was considered and deferred (`docs/decision-log.md`).
- The evaluator is deterministic; prose quality is checked only structurally (keywords, references, sections).
- Manual mode is slow (one subagent per step) and bounded by the operator cap, which may truncate learning on late tasks.
- Data are synthetic; nothing generalises to real claims operations.
