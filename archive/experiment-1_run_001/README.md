# Archive — experiment 1 (`run_001` manual run and `stub_001` simulation), 2026-09-06/07

Moved here unchanged when the repository was reset for experiment 2. Nothing in this folder is read by the current code.

## What it was
The brief's original design: three conditions (baseline, reflection_only, skill_learning) over the frozen eight-task suite, with every LLM-decision step answered by a fresh, stateless Claude Fable 5.1 subagent inside the author's Claude Code session (manual mode, no API calls). `stub_001` is the deterministic fixture run used to prove the pipeline end to end.

## What happened
- `run_001`: all three conditions passed all eight tasks on the first attempt at 4.00/4.00, 0 retries, 37 operator steps (8 / 8 / 21). The reflection path never ran (no retries). All five skill proposals were rejected by the validator for empty feedback provenance — no evaluator feedback was ever issued — so 0 evolved skills were persisted. A ceiling effect: a Fable-class planner reading briefs that stated the conventions never failed, and the loop only learns from failure.
- `stub_001`: the deterministic fixture showed every lifecycle stage working (first-attempt means 1.62 / 1.57 / 1.61; one revision per task; 5 skills persisted; 10 reuse events) but its per-component skill tokens barely transferred between tasks.

The full write-up of that run is `docs/writeup_run_001.md` here; the decision record is D-01…D-17 in `docs/decision-log.md` (kept live).

## Contents
- `logs/` — the four JSONL logs, `experiment_status.json`, `runs/run_001.json`, `runs/stub_001.json`
- `artifacts/manual/run_001/` — all 37 operator request/response pairs
- `artifacts/tasks/{run_001,stub_001}/` — every task attempt's metrics, reports and figures
- `artifacts/figures/`, `artifacts/graphs/skill_lifecycle_graph.png`, `artifacts/reports/run_summaries.json`
- `skills/evolved/stub_001/`, `skills/index.json`

The golden pack, task suite, rubric and freeze manifest were **not** changed and are not archived: experiment 2 evaluates against the same frozen reference.
