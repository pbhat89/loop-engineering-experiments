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

## D-13 · 2026-09-07 · `foundational_only` control implemented as an opt-in fourth condition (lead)

- **Alternatives:** keep the brief's three conditions only (D-11 deferred the control); run `skill_learning` twice with and without foundational skills.
- **Rationale:** `skill_learning` bundles two effects — access to the curated foundational library and accumulation of evolved skills. A condition that retrieves foundational skills but never reflects across tasks, proposes, or persists separates the two at the cost of ~8–16 extra operator steps. Implementing it is cheap (routing reads `SKILL_RETRIEVING_CONDITIONS`; `retrieve_skills` filters to `kind == foundational`), so the choice of whether to spend the operator budget on it is left to the user at the Phase 1.5 checkpoint.
- **Impact:** `CONDITIONS` gains `foundational_only`; `DEFAULT_CONDITIONS` stays the brief's three; `designed_topology()["per_condition"]`, `config/graph.yaml` and tests cover it; the spec's limitation note about the confound stands unless the control is run.

## D-14 · 2026-09-07 · `config/graph.yaml` v2 mirrors the single compiled graph (lead correction of A1's v1)

- **Alternatives:** compile one graph per condition as v1 documented; keep v1 and let the test skip the mismatch.
- **Rationale:** the implementation is one `StateGraph` whose routers read `state["condition"]` and the `next_route` decision written by `evaluate_output` / `validate_skill`; a null skill proposal is rejected inside `validate_skill` (there is no `route_after_proposal`), and the operator cap suppresses further retries because a retry needs an operator. Documentation must describe what runs.
- **Impact:** `graph.yaml` now lists the edge union with labels, four routers, `per_condition` node subsets (incl. `foundational_only`) and the termination rules; `tests/test_graph_routes.py::test_graph_yaml_mirrors_designed_topology_and_experiment_config` asserts it equals `designed_topology()` and `experiment.yaml`.

## D-15 · 2026-09-07 · Operator-step cap raised from 40 to 64 per condition (lead)

- **Alternatives:** keep 40 and accept `operator_cap` stops in `skill_learning`; remove the cap.
- **Rationale:** the stub end-to-end run (`stub_001`) used 38 of 40 steps in `skill_learning` with one retry per task. The manual worst case per task is 8 steps (plan, 2 × (reflect + revise), reflect, propose, revise proposal) → 64 for eight tasks. The cap is a safety net; the stopping rule that ends the loop is "pass → finalize". A cap that fires routinely would truncate the learning path and bias the comparison.
- **Impact:** `config/experiment.yaml`, `config/graph.yaml` (asserted equal by test), `docs/OPERATOR_PROTOCOL.md` and the brief's Addendum B now say 64; existing stub logs keep their recorded cap of 40.

## D-16 · 2026-09-07 · Operator requests now list remaining tasks with titles (lead, applied mid-run after T1)

- **Alternatives:** keep ids only; postpone until a second run.
- **Rationale:** the first `reflect_on_feedback` operator noted it could not target lessons at specific future tasks because requests carried only `remaining_task_ids`. Task titles are public parts of the fixed suite, identical for every condition and carry no golden information, so adding them is fairness-neutral and improves the specificity of proposed skills — the quantity the study measures.
- **Impact:** `Services.task_titles` + `remaining_tasks: [{task_id, title}]` in every request payload from `run_001` T1 onwards (all conditions, at the same point in the suite); recorded here and in the write-up's limitations.

## D-17 · 2026-09-07 · Model-metric sanity ranges relaxed in the golden pack (lead)

- **Alternatives:** keep `roc_auc ≥ 0.5` and `pr_auc ≥ prevalence` as A3 first wrote them; drop the range checks.
- **Rationale:** A6 measured ROC-AUC 0.499 / 0.498 / 0.515 for leakage-free logistic / random-forest / gradient-boosting models on the synthetic `fraud_label` — the label is essentially unpredictable without leakage. A floor at chance would fail honest plans on rounding noise while rewarding leaky ones. The ranges are sanity checks, not performance bars; the discriminating checks in T6/T7 are leakage exclusion, stratification, train-only fitting/thresholds and prevalence reporting.
- **Impact:** `src/build_goldens.py` writes `roc_auc ∈ [0.40, 1.0]` and `pr_auc ≥ 0.5 × prevalence_test` (T6) / `0.5 × positive_rate_test` (T7) via a `{ref, factor}` bound that `src/evaluator.py::_check_range` now resolves; goldens rebuilt, `--check` clean, then frozen and reviewed by the user.

## D-18 · 2026-09-07 · Experiment 2: deterministic rule learner (`rule_learner` mode); experiment 1 archived

- **Context:** experiment 1 (`run_001`) was a clean null — a Fable 5.1 stateless operator reading briefs that stated the house conventions passed every task first attempt, issued no feedback, and therefore produced no grounded skills (see `archive/experiment-1_run_001/`).
- **Alternatives:** (a) a weaker LLM operator with blinded briefs; (b) a batch rule-induction micro-loop on labels; (c) the rule learner chosen here. The user chose (c) first for cost (zero model calls) and certainty of exercising the retry → reflect → persist → reuse path; (a) remains a follow-up.
- **Decision:** add `src/rule_learner.py` — a planner that starts every task from the catalogue's textbook defaults and changes a choice only on evaluator feedback (current task) or on a retrieved skill's machine-readable convention (`param:<name>=<value>`, `list:<name>±=<value>`, `component:<id>`), generalised **by parameter name**. It proposes one skill per task containing only conventions not already held by existing skills, with feedback ids as provenance. Foundational prose skills are inert for it. New runtime mode `rule_learner` (`rule-learner-v1` / `deterministic-rule-learner`), freeze required like manual runs; `run-auto` CLI. Proposal payloads now include existing skills' `procedure`/`required_checks` so duplicates can be avoided before validation. `retrieval_k` raised 6 → 8 so evolved skills are not crowded out by the six foundational ones (retrieval is still tag/keyword ranked and logged).
- **Impact:** the same frozen suite, goldens and rubric; the learner's "intelligence" is deliberately minimal, so results demonstrate loop mechanics and memory transfer, not model reasoning — the write-up must say so. Over-generalised conventions (e.g. a feature list learned on T6 applied to T7) are expected and reported as observed.

