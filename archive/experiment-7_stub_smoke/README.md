# Archive - experiment 7 stub smoke (2026-09-11)

**STUB. Not a result.** No model was called anywhere in this folder. Every answer came from
one of the two deterministic stub operators in `src/underwriting/stub.py`:

- `naive` - returns `rate_manual_only(case)`: a careful reader of the starter manual who has
  learned nothing.
- `learner` - switches on any house rule whose markup sentence or spoken statement it can find
  in its own memory block or senior answers, then rates with those. With an empty memory block
  it is exactly `naive`. Both runs below used `learner`.

The learner is an **upper bound** on what an arm's memory could deliver if the operator applied
every correction perfectly. It is not a prediction of what Claude Fable 5.1 will do.

Frozen data pack: `freeze_sha256 d95f49f1f9301ecf17facd75aa2d63353f179ea161aa18958f029cba882bee8d`.
Leakage audit over every request file in both runs: **0 problems**.

`checkpoints/` is not archived - it is a LangGraph SQLite database the runner rebuilds, and it
was 4.7 MB for the smoke and 22 MB for the full pass. The full pass's request/response
transcript is not archived either (3.8 MB); its per-case logs are what it is here for.

## `uw_stub_smoke/` - the gate the build brief asks for

All five arms, end to end, 6 training cases then 2 held-out, memories frozen for the held-out
phase. Complete request/response transcript included.

| arm | train mean ladder distance | held-out mean | decision match | modifier F1 | driver recall | questions |
|---|---|---|---|---|---|---|
| new_joiner | 1.167 | 1.000 | 0.667 | 0.833 | 0.893 | 0 |
| notebook | 1.167 | 1.500 | 0.667 | 0.833 | 0.893 | 0 |
| written_rules | 1.167 | 1.500 | 0.667 | 0.833 | 0.893 | 0 |
| precedent | 1.167 | 1.000 | 0.667 | 0.833 | 0.893 | 0 |
| ask_senior | 0.167 | 0.000 | 1.000 | 1.000 | 1.000 | 25 |

The four non-asking arms are identical over six cases, and that is correct rather than
disappointing: the schedule spreads each house rule across the whole run, so in cases 1-6 every
rule that fires is firing for the first time and no memory can have been corrected on it yet.
The smoke is a mechanism check - graph routing, the file protocol, memory writes, the freeze,
the leakage audit - not a learning curve. The notebook and written-rules arms score *worse*
than the new joiner on the two held-out cases (1.50 against 1.00), which is the honest
signature of partial knowledge: six cases of corrections leave them applying one rule of a
three-rule case and overshooting.

Validation checks: cases 1-3 a dead heat across the four non-asking arms **PASS**; clean tier
flat for every arm at 0.000 **PASS**.

## `uw_stub_full/` - the same five arms over the whole 30 + 8

Logs and memory stores only. This is the mechanism check that the smoke is too short to show:
that the arms separate at all when the memory has had time to fill.

| arm | train mean | first 5 | last 5 | held-out | held-out novel-rule cases | questions |
|---|---|---|---|---|---|---|
| new_joiner | 0.933 | 1.000 | 1.200 | 0.875 | 1.000 | 0 |
| notebook | 0.367 | 1.000 | 0.000 | 0.250 | 1.000 | 0 |
| written_rules | 0.367 | 1.000 | 0.000 | 0.250 | 1.000 | 0 |
| precedent | 0.933 | 1.000 | 1.200 | 0.875 | 1.000 | 0 |
| ask_senior | 0.033 | 0.200 | 0.000 | 0.125 | 0.500 | 120 |

Reading it, with the stub's limits stated:

- **new_joiner 0.933 flat** is the floor of learnable error in this design: the mean ladder
  distance between `rate_manual_only` and the golden over the thirty training cases. A live
  model sits above it, because it also misreads bands; nothing can sit below it without the
  house rules.
- **notebook and written_rules fall to zero** over the last five cases. Both memories carry the
  markup sentences verbatim, so a perfect applier ends up with all twelve rules.
- **precedent tracks the new joiner exactly.** Its memory carries past *answers*, not rules, and
  the stub does no inference from an answer to a rule. Whether a model can make that leap is
  precisely the open question the arm exists to ask; the stub cannot answer it.
- **ask_senior 0.033** is the ceiling, not a forecast. The stub asks perfectly aimed questions
  drawn from a bank keyed on the case attributes, which is the expertise the arm is supposed to
  lack. It is also the only arm that scores on the two novel-rule held-out cases (0.500), because
  the senior knows rules 13 and 14 and will say them if asked.
- **Everyone misses the novel-rule held-out cases** except the asking arm. That is the honest
  limit the design registered in advance.

## Reproducing

```bash
python -m src.underwriting.data verify
for arm in new_joiner notebook written_rules precedent ask_senior; do
  python -m src.underwriting.run --run-id uw_stub_smoke --condition $arm --phase train   --mode stub --max-cases 6
  python -m src.underwriting.run --run-id uw_stub_smoke --condition $arm --phase holdout --mode stub --max-cases 2
done
python -m src.underwriting.run audit --run-id uw_stub_smoke
python scripts/summarize_uw_run.py --run-id uw_stub_smoke
```

Drop `--max-cases` for the full 30 + 8 pass.
