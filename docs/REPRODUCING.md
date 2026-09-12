# Reproducing these experiments

Everything here runs from a clean clone. The parts that need no model run in a couple of minutes. The live experiment needs something that can answer 258 JSON requests, and you can plug in whatever you have.

## 1. Install

Python 3.12 or 3.13, and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/pbhat89/loop-engineering-experiments.git
cd loop-engineering-experiments
uv sync --extra dev
uv run pytest          # 314 tests, about four minutes
```

If `uv run` warns that `VIRTUAL_ENV` does not match the project environment, it is telling you it ignored an already-active venv and used the project's own. That is what you want.

## 2. Check the frozen data

The underwriting pack is generated from code and frozen by hash. This command regenerates all of it and compares:

```bash
uv run python -m src.underwriting.data verify
```

Expected, and it must match exactly:

```text
freeze_sha256: d95f49f1f9301ecf17facd75aa2d63353f179ea161aa18958f029cba882bee8d
underwriting data pack clean
```

That single check covers the starter manual, the fourteen house rules, all thirty-eight application files, every answer, the derived difficulty tiers and the whole schedule, including that every rule fires in at least three training files in at least two different shapes. If it reports drift, nothing downstream is comparable with the committed results.

## 3. Run it with no model at all

Deterministic stub operators answer every request. Useful for checking the machinery end to end before spending anything.

```bash
for arm in new_joiner notebook written_rules precedent; do
  uv run python -m src.underwriting.run --run-id uw_demo --condition "$arm" --phase train   --mode stub
  uv run python -m src.underwriting.run --run-id uw_demo --condition "$arm" --phase holdout --mode stub
done
uv run python scripts/summarize_uw_run.py --run-id uw_demo
```

Stub results are labelled stub everywhere they appear and are not a result about anything. They exist to prove the graph, the scorer, the memories and the leakage audit all work.

## 4. Run it live

### How the runner works

There is no model client in this repository. The graph pauses on a LangGraph `interrupt()` at every decision, writes a request file, and returns. You answer the request by writing a response file. You run the same command again and it resumes from its checkpoint.

```text
artifacts/uw/<run_id>/requests/<arm>/<phase>_case<NN>_<step>[_rN].json
artifacts/uw/<run_id>/responses/<arm>/<same file name>.json
```

`<phase>` is `train` or `holdout`. `<step>` is `decide`, or `reflect` for the written-rules arm, or `ask` for the ask-a-senior arm. Each request carries the file to rate, the starter manual, the arm's memory block, and a JSON schema for the answer. A response that fails validation is re-requested as `_r2` and then `_r3` with the errors attached.

Start an arm's `--phase holdout` only after its `--phase train` prints `DONE`. The four arms are independent and can proceed in parallel, but **the runner rewrites a shared `run.json`, so never have two runner processes running at once.**

```bash
uv run python -m src.underwriting.run --run-id uw_002 --condition notebook --phase train
#   OPERATOR NEEDED [notebook/train] -> artifacts/uw/uw_002/requests/notebook/train_case01_decide.json
#                    response -> artifacts/uw/uw_002/responses/notebook/train_case01_decide.json

