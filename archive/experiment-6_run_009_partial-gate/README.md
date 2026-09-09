# Archive - `run_009` (2026-09-09)

First attempt at removing the skill-proposal gate (D-25). Superseded: only the proposal prompt was changed, while the reflection prompt one step upstream still asked for lessons reusable in at least two remaining tasks, so the modelling lessons were suppressed again on T7 (reflection returned no reusable lesson). Results kept for provenance: 11 attempts over six tasks, 3 skills written (candidate keys, denial-rate denominator, synthetic-data caveat). Re-run as run_011 with both prompts in step (D-26).

## What moved

- logs/experiment_events.jsonl: moved 17 lines, kept 113
- logs/skill_events.jsonl: moved 29 lines, kept 65
- logs/graph_events.jsonl: moved 138 lines, kept 650
- logs/feedback_events.jsonl: moved 32 lines, kept 155
- logs\runs\run_009.json: moved
- logs\checkpoints\run_009.sqlite: moved
- artifacts\tasks\run_009: moved
- artifacts\manual\run_009: moved
- artifacts\memory\run_009: absent
- skills\evolved\run_009: moved
- skills/index.json: moved 3 entries, kept 2
