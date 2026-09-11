# Operator protocol for manual-mode runs (L0)

How the lead drives a comparative run without any model API call. Every LLM-decision step is answered by a **fresh, stateless Claude Code subagent** that sees exactly one request file and writes exactly one response file. The Python runtime never calls a model; it pauses on a LangGraph interrupt and resumes when the response file exists.

Two operator definitions exist:

| Definition | Used in | Model | Carries analytical conventions? |
|---|---|---|---|
| `.claude/agents/experiment-operator.md` | experiment 1 (`run_001`) | Claude Fable 5.1 (session model) | yes — a list of analytical standards (denominators, train-only fitting, leakage exclusions, caveats) |
| `.claude/agents/experiment-operator-blind.md` | experiments 3 (`run_005`), 4 (`run_006`) and 5 (`run_007`, `run_008`) | Claude Haiku 4.5 (`model: haiku`) | **no** — house rules must come from the request: feedback, retrieved skills, recorded past comments, or its own review |

The second definition exists because the first, combined with briefs that stated the conventions, produced the experiment-1 ceiling (every task 4.00 first attempt, nothing to learn). Experiment 3 blinds the briefs *and* the operator, caps the feedback to the three most severe findings per attempt with the literal fix withheld, and allows five attempts (decision D-21).

Experiment 4 (`run_006`, decision D-22) keeps all of that and changes two things: the suite is **six tasks** with T1 and T8 blinded as well, and there are **five arms** — the three from experiment 3 plus two *raw-memory* arms. A memory arm carries a plain log of past findings, appended verbatim after each task to `artifacts/memory/<run_id>/<condition>.jsonl` and shown in full (most recent first, at most 30 items) in the `past_feedback` key of later `plan_task` / `revise_plan` requests. Nothing is distilled, filtered for relevance or turned into a skill; the request itself says the comments come from earlier tasks and may or may not apply.

Experiment 5 is a **held-out transfer test**: three arms — `reflection_only` (cold: checker feedback, no memory, nothing carried in), `feedback_memory` (warm: seeded with run_006's 19 raw notes) and `skill_learning` (warm: seeded with run_006's two learned skills) — over tasks none of them has attempted. No self-review arms: experiment 4 already answered that question, and the transfer question is about what memory carries.

Version 1 (`run_007`, decision D-23) ran **four** held-out tasks, **T9 → T10 → T5 → T6**, and hit a ceiling: the cold arm's *first attempts* already scored 3.09–3.68 against a 3.50 threshold, so memory had almost nothing to add, and the memory kept learning as the run went along. It is archived at `archive/experiment-5_run_007_heldout-v1/`.

