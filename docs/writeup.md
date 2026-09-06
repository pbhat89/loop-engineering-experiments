# Write-up — outline (populated only from recorded logs and generated artifacts)

**Status:** outline (A1, 2026-09-06). Every bracketed placeholder is filled in Phase 5 **from the named log or artifact only**; no number may appear here that cannot be traced to `logs/*.jsonl`, `logs/experiment_status.json`, `artifacts/figures/`, `artifacts/graphs/`, or `skills/`. If a run did not happen or a figure is missing, say so.

## 1. Title and hook

- Working title: *Teaching an agent procedures, not answers: a LangGraph loop that learns Markdown skills from a frozen golden pack.*
- Hook (one paragraph): the mechanism in plain words — plan → execute → evaluate against goldens → reflect → skill → retrieve. [No results here.]

## 2. What was built (from `docs/plan.md`, `artifacts/graphs/langgraph_topology.png`)

- Typed LangGraph `StateGraph`, one compiled graph per condition, interrupts + SQLite checkpoints.
- Deterministic executor over a fixed component catalogue; deterministic evaluator; golden pack frozen by hash.
- Skill lifecycle: propose → validate → persist (run-scoped, immutable) → retrieve → reuse.
- Figure: topology diagram, labelled *designed workflow*.

## 3. How the LLM steps happened (mandatory wording, Addendum B)

> LLM steps were performed by Claude (Fable 5.1) subagents inside the author's Claude Code session in a human/agent-in-the-loop manual mode; the Python runtime made no model API calls.

- Operator steps used per condition: [from `logs/experiment_status.json` → `operator_steps_used` / `operator_steps_cap`].
- Operator validation errors: [count of `operator_validation_error` in `logs/graph_events.jsonl`].
- Whether the operator cap was hit and where: [tasks with `stop_reason = operator_cap` in `logs/experiment_events.jsonl`].

## 4. The frozen target (from `config/freeze_manifest.json`, `goldens/`)

- Dataset revision, file hashes, `freeze_sha256`: [values].
- Golden values reviewed by the user on [date from `docs/verification-log.md`].
- Statement: *the agent was measured on whether it produced the expected claims metrics, artifacts, modelling safeguards, and caveats — not on whether it thought its own answer was good.*

## 5. Results — quality (from `logs/experiment_events.jsonl`; figure `artifacts/figures/learning_curve.png`, `rubric_heatmap.png`)

- Table: final `score_total` per task × condition [populated from final records, `status = done`].
- Later-task means (T4–T8) per condition [computed; shown with the caveat "one run per condition, illustrative"].
- Dimension heatmap commentary [only patterns visible in the heatmap; no causal language].

## 6. Results — reliability (from `logs/experiment_events.jsonl`; figure `artifacts/figures/reliability_curve.png`)

- First-attempt pass rate per condition [from `first_attempt_pass`].
- Retries and execution errors per task × condition [from `attempt`, `execution_errors`].

## 7. Results — skills (from `logs/skill_events.jsonl`, `skills/evolved/<run_id>/`; figures `skill_accumulation.png`, `skill_utility.png`, `artifacts/graphs/skill_lifecycle_graph.html`)

- Skills proposed / accepted / rejected (with rejection reasons) / persisted [counts by `event_type` and `decision`].
- Validated **useful** skills (retrieved and listed in `skills_applied` on a later task) [list with `reuse_count`].
- Skills never retrieved — reported as potential bloat [list].
- Illustrative utility deltas per skill vs `reflection_only` on the same tasks [from `skill_utility.png` source data].
- One concrete example: the lesson, the feedback that triggered it, the task where it was reused [quote skill file + event ids].

## 8. What did not work / surprises (from `docs/verification-log.md`, `logs/feedback_events.jsonl`)

- Feedback that was incorporated but did not resolve the check [from `feedback_update` records].
- Any failed tests or documented limitations [verbatim from the verification log].

## 9. Limitations (from `docs/spec.md` §14 — restate, do not soften)

- Single run per condition; illustrative; one operator model; catalogue-bounded choices; `skill_learning` also includes foundational access; deterministic (structural) evaluation of prose; synthetic data.

## 10. Reproduce it

- Commands from `README.md` (bootstrap, run-stub, init/advance/resume, verify); dataset revision and licence; `freeze_sha256`.

## 11. Draft LinkedIn post (≤ 1,300 characters; only claims supported by §5–§7)

[Placeholder — written last, from the populated sections above. Must include: synthetic data, no API calls / Claude Code subagents as operator, illustrative single-run comparison, link to repo.]

## Appendix — evidence index

| Claim in write-up | Source file(s) | Field(s) |
|---|---|---|
| [claim] | [`logs/...`] | [field] |
