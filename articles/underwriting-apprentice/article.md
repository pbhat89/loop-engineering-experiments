<!--
Title: The underwriting apprentice: five ways to make an agent learn on the job
Subtitle: A LangGraph experiment — one life insurance application rated thirty-eight times, and what each loop design actually kept
Tags: Loop Engineering, Agentic AI, LangGraph, Memory, Underwriting, Insurance
Photo credits:
  - assets/what_each_gets.png — "Image by Author" (matplotlib)
  - assets/learning_curve.png — "Image by Author" (matplotlib, from artifacts/uw/uw_001/<arm>/cases.jsonl)
  - assets/holdout.png — "Image by Author" (matplotlib, from artifacts/uw/uw_001/<arm>/cases.jsonl)
  - A stock hero photo (Unsplash: a desk of paper files, or a stack of forms) can be dropped in above the title.
-->

# The underwriting apprentice: five ways to make an agent learn on the job

*A LangGraph experiment — one life insurance application rated thirty-eight times, and what each loop design actually kept*

Every agent framework now advertises that its agents "learn from experience". Push on that claim and it usually turns out to be one of two things: a prompt somebody kept editing by hand, or a vector store of old conversations that nobody has ever measured. Neither is learning in the sense a manager means it. A manager means: the new person makes a mistake in week one, and by week six they don't make it any more.

I wanted to build the smallest honest test of that I could. Not "can an agent do the job" — models are good enough at most desk jobs now — but "does the *loop around* the agent accumulate anything, and which way of building that loop accumulates the most". That design question is what people have started calling loop engineering, and it is the actual subject here. Insurance is just the example.

The remarks below are my personal take basis building and running this over a couple of weekends. There is no branding or promotion here, and the data is entirely synthetic — no real applicants, no real carrier's manual.

## Why an underwriting desk?

My first attempt at this used a claims analytics dataset and six different analysis tasks. It failed, and the way it failed is the most useful thing I learned. Six different jobs, each exercising a different handful of conventions, gives you six one-shot trials wearing a trench coat. There is no learning curve to see, because nothing repeats.

A learning curve needs **the same job, done again and again, by someone who is getting corrected**. That is an apprenticeship. And individual life underwriting is close to a perfect laboratory version of one: a new underwriter gets a thick manual with every table in it, works files one at a time, and a senior marks up each one. The manual is not the job. The job is the manual *plus* the house practice that nobody wrote down.

> A new underwriter is not hired ignorant. They are hired with the book and without the practice.

## A one-minute primer on the setup

Three things you need to know before the results make sense.

**The starter manual.** Every design gets the same one, and it is a real working document — about 900 words, roughly thirty-five rules, and *every number is in it*: the build table, the blood pressure bands, lipids, A1c, tobacco, family history, occupation classes, avocations, driving record, the debit-to-class bands, the financial multiples. A clean file can be rated exactly right from the manual alone. This matters — I want the agent reading a manual, not guessing a hidden number from examples.

The manual is also honest about its own gaps, the way real manuals are. Lines like *"For combinations of cardiac risk factors, refer to underwriting judgement"* tell you where the unwritten knowledge sits, without telling you what it is. Remember that detail; it decides the whole experiment.

**Twelve house rules nobody is told.** Frozen before the run and never shown to anyone. Things like: a treated and controlled blood pressure carries the treatment charge only, not the reading on top; family-history debits lapse once the applicant is over 60; where the cholesterol band and the ratio band disagree, the ratio governs; a large face amount at a high multiple of income is postponed for financial evidence, not rated. Each one is *discrete* — learnable from a single correction. Each fires in at least three training cases, in at least two different shapes.

**One number to keep score.** Rating classes sit on a ladder: Preferred Plus, Preferred, Standard Plus, Standard, Table 2, Table 4, Table 6, Table 8, Decline. The score for a file is how many rungs away from the correct answer you landed. Zero is a perfect match with the reviewer. Postpone sits off the ladder and costs a flat two rungs when one side postpones and the other doesn't.

Thirty training cases with a reviewer markup after each, then eight held-out cases with memory frozen and no markup at all. Constant difficulty from case one — 30% clean, 43% needing one house rule, 27% needing two or three interacting. No gentle opening, because a gentle opening would make every line *rise* as the mix normalised, which is the opposite of the shape we're looking for.

## Five ways to close the loop