**Version 2 (`run_008`, decision D-24) is the reported run.** It runs **three convention-dense tasks**, in the order **T11 → T12 → T13**, whose conventions are all ones run_006 was corrected on and whose values it has never seen: **T11 "Portfolio deep-dive"** (T2's components verbatim — adjudicated denominator, fraud prevalence over all claims, three amount columns with quantiles, the `service_date_from` month key, printed denominators, two caveats, plus the monthly paid-spend series and two distribution quantiles T2 does not score), **T12 "High-cost model, wider net"** (T7's components verbatim with the target at the 90th percentile of paid amount — training-split-only threshold, leakage exclusions, train-only preprocessing, logistic + one tree model, the full ranking-metric set, three caveats) and **T13 "Brief for the CFO"** (T8's components, sourced **only** from T11 and T12 — a citation behind every number, associative phrasing, five sections, 600 words, two caveats). On the frozen evaluator, catalogue defaults score 1.18 / 1.69 / 1.57 and the house conventions score 4.00 / 4.00 / 4.00, so a cold arm starts with room to move.

**The memory is frozen for the whole of `run_008`** (`memory_read_only: true` in `config/experiment.yaml`). Recall is untouched — `load_context` still hands the warm arm all 19 seeded notes before every plan (`memory_retrieved`), and `retrieve_skills` still lists run_006's two skills. Nothing is written: `finalize_task` appends no note and logs a `memory_write_skipped` event with `reason: read_only` and the count it withheld, and `skill_learning` routes to `completed` instead of `learn`, so no skill is reflected on, proposed, validated or persisted. `memory_read_only` appears on the run manifest (in `config` and in `seeding`) and on every `done` record. run_008 therefore measures only what run_006 left behind — a new joiner handed three pieces of work, against a colleague who has been corrected on this data for months.

Seeding happens once, at `init`, and is read-only with respect to `run_006`. The memory arm's log is copied from `artifacts/memory/run_006/feedback_memory.jsonl` into `artifacts/memory/run_008/feedback_memory.jsonl` with **every numeric token in each record's `text` and `detail` replaced by `[n]`** (except task ids `T\d+` and the quantile names `p90` / `p99`), each record stamped `seeded_from: run_006`; **19 records, 24 tokens redacted** — run_006's log, not run_007's, which was archived with that run. The skills arm needs no copy at all — the store simply also lists `skills/evolved/run_006/*.md` read-only, so ids such as `evolved_run_006_001` show up in `skills_retrieved`; with the memory frozen, nothing new is written under `skills/evolved/run_008/`. `task_index_offset: 6` continues run_006's task numbering (its indices 0–5, run_008's 6–8), which is what keeps a skill learned after run_006's index 0 or 1 eligible from the very first held-out task. The whole provenance is in `logs/runs/run_008.json` under `"seeding"`, and `uv run python scripts/seed_audit.py --run-id run_008 --holdout T11,T12,T13` re-checks it: it exits 1 if any number from a holdout golden is reachable from the seeded notes or skill files. It reported **clean** — 95 material golden numbers in 981 string forms, 58 numeric tokens in the seeded material, 0 reachable — and named the one golden value the redaction removed (`12339`, T11's adjudicated-claim denominator, which was in the detail of run_006's T2 note). A seeded skill file is never edited — a genuine leak would be handled by adding its id to `seed_skill_exclude` in `config/experiment.yaml`.

## Preconditions (Phase 1.5 gates)

1. `goldens/` built by `src/build_goldens.py`, reviewed by the user via `artifacts/reports/golden_review.md`.
2. `config/tasks.yaml` and `config/rubric.yaml` final.
3. `uv run python -m src.run_experiment freeze` → `config/freeze_manifest.json` (hashes of data, goldens, tasks, rubric). Comparative runs refuse to start if any hash drifts. Experiment 5 v2 freeze: `bab215a5fbcc…` (v1: `74e64e1d38e3…`; experiment 4: `59fb61d35fe8…`; 3: `64b7292e8214…`; experiments 1–2: `1566c5698a50…`). Between v1 and v2 `config/tasks.yaml`, `config/rubric.yaml` and three new golden files changed; the ten existing goldens are byte-identical apart from `built_at` and `build_goldens --check` is clean over all thirteen.
4. A full `stub` run has passed end-to-end: `uv run python -m src.run_experiment run-stub --run-id stub_006 --conditions reflection_only,feedback_memory,skill_learning` (experiment 5 v2: `archive/experiment-5_stub_006_smoke/` — all three arms 4.00 on T11/T12/T13, `validate_logs()` clean, the seeded 19-note log untouched, no skill persisted; earlier: `archive/experiment-5_stub_005_smoke/`, `archive/experiment-4_stub_004_smoke/`).

## The loop

```bash
# once per run
uv run python -m src.run_experiment init --run-id run_008 --conditions reflection_only,feedback_memory,skill_learning --mode manual

# repeat until every condition reports done
uv run python -m src.run_experiment advance-all --run-id run_008     # resumes conditions whose response file exists, then prints pending requests
#   OPERATOR NEEDED [reflection_only] -> artifacts/manual/run_008/reflection_only/T11_a1_plan_task_1.request.json
#   OPERATOR NEEDED [feedback_memory] -> artifacts/manual/run_008/feedback_memory/T11_a1_plan_task_1.request.json
#   OPERATOR NEEDED [skill_learning]  -> artifacts/manual/run_008/skill_learning/T11_a1_plan_task_1.request.json
# for each pending request: spawn one operator subagent (prompt below), which writes the matching .response.json
# then advance-all again
uv run python -m src.run_experiment status --run-id run_008            # per-condition tasks, scores, steps used, rough ETA
```

`logs/experiment_status.json` and `artifacts/dashboard/progress.html` update after every node; the dashboard shows the pending request per condition and how long it has waited.

