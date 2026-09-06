# Decision log — claims-skill-loop

Format: date · decision · alternatives considered · rationale · impact. Binding design decisions live in `docs/LEAD_DESIGN_DECISIONS.md`; this log records why they were taken and what A1 formalised or deferred. Later decisions are appended, never rewritten.

## D-01 · 2026-09-06 · Dataset: HLT-008 synthetic claims sample (`xpertsystems/hlt008-sample`)

- **Alternatives:** Synthea-derived CMS-style synthetic data; Kaggle insurance-claims tables; generating our own synthetic frames.
- **Rationale:** the brief names it; it is synthetic (no PHI), multi-table (members, providers, medical and pharmacy claims, adherence) with adjudication, denial, and fraud-label fields — enough to exercise joins, denominators, leakage, and imbalance; hosted on Hugging Face with a pinnable revision (`7309ddb30e67468748b7aa9182d8517fe28c2f9c`) and per-file download.
- **Impact:** CC-BY-NC-4.0 → attribution everywhere, non-commercial educational framing, raw CSVs git-ignored. Files are downloaded individually (different schemas). If retrieval fails the build stops and asks the user rather than substituting data.

## D-02 · 2026-09-06 · Initial library of exactly six foundational skills

- **Alternatives:** start with an empty library (purest learning signal); a large hand-written library (best task performance).
- **Rationale:** the brief fixes the six (data contract, safe joins, descriptive summary, categorical/numeric analysis, reproducible analysis, evaluation and charting). They encode procedure, not answers, and give retrieval something to rank from T1.
- **Impact:** `skill_learning` bundles foundational access with evolved-skill accumulation (spec §6 note). A `foundational_only` control was considered and **deferred** (D-11). Foundational skills must pass the same validator as evolved ones.

## D-03 · 2026-09-06 · LangGraph `StateGraph` with `interrupt()` and SQLite checkpointing

- **Alternatives:** a plain Python loop with explicit state dicts; LangGraph without a checkpointer (stub-only); a custom file-backed checkpoint.
- **Rationale:** the manual operator needs pause/resume across processes — LangGraph's `interrupt()` + `Command(resume=…)` with `SqliteSaver` provides exactly that locally with no external service; a typed `StateGraph` keeps routes explicit and testable; one thread per task makes "nothing crosses tasks" structural.
- **Impact:** dependency on `langgraph-checkpoint-sqlite`; nodes must be re-execution-safe (side effects after the last interrupt); thread id `<run_id>:<condition>:<task_id>`; checkpoint DB under `logs/checkpoints/`.

## D-04 · 2026-09-06 · Runtime boundary: manual operator mode, no API (revision of the brief)

- **Alternatives:** (a) `anthropic_api` with a user-supplied key; (b) an Agent SDK integration; (c) a headless-CLI bridge that calls Claude Code from Python; (d) the brief's original combined `manual_or_stub` default (superseded by Addendum B).
- **Rationale:** the user does not want API usage and a subscription does not include API billing; (b) and (c) would reuse session credentials, which the brief forbids; the user wants to keep working in the session and watch progress. Splitting `manual_or_stub` into `manual` (interrupts + stateless subagent) and `stub` (fixtures) makes the two behaviours distinct and honestly labelled. `anthropic_api` remains as a fail-closed adapter for completeness only.
- **Impact:** one fresh `experiment-operator` subagent per request (statelessness prevents cross-task contamination); JSON request/response files under `artifacts/manual/`; every event records `provider_mode: manual`, `operator: claude-code-subagent`, `model_identifier: claude-fable-5-1`, and the response SHA-256; manual runs are slow and bounded by the operator cap; write-up wording fixed by Addendum B. `.env.example` and the dashboard footer still mention the superseded mode name — flagged to L0/A5.

## D-05 · 2026-09-06 · Golden evaluation pack built and frozen in Phase 1.5

- **Alternatives:** evaluator computes reference values at evaluation time from the executor's own tables; LLM judge; goldens produced by the executor on a "reference plan".
- **Rationale:** avoids the circular experiment (agent grades itself against its own answer); independent reference code (pandas + manifest only, never importing executor code), a user review checkpoint, and hashes in `config/freeze_manifest.json` make the target fixed before any comparative run.
- **Impact:** new phase between data profiling and Phase 2; A3 owns `build_goldens.py` and A6 owns the executor so the two are built independently; `init` refuses to run on hash drift; every evaluation event carries `freeze_sha256`.

## D-06 · 2026-09-06 · Deterministic evaluator; no LLM judge

