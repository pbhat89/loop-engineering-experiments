# A5 — observability engineer: verification note

Date: 2026-09-07 (session resumed after a rate-limit interruption; units 1–2 were verified by the lead before the resume).
Owner files: `src/experiment_logger.py`, `src/dashboard.py`, `src/charts.py`, `tests/test_logging.py`, `tests/test_dashboard.py`, this note.
Everything below was run from `d:/Projects/SkillRL/claims-skill-loop`; synthetic data only; no network; matplotlib Agg.

## Deliverables

| Path | What it is |
|---|---|
| `src/experiment_logger.py` | `ExperimentLogger` (four typed JSONL writers, readers, `write_experiment_status` atomic snapshot), `validate_logs()` with `file:line` diagnostics, `summarize_runs()`, secret-key refusal. Unchanged this session. |
| `src/charts.py` | Six log-derived figures + `figures_manifest.json` via `render_all(logs_dir, out_dir)`, `render_topology()` for the designed workflow. This session: fourth condition `foundational_only` with a fixed Okabe-Ito colour (`#CC79A7`); topology node-membership fills computed per distinct membership set (legend stays truthful for any number of conditions); title/subtitle spacing derived from figure height; a shared `_bottom_legend` strip so legends never collide with the notes line; learning-curve series get a small categorical x-offset so identical scores stay visible (noted on the figure); reliability panels use integer axes and say "every observed count is 0" instead of showing fractional ticks; skill-accumulation cumulative counts stop at the last task a condition actually reached (no carry-forward into unrun tasks); skill-utility annotation no longer overlaps its marker; small heatmap panels annotate only up to six task columns; `Colormap.with_extremes` replaces the deprecated `set_bad`; the observed-lifecycle graph draws only skill-source feedback, splits each task into creator / user nodes and sizes its height by the tallest layer (see open issue 2). |
| `src/dashboard.py` | v2. Keeps the lead's v1 sections (overall completion with the "100 % reserved until gates pass" rule, agent board, blocked work, recent events). Adds an **Experiment** area: per run → per condition rows (status glyph + word, current task · node · attempt, **pending operator request path with "waiting for Xm Ys · since …"**, tasks done/total with a bar, operator steps used/cap, retries, execution errors, skills created/retrieved, mean score, the runner's rough ETA label); a per-task score grid (rows = conditions in fixed order, columns = configured task order, cell = final score, `✓` = first-attempt pass, `◆ waiting` / `◐ running` for the current task, `—` otherwise); figures embedded via relative paths (`../figures/<name>.png`, `../graphs/langgraph_topology.png`) with manifest source/run/"no observations" notes in the captions; a log-source table (records, bytes, last modified) plus `validate_logs` problems; the footer names every source file and states that `stub` runs are deterministic simulations and `manual` runs record operator decisions (the `manual_or_stub` sentence is gone). Self-contained: inline CSS, no scripts, no external assets, `<meta http-equiv="refresh" content="30">`. `render(out_path=None, logs_dir=None, figures_dir=None)`; `python -m src.dashboard [--out] [--logs-dir] [--figures-dir]`. Degrades to "No experiment runs yet" / "No figures rendered yet" / "No agents registered yet". One broken section renders an error card instead of blanking the page. |
| `tests/test_logging.py` | 12 tests. Also exports `build_realistic_logs(logs_dir)`: runs the real graph (`build_claims_skill_graph`) with the route-test fakes for all four conditions across T2–T4 (T2–T3 for `reflection_only`) and writes the logs through `ExperimentLogger`, then a LEAD §10-shaped status snapshot computed from those logs with one synthetic `waiting_operator` overlay (labelled as such in the docstring). |
| `tests/test_dashboard.py` | 6 tests: empty render, no-100 %-before-gates, populated render (pending request path, waiting-since, computed wait duration, score grid, provider header), `render_all` on the generated logs (seven files, manifest content, relative embedding), `render_all` on no logs (every figure `observations: false` with a "no observations" note), `render_topology` into `tmp_path`. |
| `artifacts/dashboard/progress.html` | Regenerated from the real logs (27,389 bytes at the time of writing). |
| `artifacts/figures/*.png`, `figures_manifest.json` | Rendered from the real `stub_001` logs (see below). |
| `artifacts/graphs/langgraph_topology.png` (101,500 bytes), `artifacts/graphs/skill_lifecycle_graph.png` | Designed topology (labelled as design, not observation) and the observed lifecycle copy. |

## Commands run and results

```
uv run python -m src.agent_tracker start --agent A5 --task "Dashboard v2, chart verification, tests (resumed)"

uv run --extra dev pytest tests/test_logging.py tests/test_dashboard.py -q
  first run: 16 passed, 1 failed  (my fixture appended raw lines without `timestamp`; validate_logs correctly reported
             5 problems, not the 3 I asserted - fixture corrected, validator unchanged)
  after fix: 17 passed

uv run --extra dev pytest tests/test_logging.py tests/test_dashboard.py tests/test_graph_routes.py -q
  final: 28 passed   (17 A5 tests + 11 graph-route tests; output "............................ [100%]")

Chart verification (scratchpad script, PYTHONPATH=repo): build_realistic_logs -> render_all(tmp/logs, tmp/figures)
  log lines: experiment_events 28, graph_events 92, skill_events 17, feedback_events 12; validate_logs -> []
  learning_curve.png 68,900 B · reliability_curve.png 65,891 B · skill_accumulation.png 71,217 B · skill_utility.png 72,218 B
  skill_lifecycle_graph.png 89,480 B · rubric_heatmap.png 84,988 B · figures_manifest.json · graphs/skill_lifecycle_graph.png copy
  every figure observations=true; notes truthful (e.g. "no skill events: baseline, reflection_only ...")
  Visual review found and fixed: title/subtitle overlap on short figures; legend colliding with the notes line;
  errors panel with fractional ticks when all counts are 0; cumulative skill counts carried forward to tasks never
  reached (T5-T8) - now stop at the last observed task; four identical learning-curve lines collapsing into one;
  utility annotation over its marker; over-annotated small heatmap panels.

Real artifacts:
  uv run python -c "from src.charts import render_topology; render_topology()"   -> artifacts/graphs/langgraph_topology.png (101,500 B)
  uv run python -m src.charts        (real logs: run stub_001, conditions baseline / reflection_only / skill_learning, T1-T8)
  uv run python -m src.dashboard     -> artifacts/dashboard/progress.html
  validate_logs() on logs/ -> []  (dashboard shows "Log validation: no problems")
```

