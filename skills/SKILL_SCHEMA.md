# Skill schema — claims-skill-loop

A skill is one Markdown file: YAML frontmatter between `---` fences, a single `# Title`
line, and the eight `##` sections below in this fixed order. `src/skill_store.py` parses
exactly this shape; `src/skill_validator.py` checks proposals against the content rules;
`tests/test_skill_store.py` asserts every foundational skill conforms.

## Template (from the brief, plus the extension fields marked ★)

```markdown
---
skill_id: foundational_001
name: data_contract
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null        # ★ extension
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [data_contract, schema, keys]   # ★ extension
applicable_task_ids: []               # ★ extension
---

# Skill title

## Trigger
When the skill should be used.

## Objective
What general reusable problem it solves.

## Procedure
A numbered, concrete procedure.

## Required checks
Assertions, validations, or review checks.

## Expected artifacts
Files, tables, charts, or logs to be produced.

## Failure modes
Known misuse and limitations.

## Example
A concise, generic claims-data example.

## Provenance
Why this skill exists; evolved skills must cite task and feedback IDs.
```

## Frontmatter fields

| Field | Type | Required | Rule |
|---|---|---|---|
| `skill_id` | string | yes | `foundational_NNN` for the six foundational skills; `evolved_<run_id>_NNN` for learned skills (`NNN` is a zero-padded sequence per run). Never reused. |
| `name` | string | yes | snake_case slug, 3–60 characters. Two skills may share a name only as different versions (see below). |
| `version` | int ≥ 1 | yes | Increments only by writing a **new file**; an existing file is never edited. |
| `status` | `active` \| `archived` | yes | The value in the file is the status at write time; the live status lives in `skills/index.json`. |
| `kind` | `foundational` \| `evolved` | yes | Foundational skills are hand-authored; evolved skills are persisted by the skill-learning condition. |
| `created_after_task` | string \| null | yes | Task id (e.g. `T3`) whose evaluation produced the skill; `null` for foundational. |
| `created_after_task_index` ★ | int \| null | yes | Zero-based position of that task in `task_order`. Retrieval eligibility for evolved skills is `created_after_task_index < current_task_index`. `null` for foundational. |
| `source_feedback_ids` | list[str] | yes | Feedback ids the skill was learned from; `[]` for foundational, non-empty for evolved. |
| `created_at` | ISO-8601 string (quoted) | yes | Quote it so YAML keeps it a string. |
| `reuse_count` | int | yes | Always `0` in the file; the live count is in `skills/index.json`. |
| `tags` ★ | list[str] | yes | Lower-case snake_case terms used for retrieval (2 points per overlap with the task's tags). |
| `applicable_task_ids` ★ | list[str] | yes | Task ids the proposer said the skill applies to (`[]` for foundational). Informational; retrieval does not filter on it. |
| `run_id`, `condition` ★ | string | evolved only | Provenance mirror of the directory the file lives in. |

Unknown extra frontmatter keys are preserved on the parsed `Skill.extra` mapping.

## Sections

All eight sections are required and must be non-empty. Headings are matched
case-insensitively and mapped to snake_case keys: `trigger`, `objective`, `procedure`,
`required_checks`, `expected_artifacts`, `failure_modes`, `example`, `provenance`.

* `procedure`, `required_checks`, `expected_artifacts`, `failure_modes` are **lists**: one
  item per numbered (`1.`) or bulleted (`-`) line; indented continuation lines join the
  previous item. The parser exposes them as `list[str]`; prose in these sections is kept as
  a string but fails schema validation for `procedure` (which needs ≥ 2 steps).
* `trigger`, `objective`, `example`, `provenance` are prose strings.
* A **procedure step is concrete** when it names what to compute, compare, record, or
  check (≥ 3 words). "Be careful" is not a step.

## Content rules (enforced on proposals by `src/skill_validator.py`)

1. General, not a task restatement: no single task id as the only scope, no hard-coded
   numeric findings ("denial rate is 10.0%") in trigger/objective/procedure/required
   checks; thresholds and defaults (`n < 30`, `95% interval`) are fine.
2. Safe: a skill never instructs shell or command execution, network access, credential
   or API-key use, `eval`/`exec`, file deletion, or changes to the rubric/goldens/evaluator.
3. Grounded: no "proves", "guarantees", "definitively", or causal claims about fraud/denials.
4. Provenance: evolved skills cite ≥ 1 feedback id and the task they came from.
5. Applicability: an evolved skill must apply to ≥ 2 tasks still remaining in the suite.
6. Not a duplicate: token-Jaccard over `objective + procedure` against every visible skill
   must be < 0.6.

## Immutable files, mutable index

* **Skill files are immutable.** Once written, a skill file is never edited or overwritten.
  A revision is a new file with a new `skill_id` (and `version = previous + 1` when the
  name is reused). Archiving *moves* the file to `skills/archived/` unchanged.
* **`skills/index.json` is the only mutable record**: `{skill_id: {reuse_count, reused_in:
  [task ids], status, path, ...}}`. `reuse_count`/`status` on a loaded `Skill` are overlaid
  from the index when an entry exists. Index writes take `skills/.index.lock`.

## Layout and visibility

```
skills/
  SKILL_SCHEMA.md
  foundational/01_data_contract.md … 06_evaluation_and_charting.md   (foundational_001…006)
  evolved/<run_id>/<skill_id>_v<version>.md                          (run-scoped)
  archived/<same filename>
  index.json
```

`SkillStore(root, run_id)` sees the six foundational skills plus only the evolved skills of
its own `run_id`; other runs' skills are never visible, so runs cannot contaminate each other.