![What each design is handed, and what it keeps](assets/what_each_gets.png)
*Image by Author*

Underneath, all five are the same LangGraph state graph with a SQLite checkpointer. Every decision is answered by a **fresh model instance with no conversation history** — if the model remembered on its own, "new joiner" would mean nothing. What separates the five is only what each is handed before it decides, and what each keeps afterwards.

| The design | Handed before deciding | Kept afterwards |
|---|---|---|
| **New joiner** | The manual, nothing else | Nothing. Permanently on day one |
| **Running notebook** | Every past markup, verbatim, newest first | Appends the markup as written |
| **Written rules** | Its own house rule book | A second model call rewrites the whole book |
| **Precedent file** | The three nearest past cases with their correct answers | Files this case with its answer |
| **Ask a senior** | The manual, but may ask up to four questions first | Nothing. Pays the cost again every file |

The precedent file matches on attributes, not meaning — a weighted distance over age band, build, tobacco, each lab band, occupation class, avocation, driving record and the face-to-income multiple. Deterministic, explainable, and roughly how an underwriter actually searches.

The senior in "ask a senior" is not a model. It is deterministic code that routes a question to a house rule by keyword and answers narrowly and literally. Ask about the build table and you get the build table — which was already in your manual, and the question is wasted. I built it that way so a bad answer is always attributable to the question, never to a second model's mood.

## What happened over thirty cases

![How fast each design catches up](assets/learning_curve.png)
*Image by Author*

The first seven cases are a designed dead heat, and they came out as one. All four non-asking designs hold identical information there — every house rule that fires in those cases fires for the first time, so nobody has been corrected on anything yet. That check, and one other (performance on clean files, which the manual fully covers, must not change with experience — it stayed at a flat zero for all five), were registered before the run as the things that would void it. Both passed.

After that they separate, and they stay separated.

| Design | Training error (30 cases) | Files rated exactly right | Decision correct |
|---|---|---|---|
| New joiner | 0.67 rungs | 15 / 30 | 71% |
| Running notebook | 0.40 rungs | 21 / 30 | 89% |
| Written rules | 0.33 rungs | 23 / 30 | 89% |
| Precedent file | 0.47 rungs | 20 / 30 | 84% |
| Ask a senior | 0.00 rungs | 30 / 30 | 100% |

*Decision correct = accept / accept-with-modification / postpone / decline matched exactly, across all 38 files.*

The new joiner's line is the control, and it behaves like one: jagged, no trend worth the name, good on the easy files and wrong on the same kinds of file in case 28 that it was wrong on in case 8. The three memory designs bend down and stay down. Written rules reaches zero around case 15, wobbles, and finishes with six consecutive perfect files.

And then there is ask-a-senior, flat on zero the whole way, which I did not expect at all.

## The held-out test

Eight fresh files. Memory frozen — nothing is appended, no rules are rewritten. One attempt each, no markup, no second chance. The new joiner sits this one as herself, because an agent that keeps nothing *is* a new joiner by construction.

![Held-out cases](assets/holdout.png)
*Image by Author*

| Design | Held-out error | Files rated exactly right |
|---|---|---|
| New joiner | 0.88 rungs | 2 / 8 |
| Running notebook | 0.25 rungs | 6 / 8 |
| Written rules | 0.25 rungs | 6 / 8 |
| Precedent file | 0.38 rungs | 5 / 8 |
| Ask a senior | 0.00 rungs | 8 / 8 |

Two things worth sitting with.

The new joiner's held-out error of 0.88 rungs is almost exactly the 0.88 that a careful, literal reader of the manual alone scores on the same eight files. Thirty files of experience were available in that room and she had none of it. That is the honest measure of what the house practice is worth: roughly two-thirds of a rung per file, forever, for as long as nobody writes it down.

And **every design missed the two files that turn on a rule which never appeared in training** — except the one that could ask. Memory transfers what it has been corrected on, and not one inch further. If you take one line from this experiment, take that one. It is the ceiling on every "our agent learns from your data" claim you will read this year.

## What the rule-writer actually wrote

The most interesting artifact in the run is not a number, it is a file. The written-rules design rewrote its own book after every training case — thirty versions — and finished at about 48,000 characters, opening with a summary of where it believes house practice departs from the manual, then a numbered working order, then an entry per rule with *when it applies*, *boundary* and *why*, each citing the file that taught it.

