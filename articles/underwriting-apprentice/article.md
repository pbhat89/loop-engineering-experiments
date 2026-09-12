<!--
Title: The underwriting apprentice: four ways to make an agent learn on the job
Subtitle: A LangGraph experiment in loop engineering — one life insurance application rated thirty-eight times, and what each design actually kept
Tags: Loop Engineering, Agentic AI, LangGraph, Memory, Underwriting, Insurance
Photo credits:
  - assets/what_each_gets.png — "Image by Author" (matplotlib)
  - assets/learning_curve.png — "Image by Author" (matplotlib, from artifacts/uw/uw_001/<arm>/cases.jsonl)
  - assets/holdout.png — "Image by Author" (matplotlib, from artifacts/uw/uw_001/<arm>/cases.jsonl)
  - A stock hero photo (Unsplash: a desk of paper files, or a stack of forms) can be dropped in above the title.
-->

# The underwriting apprentice: four ways to make an agent learn on the job

*A LangGraph experiment in loop engineering — one life insurance application rated thirty-eight times, and what each design actually kept*

Every agent framework now advertises that its agents "learn from experience". Push on that claim and it usually turns out to be one of two things: a prompt somebody kept editing by hand, or a vector store of old conversations that nobody has ever measured. Neither is learning in the sense a manager means it. A manager means: the new person makes a mistake in week one, and by week six they don't make it any more.

So this article is not really about insurance. It is about the **loop** you build around an agent — who tells it that it was wrong, what it is allowed to keep afterwards, and what it gets handed the next time a similar job lands. Those choices are the product. People have started calling the discipline loop engineering, and the honest way to test it is to build several loops that differ in exactly one thing each, then run the same work through all of them and see which one accumulates anything.

The remarks below are my personal take basis building and running this over a couple of weekends. There is no branding or promotion here, and the data is entirely synthetic — no real applicants, no real carrier's manual.

## Why an underwriting desk?

My first attempt at this used a claims analytics dataset and six different analysis tasks. It failed, and the way it failed is the most useful thing I learned. Six different jobs, each exercising a different handful of conventions, gives you six one-shot trials wearing a trench coat. There is no learning curve to see, because nothing repeats.

A learning curve needs **the same job, done again and again, by someone who is getting corrected**. That is an apprenticeship. And individual life underwriting is close to a perfect laboratory version of one: a new underwriter is handed a thick manual with every table in it, works files one at a time, and a senior marks up each one. The manual is not the job. The job is the manual *plus* the house practice that nobody ever wrote down.

> A new underwriter is not hired ignorant. They are hired with the book and without the practice.

## A one-minute primer on the setup

Three things you need before the results make sense.

**The manual everybody gets.** The same one for every design, and it is a real working document — about 900 words, roughly thirty-five rules, and *every number is in it*: the build table, blood pressure bands, lipids, A1c, tobacco, family history, occupation classes, avocations, driving record, the debit-to-class bands, the financial multiples. A straightforward file can be rated exactly right from the manual alone. That matters. I wanted an agent reading a manual, not reverse-engineering a hidden number from examples.

The manual is also honest about its own gaps, the way real manuals are. Lines like *"For combinations of cardiac risk factors, refer to underwriting judgement"* tell you where the unwritten knowledge sits without telling you what it is.

**Twelve house rules nobody is told.** Frozen before the run and never shown. Things like: a treated and controlled blood pressure carries the treatment charge only, not the reading on top; family-history debits lapse once the applicant is over 60; where the cholesterol band and the ratio band disagree, the ratio governs; a large face amount at a high multiple of income is postponed for financial evidence rather than rated. Each one is *discrete* — learnable from a single correction. Each fires in at least three training files, in at least two different shapes, so nobody can learn it too narrowly and still pass.

**One number to keep score.** Rating classes sit on a ladder: Preferred Plus, Preferred, Standard Plus, Standard, Table 2, Table 4, Table 6, Table 8, Decline. The score for a file is how many rungs away from the senior's answer you landed. Zero is a perfect match. Postpone sits off the ladder and costs a flat two rungs when one side postpones and the other does not.

Thirty training files with a senior's markup after each, then eight held-out files with memory frozen and no markup at all. Constant difficulty from file one — 30% straightforward, 43% needing one house rule, 27% needing two or three interacting. No gentle opening, because a gentle opening would make every line *rise* as the mix normalised, which is the opposite of the shape we are looking for.

## Four ways to close the loop

![What each design has, and what it keeps](assets/what_each_gets.png)
*Image by Author*