Conditions are independent threads: one operator subagent per condition runs at the same time (three in run_008; up to five when five arms are configured). A subagent never sees another condition's files, and never the other conditions' memory logs.

## Operator subagent prompt (verbatim template, experiments 3 and 4 — unchanged)

Spawned with the Agent tool, `model: haiku`, one per request file:

> You are the **experiment operator** for one manual-mode step of the claims-skill-loop experiment. Adopt `d:/Projects/SkillRL/claims-skill-loop/.claude/agents/experiment-operator-blind.md` as your operating instructions (read it first). Then read exactly one file — the request `<REQUEST_PATH>` — and write exactly one file — the response `<RESPONSE_PATH>` — as JSON conforming to the `response_schema` embedded in the request. Use only component ids and parameter options that appear in the request's `component_catalogue`; base every decision solely on the request contents; do not read or write any other file, run code, or use the network. Finish with one line naming the file you wrote and the decision you made.

Experiment 1 used the same template with `experiment-operator.md` and the session model.

Rules the lead follows:

- One subagent per request file, never reused, never given conversation context, never told which condition or task number it is beyond what the request contains.
- The lead never edits a response. A response that fails validation is logged (`operator_validation_error`) and the runner issues a new request with `validation_errors`; the lead spawns a new subagent for it.
- The lead does not read request or response contents during the run except to confirm a file exists (to avoid steering later steps); the files are inspected only after all conditions finish.
- If the session hits a rate limit mid-run, nothing is lost: checkpoints and request/response files are on disk; `advance-all` resumes after the reset.

## What the operator is shown (experiment 4, five arms; run_008 runs the first three rows with the memory frozen)

| Arm | `plan_task` | after `evaluate_output` | `revise_plan` | `past_feedback` (cross-task memory) | after a pass |
|---|---|---|---|---|---|
| `reflection_only` | brief, catalogue, manifest summary | the 3 most severe failed checks (no literal fix) + scorecard + count of further failures | prior plan, those 3 findings, its reflection | — | — |
| `feedback_memory` | same | same | same | **yes** — every checker finding it was shown on earlier tasks, verbatim, newest first, ≤ 30 | — |
| `skill_learning` | + retrieved skills (learned in this run only; the library starts empty) | same | + retrieved skills | — (skills instead) | reflect over the whole task → propose ≤ 1 skill → validate → persist |
| `self_refine` | brief, catalogue, manifest summary | **nothing** — the operator reviews its own report and metrics (`self_evaluate`) and decides accept / revise | prior plan, its own findings | — | — |
| `self_refine_memory` | same | same (still nothing from the checker) | same | **yes** — its own review findings from earlier tasks, with each review's verdict and summary, newest first, ≤ 30 | — |

In `run_008` the three arms that run are the first three rows, with one change from `memory_read_only: true` (D-24): the "after a pass" column is empty for `skill_learning` — it neither reflects for learning nor proposes a skill — and `feedback_memory`'s log is recalled but never appended to, so its `past_feedback` stays exactly the 19 seeded notes for all three tasks.

The frozen evaluator scores every attempt of every arm identically; only what is *shown* differs. The two memory logs live at `artifacts/memory/<run_id>/<condition>.jsonl`, one line per finding, written by `finalize_task` and read by `load_context`; they are committed with the run and archived by `scripts/archive_run.py`. `self_refine_memory` never sees a checker finding in its memory — only what it told itself.

## What gets recorded

