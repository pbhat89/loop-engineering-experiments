# A4 — skill-system engineer: verification notes

Date: 2026-09-06 (resumed run after a rate-limit interruption; schema and the six foundational
skills were written in the first run and verified by the lead).

## Deliverables

| Path | What it is |
|---|---|
| `skills/SKILL_SCHEMA.md` | Schema: frontmatter fields, eight sections, content rules, immutability, layout. |
| `skills/foundational/01_data_contract.md` … `06_evaluation_and_charting.md` | `foundational_001…006`, all eight sections, tags for retrieval. |
| `src/skill_store.py` | Frontmatter + `##` section parser (`parse_skill_text`, `load_skill_file`, `validate_skill_schema`), `Skill` dataclass, `SkillStore` (`list_skills`, `retrieve`, `render_for_operator`, `persist`, `record_reuse`, `archive`, `purge_run`), `skills/index.json` handling under `skills/.index.lock`. |
| `src/skill_validator.py` | `validate(proposal, existing_skills, task_id, remaining_task_ids)` with named checks and documented thresholds. |
| `tests/test_skill_store.py` | 26 tests covering parsing/schema, retrieval, persistence, reuse/archive, and the validator. |

## Tests run (real results)

```
uv run --extra dev pytest tests/test_skill_store.py -q     -> 26 passed
uv run --extra dev pytest tests/test_graph_routes.py -q    -> 11 passed (fakes; unchanged)
```

The first run of `test_skill_store.py` had one failure in my own expectation
(`list_skills` sorted purely by `skill_id`, which puts `evolved_*` before `foundational_*`).
Fixed in the store by ordering foundational first, then evolved, each block by `skill_id`;
rerun is green.

## Integration check (script against the real `skills/` tree, run id `a4check`)

Task: `T2 "Claims portfolio description"` — objective "Describe claim volume, status mix,
denial rate with denominators and monthly trends", tags `descriptive, rates, trends, financial`.

Ranking at task index 1 (before persisting anything):

```
foundational_003  14.0  ['descriptive','financial','rates','trends','denial','denominators','monthly','portfolio','rate','status']
foundational_004   3.0  ['denial','rate','status']
foundational_001   1.0  ['rate']
foundational_002   1.0  ['denial']
foundational_006   1.0  ['describe']
```

Then: validator on a sample proposal -> `accepted` (nearest `foundational_003`, similarity 0.085);
`persist` -> `skills/evolved/a4check/evolved_a4check_001_v1.md` + index entry; retrieval at index 1
still excludes it; at index 2 it ranks second with score 6.0 (`descriptive, rates` tags +
`denominators, rate` keywords); re-proposing the same content -> `rejected`,
`duplicate_of=evolved_a4check_001`, similarity 1.0. `purge_run("a4check")` removed the run
directory and its index entry; the leftover empty `skills/index.json` was deleted so the tree
is unchanged.

## How retrieval scores (deterministic)

`score = 2 × |task tags ∩ skill tags| + 1 × |task keywords ∩ skill keywords|`, keywords =
lower-cased tokens of length ≥ 4 from task `title`+`objective` and skill `trigger`+`objective`+tags,
minus `STOP_WORDS` (function words plus suite-ubiquitous words such as *claims, data, task,
analysis, report, table*). A term counted as a tag overlap is not counted again as a keyword.
Ties break on `skill_id`. Evolved skills are eligible only when
`created_after_task_index < current_task_index`; score > 0 required; if fewer than two qualify
the list is padded with the lowest-id foundational skills at score 0 with `matched_terms: []`.
Each hit carries `matched_terms` (plus `matched_tags` / `matched_keywords`) for the log.

## Validator thresholds (also in the module docstring)

`MIN_TEXT_CHARS=10`, `MIN_PROCEDURE_STEPS=2`, `MIN_STEP_WORDS=3`, `MIN_EXAMPLE_CHARS=10`,
`MIN_FUTURE_TASKS=2` (current task excluded), `DUPLICATE_JACCARD=0.6` over token sets of
`objective + procedure`. Severity: safety / generality / duplicate / applicability / provenance
failures -> `rejected`; structural gaps (thin required fields, vague steps, empty tags, empty
optional sections, short example) -> `retry_revision`; otherwise `accepted`. All checks always
run, so `checks` is complete for the event log.

## Interface deviations / interpretations

- `list_skills()` order: foundational first, then evolved, by `skill_id` within each block
  (spec only required determinism).
- Fallback when fewer than two skills score > 0: any scoring hit is kept and the list is
  padded with foundational skills to two, rather than replacing the hit.
- Retrieval hits carry three extra informational keys (`matched_tags`, `matched_keywords`,
  `created_after_task_index`); `validate()` returns one extra key (`nearest_skill_id`) and each
  check carries `severity`. All required keys are present with the required types.
- `render_for_operator` is a `@staticmethod` (callable on the instance as the graph does).
- Added `SkillStore.purge_run(run_id)` for throw-away check runs and test cleanup only; the
  in-experiment retirement path remains `archive`.
- Skill events are not emitted by the store: `graph_nodes.py` already logs
  `skill_retrieved / skill_validated / skill_rejected / skill_persisted / skill_reused` from the
  values the store returns (`score`, `matched_terms`, provenance), so duplicating them here
  would double-log.

## Open issues

- The safety and generality checks are regex-based; the patterns are listed in
  `SAFETY_PATTERNS` / `GENERALITY_PATTERNS` and can produce occasional false positives
  (e.g. "the group count is 30" reads as a hard-coded finding). The graph's single
  `retry_revision` budget does not apply to these (they reject), so a false positive costs one
  proposal. No change requested; flagging for the lead.
- Keyword matching is exact-token (no stemming), so `denominators` in a task does not match
  `denominator` in a skill. Tags carry most of the signal, which is why the six foundational
  skills have broad tag lists.

No files outside A4's ownership were edited. No network, no secrets, synthetic data only.
