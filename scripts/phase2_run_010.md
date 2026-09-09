# Phase 2 checklist — `run_010`, the held-out test of experiment 6 (D-25)

Apply this **after `run_009` has finished** (every task of `skill_learning` reports `done` in
`uv run python -m src.run_experiment status --run-id run_009`). Phase 1 (`run_009`) re-ran the six-task
learning suite with the skill-proposal gate removed; phase 2 re-runs the D-24 held-out test seeded from it,
so the only difference from `run_008` is the library `run_009` built.

Nothing here changes the frozen material: `config/tasks.yaml`, `config/rubric.yaml`, the goldens and the raw
data are untouched, so `freeze_sha256` must still read `bab215a5fbcc…`. Do **not** `init` any of this yet.

## 1. Edit `config/experiment.yaml`

Set exactly these keys; leave every other key as it stands after phase 1.

| Key | Value | Note |
|---|---|---|
| `conditions` | `[skill_learning]` | the skills arm alone; run_008 supplies the cold and raw-memory comparisons |
| `task_order` | `[T11, T12, T13]` | the D-24 convention-dense held-out tasks, unchanged |
| `seed_from_run` | `run_009` | **not** `run_006` — phase 2 measures the library phase 1 built |
| `task_index_offset` | `6` | continues run_009's numbering (its indices 0–5), so every seeded skill is eligible from T11 |
| `memory_read_only` | `true` | freeze the carried-over library: recall and retrieval work, nothing is written |
| `skill_min_applicable_remaining` | `0` | keep the gate off; with `memory_read_only: true` no skill is proposed anyway, and the recorded config must match phase 1 |
| `seed_skill_exclude` | `[]` | unless the audit in step 2 names a skill to force out |

Unchanged from phase 1 and from run_008: `seed: 42`, `max_retries: 4`, `pass_threshold: 3.5`,
`max_operator_steps_per_condition: 64`, `feedback_max_items: 3`, `reveal_fixes: false`, `retrieval_k: 8`,
`foundational_skills: false`, `model_identifier`, `operator`.

Keep the phase-1 values in comments, as the file already does for earlier experiments.

## 2. Run the leakage audit before `init`

```bash
uv run python scripts/seed_audit.py --run-id run_010 --holdout T11,T12,T13
```

The audit reads the `seeding` block of `logs/runs/run_010.json`, so run it **again after `init`** as well;
before `init` it will only report what it can reach. It exits 1 if any material golden number of T11/T12/T13
is reachable from the seeded material. A genuine leak is handled by adding the offending skill id to
`seed_skill_exclude` — **never** by editing a skill file, which is immutable evidence.

Expect more seeded skills than run_008's two: with the gate off, `run_009` may have learned late lessons
(leakage exclusions, the ROC-AUC range, brief conventions), which is exactly the material T12 and T13 ask for
and exactly what the audit must therefore re-check.

## 3. Initialise and drive the run

```bash
uv run python -m src.run_experiment init --run-id run_010 --conditions skill_learning --mode manual
uv run python scripts/seed_audit.py --run-id run_010 --holdout T11,T12,T13   # re-run with the seeding block written
uv run python -m src.run_experiment advance-all --run-id run_010
```

Then the usual manual loop from `docs/OPERATOR_PROTOCOL.md`: for each `OPERATOR NEEDED` path, spawn one
stateless `experiment-operator-blind` subagent (model `haiku`) on that request file, let it write the matching
`.response.json`, and call `advance-all` again until the condition reports `done`.

## 4. Confirm before reporting

- `logs/runs/run_010.json` → `config.seed_from_run == "run_009"`, `config.task_index_offset == 6`,
  `config.memory_read_only == true`, `config.skill_min_applicable_remaining == 0`,
  `config.freeze_sha256` starts `bab215a5fbcc`.
- `logs/runs/run_010.json` → `seeding.skills.files` lists the `skills/evolved/run_009/*.md` files, and
  `seeding.memory` is absent for `skill_learning` (that arm carries skills, not notes).
- `logs/skill_events.jsonl` for `run_010`: `skill_retrieved` events naming `evolved_run_009_*` ids, and
  `memory_write_skipped` / no `skill_persisted` (the library is frozen for the test).
- The comparison the write-up makes is **run_010 against run_008 on T11/T12/T13** — same tasks, same freeze,
  same frozen-memory design, one variable: whether the seeded library was built with the gate on (run_006 via
  run_008) or off (run_009).