- `logs/graph_events.jsonl`: `operator_request` (request path), `operator_response` (response path, SHA-256), `operator_validation_error`, plus every node transition (for `self_evaluate`: the verdict next to the frozen score it did not see).
- `logs/experiment_events.jsonl`: one `attempt` record per evaluation (`n_failed_checks`, `n_feedback_shown`, `critical_failures`, `skills_applied`) and one `done` record per task with `attempts_to_pass`, `score_by_attempt`, `self_declared_pass`, `past_feedback_count`, `memory_read_only`, `stop_reason` (`passed` | `retry_budget_exhausted` | `self_accepted` | `operator_cap`), provider metadata and `freeze_sha256`.
- `logs/skill_events.jsonl`: for the memory arms, `memory_retrieved` (how many past comments were recalled before planning) and `memory_written` (how many findings the task added) — or, when the run carries a frozen memory (`memory_read_only`, D-24), `memory_write_skipped` with `reason: read_only` and the count withheld — alongside the skill lifecycle events.
- `artifacts/manual/<run_id>/<condition>/*.request.json|*.response.json`: the complete operator transcript, committed with the run.
- Every `propose_skill` and `revise_skill_proposal` request payload carries **`skill_rule`** — the skill-proposal rule in force for that run, in one sentence, so the transcript records what the operator was held to rather than leaving it to be inferred from the config (D-25). It reads "A lesson may become a skill only when it applies to at least two of the task ids listed in remaining_task_ids; otherwise return proposal: null" when `skill_min_applicable_remaining` is 2 (experiments 1–5, and the default), and "There is no minimum number of remaining tasks: any lesson that generalises beyond this task may become a skill, even if no remaining task in this run would use it" when it is 0 (experiment 6, `run_009` / `run_010`). The `instructions` field of the same request changes with it, and `.claude/agents/experiment-operator-blind.md` defers to both rather than stating a rule of its own.

## Budget expectations (recorded, not promised)

Per condition and task, five attempts at most: `plan_task` (1) + up to 4 × (`reflect_on_feedback` + `revise_plan`) for reflection_only / feedback_memory / skill_learning, or 4 × (`self_evaluate` + `revise_plan`) for self_refine / self_refine_memory; skill_learning adds `reflect_on_feedback` + `propose_skill` (+ ≤ 1 `revise_skill_proposal`) after each task — **except under `memory_read_only`, where the learn path is closed and skill_learning costs exactly what reflection_only costs**. The memory arms cost no extra operator steps — recall and write are pure file operations. Hard cap `max_operator_steps_per_condition = 64` (the run_008 fixture smoke run used 17 per arm over three tasks; the six-task experiment-4 fixture run used 24–41). The realised counts appear in `experiment_status.json` and the write-up.

---

# Underwriter operator (experiment 7, the underwriting apprentice)

Experiment 7 runs a different job on the same machinery. One task repeated thirty-eight times — rate a life-insurance application — with **five arms** that differ only in what each is handed before it decides and what each keeps afterwards. The design is `docs/underwriting-apprentice-design.md`, the build spec is `docs/underwriting-build-brief.md`, the rationale is decision **D-27**.

Operators are **Claude Fable 5.1** (`model: fable`), not Haiku: `.claude/agents/underwriter-operator.md`. One fresh instance per request file, as always.

| Arm | Handed at decide time | Kept afterwards |
|---|---|---|
| `new_joiner` | the starter manual | nothing. Permanently on day one |
| `notebook` | + every past markup, verbatim, newest first | appends the markup as written (no model call) |
| `written_rules` | + its own house-rule book | a **reflection call** (a fresh instance) rewrites the whole book in its own words |
| `precedent` | + the 3 nearest past cases with their correct answers and the distance | files this case with its correct answer (no model call) |
| `ask_senior` | the starter manual; may first ask up to 4 questions | nothing. Pays the cost again every case |

The ask-a-senior oracle is **deterministic code**, not a model (`src/underwriting/senior.py`): keyword routing over the house rules, gated on the rule being relevant to the case in hand, falling back to reading the manual section back and then to "Not something I can answer from here; use the manual."

## What the operator never sees

House-rule text or ids, point values of hidden rules, tier labels, golden answers, or any statement of what it is being measured on. `src/underwriting/audit.py` asserts this over **every** request file a run writes, and `python -m src.underwriting.run audit --run-id <id>` runs it. Two narrow exemptions, both deliberate: the ask-a-senior answers (quoting a rule out loud is that arm), and the operator's own rule book (its prose, not ours).

## Preconditions

1. `python -m src.underwriting.data verify` → `underwriting data pack clean`. This re-derives the manual, the house rules, the 38 cases and the goldens from code, compares them with `data/underwriting/`, re-checks the whole section-5 schedule, and verifies the freeze manifest. Experiment 7 freeze: `d95f49f1f930…`.
2. The stub smoke has passed end to end for all five arms: `archive/experiment-7_stub_smoke/` — labelled stub, no model called, leakage audit 0 problems.

