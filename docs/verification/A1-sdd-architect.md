# A1 — SDD architect · verification notes

**Date:** 2026-09-06. **Session note:** project agent types were not loaded, so A1 ran as a general-purpose agent adopting `.claude/agents/sdd-architect.md` (tools used: Read, Write, Bash, Grep only; no files outside A1 ownership were edited).

## Deliverables

| Path | Unit |
|---|---|
| `docs/idea.md`, `docs/spec.md` | 1 |
| `docs/plan.md` | 2 |
| `docs/tasks.md` | 3 |
| `docs/security-review.md` | 4 |
| `docs/decision-log.md` | 5 |
| `config/experiment.yaml`, `config/graph.yaml` | 6 |
| `README.md`, `docs/writeup.md` (outline), `docs/verification-log.md` (skeleton) | 7 |
| consistency pass + this file | 8 |

## Commands run and results

1. `uv run python -m src.agent_tracker start --agent A1 --task "SDD documents and configuration"` — A1 `running`; totals L0 12, A1 8, A2 5, A3 10, A4 7, A5 8, A6 8.
2. Locked versions read from `uv.lock` (grep): pandas 3.0.5, scikit-learn 1.9.0, langgraph 1.2.11, langgraph-checkpoint-sqlite 3.1.1, langchain-core 1.6.2, pydantic 2.13.5, matplotlib 3.11.1, networkx 3.6.1, huggingface-hub 1.30.0, pytest 9.1.1, langchain-anthropic 1.7.1 (optional extra); `uv run python --version` → Python 3.12.13. Used in `docs/decision-log.md` D-10.
3. `docs/tasks.md` unit sums vs tracker — Python snippet:

   ```python
   import re, json
   from collections import defaultdict
   sums = defaultdict(float)
   for line in open("docs/tasks.md", encoding="utf-8"):
       m = re.match(r"^\|\s*(L0|A[1-6])-(\d+)\s*\|", line)
       if m:
           sums[m.group(1)] += float([c.strip() for c in line.strip().strip("|").split("|")][3])
   tracker = {a["agent_id"]: a["total_work_units"] for a in json.load(open("logs/agent_status.json"))["agents"]}
   assert all(sums[k] == tracker[k] for k in tracker), (dict(sums), tracker)
   ```

   Result: L0 12, A1 8, A2 5, A3 10, A4 7, A5 8, A6 8 — all match; 49 rows; 58 units. **Passed.**
4. `uv run python -c "import yaml;[yaml.safe_load(open(p)) for p in ['config/experiment.yaml','config/graph.yaml']];print('yaml ok')"` → `yaml ok`. **Passed.**
5. Structural check of the configs (Python): `list(experiment.yaml) == [seed, conditions, task_order, max_retries, pass_threshold, max_operator_steps_per_condition, retrieval_k, duplicate_similarity_threshold, dataset, freeze_manifest, default_mode, model_identifier, operator, dashboard_refresh_seconds]` → True; `dataset` keys `[repo, revision, files]` → True; condition sets equal between the two files → True. **Passed.** Per-condition edge check (rerun with `PYTHONIOENCODING=utf-8` after the first attempt crashed printing a non-ASCII character to the cp1252 console): `baseline` 6 nodes / 6 static edges, `reflection_only` 7 / 7, `skill_learning` 12 / 9 — all edge endpoints declared, all conditional targets declared, all router labels declared, every node entered and with an exit; `termination` mirrors `experiment.yaml`; `llm_decision_nodes ⊆ nodes`; `skill_learning` uses all 12 nodes → `STRUCTURE OK`. **Passed.**
6. Stale-term grep over A1-owned files for `manual_or_stub|default anthropic_api|Agent SDK|headless` → 7 matches, all prohibition statements or the decision log's historical mention (D-04); no stale usage. Grep for `reflection-only|skill-learning condition|skill-learning route` → none (condition names spelled `reflection_only` / `skill_learning` consistently). **Passed.**
7. Tracker: `complete-unit` recorded after units 1–5 (see `logs/agent_events.jsonl`); units 6–8 and `review` recorded at the end of this session.

## Failures and how they were handled

- A ~13 KB quoted heredoc for `docs/spec.md` was rejected by the shell (`unexpected EOF`); bash rejects the whole command before executing, so no partial file was written. Large documents were written with the file-write tool instead. No impact on deliverables.
- Structural-check script crashed printing `⊆` to a cp1252 console; rerun with UTF-8 stdout (item 5).

## Requests to other owners (not edited by A1)

- **L0:** `.env.example` lines 6 and 8 still document/set `CLAIMS_SKILL_LOOP_LLM_MODE=manual_or_stub`; update to `manual` (default) / `stub` / `anthropic_api` and add `CLAIMS_SKILL_LOOP_OPERATOR`. Add `logs/checkpoints/*.sqlite` to `.gitignore`. Confirm or override the A1 formalisations listed in `docs/decision-log.md` D-12.
- **A5:** `src/dashboard.py:231` footer says results from `manual_or_stub` runs are simulations; change to `stub`, and label `manual` runs as operator-driven (no API).
- **A3:** the catalogue may optionally declare `required_components` per task (plan §3 stub rule); if not, the stub provider uses `default_selected` only.
- **A6:** accept `timeout_seconds` in `run_context` (plan §13; graph.yaml `execution_timeout_seconds`).

## Deliberate deviations / formalisations relative to LEAD_DESIGN_DECISIONS

None contradict LEAD. Additions are marked **(A1 formalisation)** in `docs/plan.md` and listed in `docs/decision-log.md` D-12: `analysis_plan: dict | None`; routers `route_after_reflection/proposal/validation`; ≤ 2 validation re-requests then catalogue-default fallback; cap counts every request file; `execution_timeout_seconds` placed in `config/graph.yaml` (LEAD §12 fixes the `experiment.yaml` key list); freeze-manifest shape + `freeze_sha256 = sha256_file(manifest)`; `logs/runs/<run_id>.json`; dropped `skills_applied` handling; feedback `incorporated`/`resolved` rules; `feedback_update` records; empty-dimension scoring rule.

## Limitations

- A1 verified document consistency and configuration structure only; no implementation exists yet, so no runtime behaviour described in `docs/plan.md` has been executed.
- The `graph.yaml` mirror is checked for internal consistency here; equality with the compiled graph is asserted only once L0's `tests/test_graph_routes.py` exists.