uv run python -m src.underwriting.run status --run-id uw_002
```

Add `--poll` if you would rather the runner wait for each response file than return and be re-invoked.

### Option A: Claude Code subagents, on a subscription

This is how `uw_001` was produced. No API key is involved. For each request file, spawn one fresh subagent with the verbatim prompt template in [OPERATOR_PROTOCOL.md](OPERATOR_PROTOCOL.md), substituting only the two paths the runner printed. The agent definition is `.claude/agents/underwriter-operator.md`.

Rules that matter for the result:

- **One agent per request file.** Never reuse one, never give it conversation context. A stateless operator is the whole premise.
- **Never edit a response by hand.** A bad response becomes a new request; answer that instead.
- **Do not read request or response contents** while orchestrating, beyond checking a file exists.

### Option B: your own model provider

Write a small loop that watches the requests directory, sends `payload` plus `instructions` to your model, validates the reply against the embedded `response_schema`, and writes the response file. Roughly forty lines. Keep each call independent with no history, or you are measuring a different experiment.

The optional `anthropic` extra (`uv sync --extra anthropic`) installs `langchain-anthropic` if you prefer to wire a provider in directly. `ANTHROPIC_API_KEY` goes in a `.env` file, which is git-ignored. Copy `.env.example` to start.

### Budget

| Arm | Calls per file | Over 38 files |
|---|---|---|
| `new_joiner` | 1 | 38 |
| `notebook` | 1 | 38 |
| `written_rules` | 2 in training (decide, then reflect) | 68 |
| `precedent` | 1 | 38 |
| **total** | | **182** |

`uw_001` also ran a fifth `ask_senior` arm at 76 calls, making 258. That arm is excluded from the article for the reason recorded in decision **D-29**: its senior was a deterministic lookup that always knew the answer, so it measured the oracle rather than the loop. The code is still here if you want to build a better senior.

Each request is about 11 KB. `uw_001` took an evening, spread over several sessions because of rate limits. Nothing is lost to an interruption: every checkpoint and every file is on disk and the same command resumes.

## 5. Read the results

```bash
uv run python -m src.underwriting.run audit --run-id uw_002        # must print 0 problems
uv run python scripts/summarize_uw_run.py --run-id uw_002 --json artifacts/uw/uw_002/summary.json
uv run python articles/underwriting-apprentice/assets/make_figures.py --run-id uw_002
```

The **audit** is the one to run first. It checks every request file for house rule text or identifiers, point values, tier labels, the file's own answer or markup, and any number appearing in a rule statement but nowhere in the manual. If it reports anything other than zero, the agent could see what it was meant to work out, and the run is void.

The **summariser** prints per-arm results, per-tier means, the running series, and the three checks registered in advance:

1. Files 1 to 3 must be a dead heat across the arms that cannot ask.
2. Files the manual fully covers must stay flat for everyone.
3. The two held-out files turning on a rule absent from training should be missed by every arm that cannot ask.

Checks 1 and 2 are pass or fail. If either fails, information leaked between arms and the numbers mean nothing.

## 6. Compare against the committed run

`uw_001` is committed in full: 258 request and response pairs, per-file logs, the three memories, and `summary.json`. Expect your own numbers to differ. One file per design is a coin-flip's worth of noise in places, models change, and there are no error bars here. What should survive is the **ordering**: the arms that keep something beat the one that does not, by a wide margin, and all of them miss the two unlearnable held-out files.

Worth reading directly:

- `artifacts/uw/uw_001/written_rules/rulebook.md` and its thirty versions under `history/`. The rule book the agent wrote for itself, which found the shape of the hidden rules and bracketed two thresholds slightly wrong.
- `artifacts/uw/uw_001/notebook/markups.jsonl`. Every correction the senior gave, which is exactly what that arm keeps.
- `artifacts/uw/uw_001/precedent/filed_cases.jsonl`, with the nearest-neighbour distance recorded for every file.

## 7. The claims experiments

Experiments 1 to 6 use a synthetic healthcare claims dataset that is **not** redistributed here. Fetch it at the pinned revision first:

```bash
uv run python -m src.download_data
```

It reads `config/experiment.yaml` for the repository and commit, writes `data/raw/download_record.json` with sizes and hashes, and touches the network exactly once. The dataset is CC BY-NC 4.0; see [LICENSE](../LICENSE).

From there the pattern is the same file protocol with a different runner, `src/run_experiment.py`, driven by `config/experiment.yaml`. Each archived run under `archive/` carries the configuration it ran with. `docs/writeup.md` is the long-form record and `docs/decision-log.md` explains every choice.

## Troubleshooting

**`ModuleNotFoundError: langgraph.checkpoint.sqlite`** means you are running a Python that is not the project environment. Use `uv run`, or the interpreter in `.venv/`.

**The runner prints the same request twice.** It is idempotent and re-prints whatever is unanswered. Write the response file and run it again.

**Unicode errors on Windows.** Set `PYTHONIOENCODING=utf-8` before the command.

**A response keeps failing validation.** Read the `validation_errors` key in the `_r2` request. After two re-requests the answer is scored at the postpone-equivalent deviation of 2 and flagged `unparseable` in the log, so a stubborn operator degrades the result rather than stalling the run.
