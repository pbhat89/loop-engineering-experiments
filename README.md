# The underwriting apprentice

An experiment in **loop engineering**: the design of the loop *around* an agent. Who tells it that it was wrong, what it is allowed to keep afterwards, and what it gets handed the next time similar work arrives.

One job, repeated thirty-eight times. Rate a life insurance application. Four designs run the identical job on the identical model against the identical feedback, and differ in exactly one thing each: what they keep between files.

Built on **LangGraph** with a SQLite checkpointer, on **synthetic data only**, scored by deterministic code against answers frozen by hash before any agent starts.

![Deviation falls as the files add up](articles/underwriting-apprentice/assets/learning_curve.png)

## The setup

Thirty training files with a senior's markup after each, then eight held-out files with memory frozen and no feedback at all. Every decision is answered by a **fresh model instance with no conversation history**, so nothing can be remembered except through the design's own memory.

The agent gets a 900-word starter manual containing every rating table, so a straightforward file can be rated exactly right from it alone. **Twelve house rules are never shown to anyone.** Each is learnable only by being corrected on it, and each fires in at least three training files in at least two different shapes.

| Design | Has when opening the file | Keeps when the file is done |
|---|---|---|
| `new_joiner` | The manual, nothing else | Nothing. Every file is day one |
| `notebook` | Plus every past markup, word for word | Appends the markup as written |
| `written_rules` | Plus a rule book it wrote itself | A second model call rewrites the book |
| `precedent` | Plus the three nearest past files and their answers | Files this case with its answer |

**Scoring** is one number: the average deviation from the actual rating, counted in positions along the rating ladder from Preferred Plus to Decline. Zero is an exact match. A postpone against a rating counts as two.

## Result

`uw_001`, committed in full under `artifacts/uw/uw_001/`. Lower is better.

| Design | 30 training files | 8 held-out files | Held-out exactly right |
|---|---|---|---|
| New joiner | 0.67 | 0.88 | 2 of 8 |
| Running notebook | 0.40 | 0.25 | 6 of 8 |
| Written rules | 0.33 | 0.25 | 6 of 8 |
| Precedent file | 0.47 | 0.38 | 5 of 8 |

Three things the data says:

- **Keeping anything beats keeping nothing, by a wide margin.** 0.25 against 0.88 on unseen work, same model, same manual, same eight files.
- **Two of the eight held-out files turn on a rule that appears in no training file, and all four designs missed both.** That puts the ceiling at six of eight, and the two note-taking designs reached it: every file that could be got right, they got. A learning loop captures only what its feedback has actually covered, so the coverage of your examples binds harder than the cleverness of your memory.
- **Cheap memory nearly matched clever memory.** Pasting the raw markups in reverse order landed level with a self-written rule book that cost a second model call on every file.

Two checks were registered before the run and both passed: the designs must be a dead heat over the first seven files, where they hold identical information, and performance on files the manual fully covers must not change with experience.

Read the write-up: **[articles/underwriting-apprentice/article.md](articles/underwriting-apprentice/article.md)**

## Honest framing

- **Synthetic data only.** The manual, the house rules and all thirty-eight applications are invented for the experiment. Nothing here is medical, actuarial, underwriting, pricing, legal or regulatory evidence.
- **External memory, not training.** The learning is Markdown and JSONL retrieved into the agent's context. No model weights change.
- **One run per design.** The ordering is the finding, the decimals are not. There are no error bars.
- **A model change mid-run.** `uw_001` began on Claude Fable 5.1 and the quota ran out with 37 of 258 calls outstanding, so `written_rules` and `ask_senior` finished on Claude Opus 5. Every case record stores the model that produced it, so the results split by model straight from the logs. See decision **D-02**.
- **A fifth design is in the code and excluded from the analysis.** `ask_senior` may ask up to four questions instead of keeping memory. It scored a perfect zero, because its senior was a deterministic lookup that always knew the answer. That measures the oracle, not the loop. See decision **D-03**.

## Quick start

Requires Python 3.12 or 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/pbhat89/loop-engineering-experiments.git
cd loop-engineering-experiments
uv sync --extra dev

uv run python -m src.underwriting.data verify   # regenerates the frozen data and checks the hash
uv run pytest                                   # 119 tests
```

To watch the machinery work without calling a model at all:

```bash
uv run python -m src.underwriting.run --run-id uw_demo --condition notebook --phase train --mode stub
uv run python scripts/summarize_uw_run.py --run-id uw_demo
```

## Running it for real, on whatever model you have

**There is no model client in this repository, and you do not need any particular provider to run it.** The graph pauses at every decision, writes a JSON request file, and waits for a JSON response file. Anything that can read one and write the other can be the operator: a Claude Code subagent on a subscription, a short script against any provider API, Gemini, an OpenAI model through Codex, a local model, or you with a text editor.

Set the labels in [`config/underwriting.yaml`](config/underwriting.yaml) so the logs record what answered:

```yaml
mode: manual                  # manual | stub
operator: claude-code-subagent
model_identifier: claude-opus-5
```

Those two fields are **labels written into every case record**, not client configuration. The one rule that affects the result: each call must be independent, with no history carried between files, or you are measuring a different experiment.

**[docs/REPRODUCING.md](docs/REPRODUCING.md)** has the step-by-step, including worked setups for Claude Code, the Anthropic, Gemini and OpenAI APIs and a local model, plus the call budget and how to check your results against the committed ones.

## What is in the repository

```
src/underwriting/       rating engine, case generator, scorer, the three memories, graph, runner
data/underwriting/      the frozen pack: starter manual, house rules, 38 files, answers, hashes
config/                 every knob, with comments explaining the value
scripts/                the summariser, which is the source of every number published
artifacts/uw/uw_001/    the committed run: 258 request and response pairs, per-file logs, memories
archive/                the stub smoke that gates the machinery before any model is called
docs/                   the pre-registered design, the decision log, the operator protocol, reproduction
articles/               the write-up and the figure pipeline that draws from the logs
tests/                  119 tests, including a leakage audit over every request file
```

**Where to start reading:** [docs/underwriting-apprentice-design.md](docs/underwriting-apprentice-design.md) is the pre-registration, committed before any code existed. [docs/decision-log.md](docs/decision-log.md) records every design decision and what was rejected. [docs/OPERATOR_PROTOCOL.md](docs/OPERATOR_PROTOCOL.md) is the contract between the runner and whatever answers it.

Two artifacts of the run are worth opening directly. `artifacts/uw/uw_001/written_rules/rulebook.md` is the rule book the agent wrote for itself across thirty revisions, which found the shape of the hidden rules and bracketed two thresholds slightly wrong while saying so out loud. `artifacts/uw/uw_001/notebook/markups.jsonl` is every correction the senior gave, which is exactly what that design keeps.

## Licence

MIT. See [LICENSE](LICENSE).