Underneath, all four are the same LangGraph state graph with a SQLite checkpointer. Every decision is answered by a **fresh model instance with no conversation history** — if the model remembered on its own, "new joiner" would mean nothing. What separates the four is only what each has when it opens the file, and what each keeps when the file is done.

| The design | What they have when they open the file | What they keep when the file is done |
|---|---|---|
| **New joiner** | The manual, and nothing else | Nothing. Every file is day one again |
| **Running notebook** | The manual, plus every comment the senior has ever written, word for word | Pastes the senior's comment into the notebook exactly as written |
| **Written rules** | The manual, plus a rule book they have written themselves | Turns the new correction into a rule in their own words and rewrites the book |
| **Precedent file** | The manual, plus the three most similar past files and how each was rated | Files this case away with its correct answer |

The notebook is the cheapest thing imaginable — no summarising, no filtering, just paste and re-read. The rule book is the expensive version: after every file, a second model call rereads the whole book alongside the new correction and rewrites it. The precedent file matches on attributes rather than meaning — a weighted distance over age band, build, tobacco, each lab band, occupation class, avocation, driving record and the face-to-income multiple. Deterministic, explainable, and roughly how an underwriter actually searches.

## What happened over thirty-eight files

![Error falls as the files add up](assets/learning_curve.png)
*Image by Author*

This is the whole experiment in one picture. Each line is the running average of rating error over every file done so far, so it answers the question a manager actually asks: *across everything this person has touched, how far off have they been?*

For the first seven files all four lines sit exactly on top of one another, which is why you only see one. That was designed and pre-registered as a condition for the run to count: every house rule that fires in those files fires there for the *first* time, so nobody has been corrected on anything yet and all four hold identical information. Had they separated there, something had leaked and the run would have been void. A second check was registered the same way — performance on straightforward files, which the manual fully covers, must not change with experience. It stayed flat at zero for all four, start to finish.

From file eight they fan out and they never come back together.

| Design | Error over 30 training files | Files rated exactly right | Decision correct |
|---|---|---|---|
| New joiner | 0.67 rungs | 15 / 30 | 71% |
| Running notebook | 0.40 rungs | 21 / 30 | 89% |
| Written rules | 0.33 rungs | 23 / 30 | 89% |
| Precedent file | 0.47 rungs | 20 / 30 | 84% |

*Decision correct = accept / accept-with-modification / postpone / decline matched exactly, across all 38 files.*

The new joiner's line is the control and it behaves like one. It drifts down a little — a capable model does pick up some house practice from general knowledge, and the running average of a jagged series flattens by arithmetic alone — but it is wrong on the same kinds of file at file 28 that it was wrong on at file 8. Nothing is being retained, because there is nothing to retain it in.

The three memory designs pull away and then **flatten out around file 25**. That flattening is not a stall, and it is worth being clear about why. Error cannot go below zero, the straightforward files were never going to be wrong, and by file 25 each design has been corrected on most of the twelve house rules at least once. There is simply less left to learn. Where a line settles is the interesting number, not whether it is still falling.

## The held-out test

The shaded region on the right is where it gets interesting. Eight fresh files, memory frozen — nothing appended, no rules rewritten — one attempt each, no markup, no second chance. The new joiner sits this one as herself, because an agent that keeps nothing *is* a new joiner by construction.

Watch what the running average does when the feedback stops. The new joiner's line **turns upward**, from 0.67 to 0.71. The other three keep falling. That is the entire finding in one gesture: the designs that kept something walk into unseen work and do better than their own track record, and the one that kept nothing does worse.

![Held-out cases](assets/holdout.png)
*Image by Author*

| Design | Error on the 8 held-out files | Rated exactly right |
|---|---|---|
| New joiner | 0.88 rungs | 2 / 8 |
| Running notebook | 0.25 rungs | 6 / 8 |
| Written rules | 0.25 rungs | 6 / 8 |
| Precedent file | 0.38 rungs | 5 / 8 |

Two things worth sitting with.

The new joiner's 0.88 rungs is almost exactly the 0.88 that a careful, literal reader of the manual alone scores on the same eight files. Thirty files of experience existed in that room and she had access to none of it. That is the honest price of house practice nobody writes down: roughly two-thirds of a rung per file, forever.

And **every design missed the two files that turn on a house rule which never appeared in training**. All four, equally, at a full rung each. Memory transfers what it has been corrected on and not one inch further. If you take one line from this experiment, take that one. It is the ceiling on every "our agent learns from your data" claim you will read this year.

## What the rule-writer actually wrote

The most interesting artifact in the run is not a number, it is a file. The written-rules design rewrote its own book after every training file — thirty versions — finishing at about 48,000 characters: a summary of where it believes house practice departs from the manual, a numbered working order, then an entry per rule with *when it applies*, *boundary*, and *why*, each citing the file that taught it.