## Figure list (real `artifacts/figures/`, from `stub_001`)

| Figure | Bytes | Manifest notes |
|---|---|---|
| `learning_curve.png` | 57,977 | series offset slightly on the task axis; no observations: foundational_only |
| `reliability_curve.png` | 58,237 | no observations: foundational_only |
| `skill_accumulation.png` | 58,273 | no skill events: baseline, reflection_only, foundational_only (only skill_learning and foundational_only retrieve skills; only skill_learning creates them) |
| `skill_utility.png` | 69,419 | illustrative: descriptive comparison within one condition, later tasks only; not a causal estimate (5 evolved skills) |
| `skill_lifecycle_graph.png` | 188,498 | observed from logs; 44 foundational skill retrieval events omitted for legibility; 74 of 79 feedback items never became a skill source and are not drawn (21 nodes, 25 edges; also copied to `artifacts/graphs/`) |
| `rubric_heatmap.png` | 80,832 | no observations: foundational_only |
| `figures_manifest.json` | 5,752 | run_ids `["stub_001"]`, task_ids T1–T8, condition colours, per-figure sources/notes, skill-utility rows |

`foundational_only` shows as "no observations" everywhere because `stub_001` was started with the three default conditions; that is the correct rendering of a missing condition, not a chart defect.

## Dashboard behaviour checked

- Empty `logs/` → "No experiment runs yet", "No agents registered yet", "No figures rendered yet", validation clean (test).
- Tracker status with 99.5 % and gates not passed → "not yet passed" and "100% is reserved until they pass" (test).
- Generated logs + status → pending request path, `waiting_since`, "waiting for 7m NNs", `◆ waiting_operator`, `● done`, score cells `4.00 ✓` / `4.00`, `◆ waiting` in the current task's cell, T1–T8 columns, `/40` caps, condition swatches in the fixed colours (test).
- Real logs → run header `mode stub · provider stub · model deterministic-fixture-v1 · operator deterministic-fixture · freeze unfrozen`; three condition rows; score grid; six figures + topology embedded via `../figures/` and `../graphs/` (checked with grep). A first render printed the runner's `provider` dict as a Python repr; fixed and guarded by a test.

## Open issues / requests to other owners

1. **L0 (`src/run_experiment.py`)**: the runner refreshes the dashboard after every node but never calls `charts.render_all`, so `artifacts/figures/` only updates when `python -m src.charts` is run (plan §18 expects a chart refresh at `finalize_task` / end of condition). Suggested: best-effort `charts.render_all(run_ids=[run_id])` in `finalize` paths, wrapped like the dashboard call.
2. The first real render of the lifecycle figure was illegible (912 KB): `stub_001` issues ~80 feedback items and every task both issues feedback and later uses skills, so all feedback stacked in one column and all eight tasks collapsed onto one spot. Fixed in `build_lifecycle_graph`: only feedback items that became a skill's source are drawn (the omitted count is printed on the figure), each task appears once as a creator (left) and once as a user (right), and the figure height follows the tallest layer. Before any skill is persisted the task -> feedback half is still drawn. A very long multi-run render may still want `--run-id` filtering.
3. Figure subtitles use `utils.rel()`; for logs outside the repo (tests, scratch runs) the path falls back to an absolute path and the subtitle wraps to two or three lines. Inside the repo it is one line.
4. `foundational_only` is in `designed_topology()` and everywhere in charts/dashboard, but `config/experiment.yaml` still lists three conditions; a run must opt in with `--conditions ...,foundational_only`.

## Interface deviations from `docs/plan.md` / `docs/tasks.md`

- `docs/tasks.md` A5-2 names `update_status(...)`; the implemented API is `ExperimentLogger.write_experiment_status(snapshot)` — the runner builds the LEAD §10 snapshot (`Runner.status_snapshot`) and the logger validates (secret keys) and writes it atomically. ETA arithmetic therefore lives in the runner; my tests cover the snapshot shape and atomic write, not the ETA rule.
- A5-5 names `artifacts/graphs/skill_lifecycle_graph.html`; the artifact is `skill_lifecycle_graph.png` (matplotlib + networkx, no external assets), written to `artifacts/figures/` and copied to `artifacts/graphs/`.
- LEAD §10's example shows `provider` as absent; the runner writes a dict `{provider_mode, operator, model_identifier}` — the dashboard accepts a string or that dict.
- `dashboard.render` gained optional `logs_dir` / `figures_dir` parameters (backwards compatible; the tracker and runner call it with no arguments).