## D-19 · 2026-09-07 · Evaluator 1.1 (caveat scope) and learner removal rule; run_002 superseded by run_003

- **Finding:** in `run_002` the baseline condition scored higher than `reflection_only` on T7's first attempt although both ran the identical naive plan. Cause: the `caveat_keywords` check scanned the whole report and the golden's `model_limitations` keywords include "baseline", which matched the condition name inside the report's own artifact paths. A second issue: the rule learner derived list *removals* from every recommended list (e.g. dropping `descriptive_only` because T3's golden did not list it), although caveat checks are "at least these" requirements.
- **Decision:** `EVALUATOR_VERSION = "1.1"` — caveat keywords are matched only inside sections whose heading mentions caveats/limitations, falling back to the full text with artifact paths and `[source: …]` citations removed. The learner learns removals only from exclusion-type feedback (issue/check names containing leak/exclud/prohibit/protected). Neither change touches `rubric.yaml`, the goldens or the freeze; `run_002` is archived under `archive/experiment-2_run_002_pre-fix/` and `run_003` is the reported run.
- **Impact:** conditions are graded identically regardless of their names; the learner no longer un-learns harmless caveats; every evaluation event now records `evaluator_version 1.1`.

## D-20 · 2026-09-07 · Experiment 2 archived; the loop must be seen to iterate

- **Finding:** `run_004` demonstrated cross-task memory (first-attempt mean 1.53 → 2.07) but every task still converged after exactly one retry, because the evaluator handed back the complete list of failed checks with the literal parameter fix attached. A verification loop that always closes on the first retry is a good error message, not loop engineering; and the planner was a deterministic rule learner, so nothing in the loop reasoned.
- **Decision:** archive `run_004` unchanged under `archive/experiment-2_run_004/` (logs, checkpoints, task artifacts, evolved skills, write-up v2, article v1) with `scripts/archive_run.py`, and redesign the run rather than re-run it.
- **Impact:** the evolved-skill index is empty again; the goldens and rubric are unchanged by this decision (see D-21 for what did change).

## D-21 · 2026-09-07 · Experiment 3 design: blinded four-task suite, capped fix-free feedback, five attempts, empty library, Haiku operator, `self_refine` arm

- **Alternatives:** keep the rule learner and only cap the feedback; keep eight tasks; keep the curated foundational skills in the library; a fourth `baseline` arm.
- **Decisions:**
  1. **Four tasks in the order T2 → T4 → T3 → T7** (portfolio description, denial analysis, provider/network patterns, high-cost model). Their briefs are rewritten the way a sponsor would ask — no denominators, small-group thresholds, train-only rules or required caveats. The rubric, goldens and remaining briefs are byte-identical to the experiment-1/2 pack except for item 5.
  2. **Feedback cap:** after each attempt the operator sees only the **three most severe** failed checks (critical first, then rubric weight, then rubric order), the scorecard, and a count of further failures. `related_components` — the literal component/parameter fix — is withheld (`reveal_fixes: false`). Fixture and rule-learner modes keep the literal fix because they apply it by construction.
  3. **Five attempts** (`max_retries: 4`); the stopping rules are otherwise unchanged (pass → stop; cap 64 operator steps).
  4. **Empty starting library** (`foundational_skills: false`): every skill `skill_learning` retrieves was learned inside the run, so the comparison is learned memory vs none, not curated library vs none.
  5. **T7 ROC-AUC target band [0.60, 0.95]** instead of the floor 0.40: leakage-free models reach 0.89–0.91 on this data, amount features push it to 0.997–1.0, so a first model above 0.95 is treated as evidence of leakage rather than skill. `build_goldens --check` clean; new freeze `64b7292e8214…`.
  6. **Operator:** a fresh, stateless Claude Code subagent per request, `model: haiku` (Claude Haiku 4.5), using `.claude/agents/experiment-operator-blind.md`, which carries no list of analytical conventions. Recorded as `model_identifier: claude-haiku-4-5-20251001` on every event.
  7. **Conditions:** `reflection_only` (verifier feedback, no memory), `skill_learning` (verifier feedback + learned skills), and a new **`self_refine`** arm in which the frozen evaluator scores every attempt for the record but the operator never sees it — it reviews its own report and metrics (`self_evaluate` node) and decides accept/revise (Madaan et al., *Self-Refine*, 2023). `baseline` is not run (it differs from `reflection_only` only by the reflection step).
- **Rationale:** the literature the study cites separates within-rollout refinement from cross-task accumulation and puts the evaluator outside the loop; the three arms map onto exactly those distinctions, and capped diagnostic feedback is what makes score-versus-attempt curves informative.
- **Impact:** graph v3 (`self_evaluate` node, `route_after_self_evaluation`), evaluator 1.2 (strips the new condition name; scoring unchanged), new experiment records (`attempts_to_pass`, `score_by_attempt`, `n_feedback_shown`, `self_declared_pass`), new tests; the experiment-3 comparison is not comparable number-for-number with experiments 1–2 (different briefs, tasks, feedback and freeze) and the write-up must say so.
