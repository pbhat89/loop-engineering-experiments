# Archive - `run_011` (2026-09-09)

Second attempt at removing the skill-proposal gate. Reflection and proposal prompts were in step (D-26) and the reflection did produce reusable lessons on T3 and T7, but the validator's generality check still treated 'applicable_task_ids names a single task' as evidence of a one-off, so both proposals were rejected and the modelling lesson was lost a third time. Results kept for provenance: 12 attempts over six tasks, 4 skills written. Re-run as run_012 with that heuristic disabled when the gate is off.

## What moved

- logs/experiment_events.jsonl: moved 18 lines, kept 113
- logs/skill_events.jsonl: moved 26 lines, kept 65
- logs/graph_events.jsonl: moved 154 lines, kept 650
- logs/feedback_events.jsonl: moved 32 lines, kept 155
- logs\runs\run_011.json: moved
- logs\checkpoints\run_011.sqlite: moved
- artifacts\tasks\run_011: moved
- artifacts\manual\run_011: moved
- artifacts\memory\run_011: absent
- skills\evolved\run_011: moved
- skills/index.json: moved 4 entries, kept 2