- **Alternatives:** LLM-as-judge for prose dimensions; hybrid with rule checks plus a model score.
- **Rationale:** zero cost, reproducibility, and no dependence on a model for the outcome metric; the golden pack makes exact/tolerance/artifact/contract/keyword checks sufficient for this compact study.
- **Impact:** communication quality is judged structurally (required sections, caveat keywords, artifact references, forbidden causal phrasing); this is a stated limitation.

## D-07 · 2026-09-06 · Run-scoped evolved skills: `skills/evolved/<run_id>/`

- **Alternatives:** the brief's flat `skills/evolved/`; a database-backed store.
- **Rationale:** flat storage would let a stub run or an earlier manual run leak skills into a later run's retrieval; run scoping keeps each run's memory isolated while remaining plain Markdown files.
- **Impact:** `SkillStore(root, run_id)` filters evolved skills by run; ids `evolved_<run_id>_<nnn>`; `skills/index.json` remains the mutable reuse index. Deliberate deviation from the brief's layout, recorded here.

## D-08 · 2026-09-06 · Roster extension: A6 analysis engineer and the stateless `experiment-operator`

- **Alternatives:** A3 builds both goldens and executor; a single long-lived operator conversation answering all steps.
- **Rationale:** independence between goldens and executor (D-05) requires separate owners; a stateful operator would carry lessons between tasks and contaminate `baseline`/`reflection_only`, so the operator is a fresh subagent per step with Read/Write tools only.
- **Impact:** seven agent definitions under `.claude/agents/`; at most five build agents concurrently and at most three operator subagents in flight; the lead orchestrates advance → spawn → resume and never edits responses.

## D-09 · 2026-09-06 · Stopping rules (Addendum B)

- **Alternatives:** unlimited retries until pass; a fixed number of operator steps per task; stopping the whole suite once a condition "looks good".
- **Rationale:** the user asked for a limit "once optimal performance is received" while keeping conditions comparable: pass → finalise immediately; `max_retries = 2`; skill proposals only for lessons reusable in ≥ 2 remaining tasks; ≤ 1 proposal revision; hard cap of 40 operator steps per condition; all conditions always run all eight tasks.
- **Impact:** bounded operator effort and wall-clock time; a capped condition finishes with catalogue defaults and `stop_reason = operator_cap`, which the write-up must show; retry counts remain comparable because routing does not depend on the cap.

## D-10 · 2026-09-06 · uv-managed environment: Python 3.12, pandas 3.0.5, scikit-learn 1.9.0, langgraph 1.2.11

- **Alternatives:** pip + venv with loose pins; conda; older pins (pandas 2.x, scikit-learn 1.6).
- **Rationale:** `uv.lock` gives a reproducible resolution with one command (`uv sync --extra dev`); current stable versions of the stack (langchain-core 1.6.2, langgraph-checkpoint-sqlite 3.1.1, pydantic 2.13.5, matplotlib 3.11.1, networkx 3.6.1, pytest 9.1.1) avoid known deprecations.
- **Impact:** analyses must follow pandas 3 semantics (copy-on-write, default string dtype); `uv run` prints a harmless `VIRTUAL_ENV` mismatch warning in this shell; `langchain-anthropic` stays an uninstalled optional extra.

## D-11 · 2026-09-06 · Deferred: `foundational_only` control condition

- **Alternatives:** add a fourth condition (foundational retrieval, no skill creation) to separate the two treatments bundled in `skill_learning`.
- **Rationale:** it would add 8 more tasks of manual operator work to a compact study; the primary learning claim rests on evolved-skill reuse, which the logs isolate (`skill_reused` events for `evolved_*` ids).
- **Impact:** stated as a limitation in `docs/spec.md` §14; may be added in a later run without changing the graph (it is the `skill_learning` route with `propose_skill` disabled).

## D-12 · 2026-09-06 · A1 formalisations pending L0 confirmation

Recorded in `docs/plan.md` and marked **(A1 formalisation)**: `analysis_plan` typed `dict | None` (brief said `str | None`; LEAD §4 makes plans structured); routers `route_after_reflection`, `route_after_proposal`, `route_after_validation`; ≤ 2 validation re-requests then catalogue-default fallback; `operator_steps_used` counts every request file including re-requests; `execution_timeout_seconds` lives in `config/graph.yaml` (LEAD §12 fixes the `experiment.yaml` key list); freeze-manifest JSON shape and `freeze_sha256 = sha256_file(manifest)`; `logs/runs/<run_id>.json` run metadata; dropped-`skills_applied` handling; feedback `incorporated`/`resolved` rules; empty-dimension handling in scoring; `feedback_update` records. Any of these can be overridden by L0 without changing the spec.