It found the shape of the house rules. It got some thresholds slightly wrong. The real rule is that three or more cardiac factors together carry an interaction charge; the book settled on four. The real rule postpones a DUI inside three years; the book settled on two — and, this is the part I like, said so out loud:

> *Three years is untested: lean recent, postpone, and say judgement was used, because both corrections on this line were for accepting too soon.*

That is exactly what you would want a junior to write. The senior never states a number, so the book can only bracket the threshold from the corrections it has actually received. It knew the difference between what it had been taught and what it had inferred, and it wrote the difference down.

## Food for thought

> **Cheap memory did almost as well as clever memory.** The notebook does nothing smarter than paste every past comment in reverse order, and it finished level with the rule book on the held-out files and a third of a rung behind over training. The rule book needed a second model call after every single file to get there — 68 calls against the notebook's 38. On a longer run the notebook's context will eventually burst and the rule book's will not, so a crossover exists. On thirty files it has not arrived. Before you build a summarisation-and-retrieval layer, check whether pasting the raw log gets you most of the way.

> **Precedent was the weakest of the three memories.** It carries *answers*, not *rules*. A near-identical past file helps enormously, and a merely similar one quietly misleads — which is why it finished behind both note-takers despite having the richest thing in its hands.

> **The gap that matters is not between the memory designs.** It is between having one and not: 0.25 against 0.88 on unseen work, the same model, the same manual, the same eight files. Everything else in this article is a rounding error next to that.

> **Where do you put the effort?** On this evidence, into the *feedback* rather than the memory. All three memory designs converge to a similar place because they are all fed the same markup. The senior's comment is the scarce input; the container you pour it into matters much less than people building agent frameworks currently assume.

## Learnings and future enhancement areas

- **One job repeated is the whole design.** The claims version of this experiment failed because six different tasks cannot produce a curve. If you are evaluating whether an agent improves, the first question is not which memory you use, it is whether your test set repeats.
- **Pre-register the checks that would void the run.** The dead heat over the first seven files and the flat performance on straightforward files were both written down before any code ran. Had either failed, the honest finding would have been "something leaked", and this article would have said so.
- **A fifth design did not make the cut, and the reason is instructive.** I also built an *ask a senior* arm, which keeps no memory but may ask up to four questions before deciding. It scored a perfect zero on all thirty-eight files — which tells you about my senior, not about the design. I had implemented the senior as a deterministic lookup that always knew the right answer, so it was an oracle, not a colleague. A real senior is an experienced average: the manual, a bit more knowledge, and their own blind spots. Modelling that properly is a better experiment than the one I ran, and it is the first thing I would add.
- **This is one run per design, not a benchmark.** No error bars. The ordering is the finding; the exact decimals are not. Repeating each design five times is the obvious next step.
- **The manual is mine, so this measures learning a house style**, not learning underwriting. A real carrier's manual and real markups from a real senior would be a genuinely different and much harder test.
- **One honest wrinkle in the run itself.** I ran out of model quota partway through. New joiner, running notebook and precedent file were rated end to end by Claude Fable 5.1; the written-rules design finished its last two training files and its whole held-out test on Claude Opus 5. Every case record stores the model that produced it, so the run can be split by model straight from the logs. The clean three-way comparison is therefore the other three designs, and I would treat the written-rules held-out number as indicative rather than like-for-like. I would rather say that plainly than quietly average it away.
- **What I would build next:** a retirement rule for memory, since nothing here ever forgets and a wrong early lesson would persist forever; a cost-weighted score, so a Table 2 written as Table 4 is not penalised the same as a decline written as an accept; and a design that keeps a rule book *and* may ask when the book is silent — which, on this evidence, is what an actual apprentice does.

## References

1. Madaan et al., *Self-Refine: Iterative Refinement with Self-Feedback* (2023) — the self-review loop.
2. Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning* (2023) — verbal feedback as memory.
3. Wang et al., *Voyager: An Open-Ended Embodied Agent with Large Language Models* (2023) — the growing skill library.
4. Zhao et al., *ExpeL: LLM Agents Are Experiential Learners* (2023) — insights extracted from past trials.
5. LangGraph documentation — `interrupt()` / `Command(resume=)` and checkpointers: https://langchain-ai.github.io/langgraph/

*Every number in this article comes from the run logs in `artifacts/uw/uw_001/<design>/cases.jsonl` and is reproduced by `scripts/summarize_uw_run.py`. The files, answers, manual and house rules are frozen by hash before the run.*