## The file protocol

```text
artifacts/uw/<run_id>/requests/<arm>/<phase>_case<NN>_<step>[_rN].json
artifacts/uw/<run_id>/responses/<arm>/<same file name>.json
```

`<phase>` is `train` or `holdout`; `<NN>` is the case number inside that phase, zero-padded; `<step>` is `ask`, `decide` or `reflect`. A response that fails Pydantic validation is re-requested with the errors attached under the payload key `validation_errors`, as `…_r2` and then `…_r3`; after that the answer is scored at the postpone-equivalent distance of 2 and flagged `unparseable` in the run log.

## The loop

```bash
# per arm and phase; the command runs until it needs an operator, then returns
python -m src.underwriting.run --run-id uw_001 --condition notebook --phase train
#   OPERATOR NEEDED [notebook/train] -> artifacts/uw/uw_001/requests/notebook/train_case01_decide.json
#                    response -> artifacts/uw/uw_001/responses/notebook/train_case01_decide.json
# spawn one fresh operator subagent for that request, then run the same command again
python -m src.underwriting.run status --run-id uw_001
```

Arms are independent: five runner processes may run at the same time, and a subagent never sees another arm's files. Within an arm, finish `--phase train` before starting `--phase holdout` — the held-out phase reads the memory training left behind and writes nothing back.

`--poll` makes the runner wait for each response file itself instead of returning, for an orchestrator that would rather block than re-invoke.

## Operator subagent prompt (verbatim template, experiment 7)

Spawned with the Agent tool, `model: fable`, one per request file:

> You are the **underwriting operator** for one step of the underwriting-apprentice experiment. Adopt `d:/Projects/SkillRL/claims-skill-loop/.claude/agents/underwriter-operator.md` as your operating instructions (read it first). Then read exactly one file — the request `<REQUEST_PATH>` — and write exactly one file — the response `<RESPONSE_PATH>` — as JSON conforming to the `response_schema` embedded in the request. Base every decision solely on the request contents; do not read or write any other file, run code, or use the network. Finish with one line naming the file you wrote and the decision you made.

Substitute `<REQUEST_PATH>` and `<RESPONSE_PATH>` with the two paths the runner printed, and nothing else. The prompt never names the arm, the case number, the tier or the phase.

Rules the orchestrator follows, unchanged from experiments 3–6:

- One subagent per request file, never reused, never given conversation context.
- Never edit a response. A response that fails validation produces a new request with `validation_errors`; spawn a new subagent for it.
- Do not read request or response contents during the run except to confirm a file exists.
- Nothing is lost to a rate limit: checkpoints and request/response files are on disk and the same command resumes.

## Budget

| Arm | Calls per case | Over 38 cases |
|---|---|---|
| `new_joiner` | 1 decide | 38 |
| `notebook` | 1 decide | 38 |
| `written_rules` | 1 decide + 1 reflect (training cases only) | 68 |
| `precedent` | 1 decide | 38 |
| `ask_senior` | 1 ask + 1 decide | 76 |
| **total** | | **258** |

Re-requests add to this; the stub smoke needed none. The notebook and precedent updates cost nothing — they are file operations, not calls.

## What gets recorded

- `artifacts/uw/<run_id>/<arm>/cases.jsonl` — one record per case: index, phase, every score, question count, memory size, nearest precedent distance, re-requests, the request and response file names, timestamps, mode, operator and model identifier, and the freeze. **The tier is not written here**; `scripts/summarize_uw_run.py` joins it in from the goldens at analysis time, so nothing downstream can condition on it by accident.
- `artifacts/uw/<run_id>/run.json` — per-arm, per-phase progress, the pending request, the provider metadata and the freeze.
- `artifacts/uw/<run_id>/requests/`, `responses/` — the complete operator transcript.
- `artifacts/uw/<run_id>/notebook/markups.jsonl`, `written_rules/rulebook.md` + `history/vNN.md`, `precedent/filed_cases.jsonl` — the three memories.
- `python scripts/summarize_uw_run.py --run-id <id>` prints the per-arm table, the per-tier means, the trailing-five series and the three validation checks registered in advance: cases 1–3 a dead heat across the four non-asking arms, the clean tier flat for everyone, and the two novel-rule held-out cases missed.