It found the shape of the house rules. It got some of the thresholds slightly wrong. The real rule is that three or more cardiac factors together carry an interaction charge; the book settled on four. The real rule postpones a DUI inside three years; the book settled on two, and — this is the part I like — said so out loud:

> *Three years is untested: lean recent, postpone, and say judgement was used, because both corrections on this line were for accepting too soon.*

That is exactly right, and exactly what you would want a junior to write. The reviewer never states a number, so the book can only bracket the threshold from the corrections it has actually received. It knew the difference between what it had been taught and what it had inferred, and it wrote the difference down.

## Food for thought

> **The winner is the one that learns nothing.** Ask-a-senior was perfect on all thirty-eight files and my pre-registered prediction for it was 1.3 rungs. I was badly wrong, and the reason is the manual's *"refer to underwriting judgement"* lines. They are signposts. They tell a good asker precisely where the gap is, and the senior fills it on demand. Knowing what to ask turned out to be much cheaper than knowing the answer — but only because someone wrote an honest manual that admits where it stops.

> **It is also the most expensive design by a distance.** It asked **121 questions across 38 files**, a little over three per file, and it will ask three per file forever. That is a senior underwriter interrupted a hundred-odd times per apprentice, permanently. The memory designs pay their cost once, during training, and then pay nothing. If your "senior" is a human expert, ask-a-senior is the design you cannot afford; if it is a cheap deterministic lookup, it is the one you should reach for first.

> **Raw notes beat structured rules on effort-adjusted terms.** The notebook — which does nothing cleverer than paste every past markup in reverse order — landed at 0.25 rungs held out, identical to the rule book. The rule book needed a second model call after every single case to get there, 68 calls against the notebook's 38. On a longer run the notebook's context will eventually burst and the rule book's will not, so the crossover exists; on thirty cases it has not arrived.

> **Precedent was the weakest memory.** It carries *answers*, not *rules*. A near-identical past file helps enormously and a merely similar one quietly misleads, which is why it finished behind both note-takers.

## Learnings and future enhancement areas

- **One job repeated is the whole design.** The claims version of this experiment failed because six different tasks cannot produce a curve. If you are evaluating whether an agent improves, the first question is not which memory you use, it is whether your test set repeats.
- **Pre-register the checks that would void the run.** The dead heat over the first seven cases and the flat clean tier were both written down before any code ran. Had either failed, the honest finding would have been "something leaked" and this article would have said so.
- **This is one run per design, not a benchmark.** No error bars. The ordering is the finding; the exact decimals are not. Repeating each arm five times is the obvious next step and the one I would do first.
- **The manual is mine, so this measures learning a house style**, not learning underwriting. A real carrier's manual, and real markups from a real senior, would be a genuinely different and much harder test.
- **One honest wrinkle in the run itself.** I ran out of model quota with 37 of the 258 calls outstanding. The first 167 files were rated by Claude Fable 5.1; written rules and ask-a-senior finished their last cases and took their whole held-out test on Claude Opus 5. Every case record stores the model that produced it, so the run can be split by model from the logs. It does not touch the training curve, which is Fable throughout for the three complete designs, but it does mean **those two designs' held-out numbers are not strictly like-for-like** against the other three. I would rather say that plainly than quietly average it away.
- **What I would build next:** a retirement rule for memory (nothing here ever forgets, and a wrong early lesson would persist forever), a cost-weighted score so a Table 2 written as Table 4 is not scored the same as a decline written as an accept, and a hybrid arm that keeps a rule book *and* may ask when the book is silent — which, on this evidence, is what an actual apprentice does.

## References

1. Madaan et al., *Self-Refine: Iterative Refinement with Self-Feedback* (2023) — the self-review loop.
2. Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning* (2023) — verbal feedback as memory.
3. Wang et al., *Voyager: An Open-Ended Embodied Agent with Large Language Models* (2023) — the growing skill library.
4. Zhao et al., *ExpeL: LLM Agents Are Experiential Learners* (2023) — insights extracted from past trials.
5. LangGraph documentation — `interrupt()` / `Command(resume=)` and checkpointers: https://langchain-ai.github.io/langgraph/

*Every number in this article comes from the run logs in `artifacts/uw/uw_001/<design>/cases.jsonl` and is reproduced by `scripts/summarize_uw_run.py`. The cases, goldens, manual and house rules are frozen by hash before the run.*
