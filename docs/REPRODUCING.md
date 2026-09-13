# Reproducing this experiment

Everything runs from a clean clone. The parts that need no model finish in a couple of minutes. The live experiment needs something that can answer 182 JSON requests, and you choose what that is.

## 1. Install

Python 3.12 or 3.13, and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/pbhat89/loop-engineering-experiments.git
cd loop-engineering-experiments
uv sync --extra dev
uv run pytest            # 145 tests, about two minutes
```

If `uv run` warns that `VIRTUAL_ENV` does not match the project environment, it is telling you it ignored an already-active venv and used the project's own. That is what you want.

## 2. Check the frozen data

The whole dataset is generated from code and frozen by hash. This regenerates all of it and compares:

```bash
uv run python -m src.underwriting.data verify
```

Expected, and it must match exactly:

```text
freeze_sha256: d95f49f1f9301ecf17facd75aa2d63353f179ea161aa18958f029cba882bee8d
underwriting data pack clean
```

That one check covers the starter manual, the fourteen house rules, all thirty-eight application files, every answer, the derived difficulty tiers and the whole schedule. Twelve of the fourteen rules are used in training, and the check includes that each of those twelve fires in at least three training files in at least two different shapes. The other two fire only in the held-out files, so no training feedback can teach them. If it reports drift, nothing downstream compares with the committed results.

## 3. Run it with no model at all

Deterministic stubs answer every request. Worth doing first: it proves the graph, the scorer, the memories and the leakage audit all work before you spend anything.

```bash
for arm in new_joiner notebook written_rules precedent; do
  uv run python -m src.underwriting.run --run-id uw_demo --condition "$arm" --phase train   --mode stub
  uv run python -m src.underwriting.run --run-id uw_demo --condition "$arm" --phase holdout --mode stub
done
uv run python scripts/summarize_uw_run.py --run-id uw_demo
```

A stub run records `mode: stub` in its run log and in every case record, and the figure script stamps a stub watermark on every figure it draws from such a run. The watermark keys on the mode, not on the run id, so it fires whatever you name the run. Stub output is not a result about anything.

## 4. How the live loop works

There is no model client in this repository. The graph pauses on a LangGraph `interrupt()` at every decision, writes a request file, and returns. You write the response file. You run the same command again and it resumes from its checkpoint.

```text
artifacts/uw/<run_id>/requests/<arm>/<phase>_case<NN>_<step>[_rN].json
artifacts/uw/<run_id>/responses/<arm>/<same file name>.json
```

`<phase>` is `train` or `holdout`. `<step>` is `decide`, or `reflect` for the written-rules design, or `ask` for the excluded ask-a-senior design.

```bash
uv run python -m src.underwriting.run --run-id uw_002 --condition notebook --phase train
#   OPERATOR NEEDED [notebook/train] -> artifacts/uw/uw_002/requests/notebook/train_case01_decide.json
#                    response -> artifacts/uw/uw_002/responses/notebook/train_case01_decide.json

uv run python -m src.underwriting.run status --run-id uw_002
```

Start an arm's `--phase holdout` only after its `--phase train` prints `DONE`. The arms are independent and can proceed in parallel, but **the runner rewrites a shared `run.json`, so never have two runner processes running at once.** Add `--poll` if you would rather the runner wait for each response file than return and be re-invoked.

### What a request looks like

```json
{
  "request_id": "uw_002:notebook:train:case03:decide:a1",
  "run_id": "uw_002", "condition": "notebook", "phase": "train",
  "case_index": 3, "case_id": "UW-T03", "step": "decide", "attempt": 1,
  "instructions": "Rate this life-insurance application. The starter manual ...",
  "payload":  { "case": {}, "manual": "...", "memory": {} },
  "response_schema": { "...": "JSON Schema for the answer" }
}
```

Send `instructions` plus `payload` to your model, require a reply matching `response_schema`, and write it to the response path. A reply that fails validation is re-requested as `_r2` and then `_r3` with the errors attached under `validation_errors`. After that the answer is scored at the postpone-equivalent deviation of 2 and flagged `unparseable`, so a stubborn operator degrades the result rather than stalling the run.

## 5. Configuring the model

Two fields in [`config/underwriting.yaml`](../config/underwriting.yaml):

```yaml
mode: manual                  # manual | stub
operator: claude-code-subagent
model_identifier: claude-opus-5
```

These are **labels stamped into every case record** so a reader can tell what produced an answer. They are not client configuration, because there is no client. Set them to whatever you actually used, for example `operator: gemini-cli` and `model_identifier: gemini-3-pro`.

**The one rule that changes the result: every call must be independent, with no conversation history carried between files.** A stateless operator is the premise of the whole experiment. If your operator remembers the previous file, the new-joiner design stops being a new joiner and the comparison is meaningless.

### Option A: Claude Code subagents, on a subscription

This is how `uw_001` was produced. No API key is involved. For each request file, spawn one fresh subagent with the verbatim prompt template in [OPERATOR_PROTOCOL.md](OPERATOR_PROTOCOL.md), substituting only the two paths the runner printed. The agent definition is [`.claude/agents/underwriter-operator.md`](../.claude/agents/underwriter-operator.md). Never reuse a subagent, and never edit a response by hand: a bad response becomes a new request, and you answer that instead.

### Option B: any API, in about forty lines

The worker below is provider-agnostic. Replace `call_model` and it works with Anthropic, Gemini, OpenAI, OpenRouter, Ollama or anything else that takes a prompt and returns text. Run it in one terminal and the runner with `--poll` in another.

```python
# worker.py  -- answers request files until you stop it
import json, time, pathlib

