# Operator protocol

One job repeated thirty-eight times: rate a life insurance application. Four published designs, plus a fifth kept
in the code and excluded from the analysis (D-03), differing only in what each is handed before it decides and what
each keeps afterwards. The pre-registered design is `docs/underwriting-apprentice-design.md` and the reasoning is
in `docs/decision-log.md`.

The graph never calls a model. It pauses, writes a request file, and waits for a response file. **Any model that can
read JSON and write JSON can be the operator**; `docs/REPRODUCING.md` shows how to wire one up. The run committed
here used stateless Claude Code subagents defined by `.claude/agents/underwriter-operator.md`, one fresh instance
per request file.

| Arm | Handed at decide time | Kept afterwards |
|---|---|---|
| `new_joiner` | the starter manual | nothing. Permanently on day one |
| `notebook` | + every past markup, verbatim, newest first | appends the markup as written (no model call) |
| `written_rules` | + its own house-rule book | a **reflection call** (a fresh instance) rewrites the whole book in its own words |
| `precedent` | + the 3 nearest past cases with their correct answers and the distance | files this case with its correct answer (no model call) |
| `ask_senior` | the starter manual; may first ask up to 4 questions | nothing. **Excluded from the published analysis** (D-03): the senior was a lookup that always knew the answer, so the arm measured the oracle, not the loop |

The ask-a-senior oracle is **deterministic code**, not a model (`src/underwriting/senior.py`): keyword routing over the house rules, gated on the rule being relevant to the case in hand, falling back to reading the manual section back and then to "Not something I can answer from here; use the manual."

## What the operator never sees

House-rule text or ids, point values of hidden rules, tier labels, golden answers, or any statement of what it is being measured on. `src/underwriting/audit.py` asserts this over **every** request file a run writes, and `python -m src.underwriting.run audit --run-id <id>` runs it. Two narrow exemptions, both deliberate: the ask-a-senior answers (quoting a rule out loud is that arm), and the operator's own rule book (its prose, not ours).

## Preconditions

1. `python -m src.underwriting.data verify` → `underwriting data pack clean`. This re-derives the manual, the house rules, the 38 cases and the goldens from code, compares them with `data/underwriting/`, re-checks the whole section-5 schedule, and verifies the freeze manifest. Freeze: `d95f49f1f930…`.
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

## Operator subagent prompt (verbatim template)

Spawned with the Agent tool, one fresh instance per request file:

> You are the **underwriting operator** for one step of the underwriting-apprentice experiment. Adopt `<REPO>/.claude/agents/underwriter-operator.md` as your operating instructions (read it first). Then read exactly one file — the request `<REQUEST_PATH>` — and write exactly one file — the response `<RESPONSE_PATH>` — as JSON conforming to the `response_schema` embedded in the request. Base every decision solely on the request contents; do not read or write any other file, run code, or use the network. Finish with one line naming the file you wrote and the decision you made.

Substitute `<REPO>` with the absolute path to your clone, and `<REQUEST_PATH>` and `<RESPONSE_PATH>` with the two paths the runner printed. Change nothing else. The prompt never names the arm, the case number, the tier or the phase.

Rules that matter for the result:

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
