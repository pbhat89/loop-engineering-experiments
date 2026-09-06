# Idea — claims-skill-loop

**Status:** Phase 1 SDD document (A1). **Date:** 2026-09-06. **Sources:** the project brief incl. Addendum A (golden pack) and Addendum B (manual operator, stopping rules); `docs/LEAD_DESIGN_DECISIONS.md`.

## One line

A small, reproducible LangGraph loop in which a claims-analysis agent is scored against a **frozen golden pack**, reflects on the evaluator's feedback, distils reusable lessons into **versioned Markdown skills**, and retrieves those skills on later tasks — so that later tasks need fewer retries and score higher.

## Audience

Technical LinkedIn readers interested in agentic systems, reliability engineering, and context engineering. They want to see the mechanism (typed state, routes, deterministic evaluator, skill lifecycle), the evidence (structured logs and charts generated only from those logs), and the honest limits.

## What is demonstrated

External, versioned **procedural memory** stored as Markdown skill files — not model-weight training, not fine-tuning, not a "self-improving model". The model is the same at every step; what changes between tasks is the set of validated skill files the planner is shown. Learning is therefore inspectable (`skills/evolved/<run_id>/`), auditable (`logs/skill_events.jsonl`), and revertible (delete a file).

## User story

> "As an analyst, I want an agent to retain reliable claims-analysis procedures across tasks so later analysis is more reproducible and needs fewer retries."

## The loop for one task

```text
plan (operator chooses components + parameters from a fixed catalogue)
  → execute (deterministic pandas / scikit-learn code; never model-generated code)
  → evaluate (deterministic checks against the frozen rubric + golden file)
  → pass: finalise immediately
  → fail: reflect (not in baseline) → revise plan → re-execute, at most 2 retries
  → skill_learning only: propose a reusable skill (only if it helps ≥ 2 remaining tasks)
        → validate (schema, safety, generality, provenance, duplicates) → persist
        → retrievable from the next task onward
```

## Three comparable conditions

`baseline`, `reflection_only`, `skill_learning` run the same eight tasks (T1–T8) in the same order with the same data snapshot, rubric, golden pack, seed, retry budget, and operator cap. The only difference is what may carry across attempts and across tasks (precise definitions in `docs/spec.md` §6).

## How the LLM steps happen — no API

The Python runtime makes **no model API calls**. At each decision node (`plan_task`, `revise_plan`, `reflect_on_feedback`, `propose_skill`, `revise_skill_proposal`) the graph pauses on a LangGraph `interrupt()` with a SQLite checkpoint, writes a JSON request under `artifacts/manual/`, and a **fresh, stateless Claude Code subagent** (Claude Fable 5.1, tools Read/Write only) writes exactly one JSON response. Because the operator has no memory across steps, the only cross-task memory available in `skill_learning` is the skill files — the baseline cannot be contaminated by an operator that "remembers".

## Why goldens come first

The golden pack (`goldens/`) is built once by independent reference code, reviewed by the user (Phase 1.5 checkpoint), and frozen by hash (`config/freeze_manifest.json`) before any comparative run. The agent is graded against a pre-built answer, never against its own output.

## Planned visuals (all generated from logs, missing data shown as missing)

| # | Visual | Location |
|---|---|---|
| 1 | LangGraph topology — labelled *designed workflow* | `artifacts/graphs/langgraph_topology.png` |
| 2 | Learning curve — rubric score by task × condition | `artifacts/figures/learning_curve.png` |
| 3 | Reliability curve — retries and execution errors by task × condition | `artifacts/figures/reliability_curve.png` |
| 4 | Skill accumulation — foundational and evolved skills over time | `artifacts/figures/skill_accumulation.png` |
| 5 | Skill utility — reuse count and illustrative score/retry delta per skill | `artifacts/figures/skill_utility.png` |
| 6 | Observed skill-lifecycle graph — task → feedback → skill → later retrieval/reuse | `artifacts/graphs/skill_lifecycle_graph.html` |
| 7 | Rubric heatmap — dimension scores by task × condition | `artifacts/figures/rubric_heatmap.png` |
| 8 | Active-agent tracker and live experiment status | `artifacts/dashboard/progress.html` |

## What success looks like

- All three conditions complete all eight tasks; every attempt, route, evaluation, feedback item, and skill event is logged with provider mode, operator, model identifier, and freeze hashes.
- At least one evolved skill passes validation, is retrieved on a later task, and is listed in that task's `skills_applied` (a *validated useful skill*, `docs/spec.md` §11).
- The write-up reports comparisons as **illustrative** (one run per condition), populated only from the recorded logs and artifacts.

## What this is not

Not medical, actuarial, fraud, underwriting, pricing, adjudication, legal, regulatory, or operational evidence. The data are synthetic (HLT-008 sample, CC-BY-NC-4.0). The study is compact and unpowered; it demonstrates a mechanism, not a statistically significant effect.