RUN = "uw_002"
REQ = pathlib.Path(f"artifacts/uw/{RUN}/requests")
RES = pathlib.Path(f"artifacts/uw/{RUN}/responses")

def call_model(prompt: str) -> str:
    """Swap this one function for your provider. Return raw text containing JSON.

    Anthropic:  client.messages.create(model=..., max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]).content[0].text
    Gemini:     client.models.generate_content(model=..., contents=prompt).text
    OpenAI:     client.responses.create(model=..., input=prompt).output_text
    Ollama:     requests.post("http://localhost:11434/api/generate",
                    json={"model": ..., "prompt": prompt, "stream": False}).json()["response"]

    Start a NEW call every time. Never pass previous messages.
    """
    raise NotImplementedError

def answer(path: pathlib.Path) -> None:
    req = json.loads(path.read_text(encoding="utf-8"))
    prompt = (
        f"{req['instructions']}\n\n"
        f"INPUT:\n{json.dumps(req['payload'], indent=1)}\n\n"
        f"Reply with JSON only, matching this schema:\n{json.dumps(req['response_schema'])}"
    )
    text = call_model(prompt).strip()
    text = text.removeprefix("```json").removeprefix("```").removesuffix("```")
    out = RES / path.parent.name / path.name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(json.loads(text), indent=1), encoding="utf-8")
    print("answered", out)

while True:
    pending = [p for p in REQ.rglob("*.json") if not (RES / p.parent.name / p.name).exists()]
    for p in sorted(pending):
        answer(p)
    time.sleep(3)
```

If you would rather wire a provider into the graph itself, `uv sync --extra anthropic` installs `langchain-anthropic`. Put the key in a `.env` file, which is git-ignored; copy `.env.example` to start. Never commit a real key.

### Budget

| Design | Calls per file | Over 38 files |
|---|---|---|
| `new_joiner` | 1 | 38 |
| `notebook` | 1 | 38 |
| `written_rules` | 2 in training (decide, then reflect) | 68 |
| `precedent` | 1 | 38 |
| **total** | | **182** |

Each request is about 11 KB. `uw_001` also ran the excluded `ask_senior` design at 76 calls, making 258, and took an evening across several sessions because of rate limits. Nothing is lost to an interruption: every checkpoint and file is on disk and the same command resumes.

## 6. Read the results

```bash
uv run python -m src.underwriting.run audit --run-id uw_002        # must print 0 problems
uv run python scripts/summarize_uw_run.py --run-id uw_002 --json artifacts/uw/uw_002/summary.json
uv run python articles/underwriting-apprentice/assets/make_figures.py --run-id uw_002   # -> artifacts/uw/uw_002/figures/
```

Run the **audit** first. It reads each request file whole, not the payload alone, and checks for house rule identifiers, tier words used as values, the file's own golden modifier keys or markup, and house rule statements matched as near-verbatim substrings. What it reliably catches is a verbatim splice of rule text or golden fields into a request, which is the realistic coding-bug failure mode. It does not claim to catch a paraphrase. Anything other than zero means the agent could see what it was meant to work out, and the run is void.

The **summariser** prints per-design results, per-tier means, the running series, decision accuracy over the training files and over all 38, how many of the eight held-out files each design rated exactly right, and the three checks registered in advance:

1. Files 1 to 3 must be a dead heat across the designs that cannot ask.
2. Files the manual fully covers must stay flat for everyone.
3. The two held-out files turning on the two rules absent from training should be missed by every design that cannot ask.

Checks 1 and 2 are pass or fail. If either fails, information leaked between designs and the numbers mean nothing.

The **figure script** writes into `artifacts/uw/<run-id>/figures/`, so your run cannot overwrite the charts published with the article. Redrawing those takes an explicit `--out articles/underwriting-apprentice/assets`.

## 7. Compare against the committed run

`uw_001` is committed in full: 258 request and response pairs, per-file logs, the three memories and `summary.json`. Expect your own numbers to differ. One file per design is a coin flip's worth of noise in places, models change, and there are no error bars here. What should survive is the **ordering**: the designs that keep something beat the one that does not by a wide margin, and all of them miss the two unlearnable held-out files.

Worth opening directly:

- `artifacts/uw/uw_001/written_rules/rulebook.md` and its thirty revisions under `history/`. The rule book the agent wrote for itself.
- `artifacts/uw/uw_001/notebook/markups.jsonl`. Every correction the senior gave.
- `artifacts/uw/uw_001/precedent/filed_cases.jsonl`, with the nearest-neighbour distance recorded for every file.

## Troubleshooting

**`ModuleNotFoundError: langgraph.checkpoint.sqlite`** means you are running a Python that is not the project environment. Use `uv run`, or the interpreter in `.venv/`.

**The runner prints the same request twice.** It is idempotent and re-prints whatever is unanswered. Write the response file and run it again.

**Unicode errors on Windows.** Set `PYTHONIOENCODING=utf-8` before the command.

**Every design scores the same.** Check you are not carrying conversation history between calls. That is the single mistake that collapses the experiment.
