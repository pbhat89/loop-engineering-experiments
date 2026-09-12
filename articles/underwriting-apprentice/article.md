<!--
Title: The underwriting apprentice: four ways to make an agent learn on the job
Subtitle: A LangGraph experiment in loop engineering. One life insurance application rated thirty-eight times, and what each design actually kept.
Tags: Loop Engineering, Agentic AI, LangGraph, Memory, Underwriting, Insurance
Photo credits:
  - assets/what_each_gets.png, "Image by Author" (matplotlib)
  - assets/learning_curve.png, "Image by Author" (matplotlib, from artifacts/uw/uw_001/<arm>/cases.jsonl)
  - assets/holdout.png, "Image by Author" (matplotlib, from artifacts/uw/uw_001/<arm>/cases.jsonl)
  - A stock hero photo (Unsplash: a desk of paper files, or a stack of forms) can be dropped in above the title.
-->

# The underwriting apprentice: four ways to make an agent learn on the job

*A LangGraph experiment in loop engineering. One life insurance application rated thirty-eight times, and what each design actually kept.*

Every agent framework now advertises that its agents "learn from experience". Push on that claim and it usually turns out to be one of two things: a prompt somebody kept editing by hand, or a vector store of old conversations that nobody has ever measured. Neither is learning in the sense a manager means it. A manager means the new person makes a mistake in week one, and by week six they don't make it any more.

So this article is not really about insurance. It is about the **loop** you build around an agent. Who tells it that it was wrong, what it is allowed to keep afterwards, and what it gets handed the next time a similar job lands. Those choices are the product. People have started calling the discipline loop engineering, and the honest way to test it is to build several loops that differ in exactly one thing each, then push the same work through all of them and see which one accumulates anything.

The remarks below are my personal take basis building and testing this over a couple of weekends. There is no branding or promotion here, and the data is entirely synthetic. No real applicants, no real carrier's manual.

## Why an underwriting desk?

My first attempt at this used a claims analytics dataset and six different analysis tasks. It failed, and the way it failed is the most useful thing I learned. Six different jobs, each exercising a different handful of conventions, gives you six one-shot trials wearing a trench coat. There is no learning curve to see, because nothing repeats.

A learning curve needs **the same job, done again and again, by someone who is getting corrected**. That is an apprenticeship. And individual life underwriting is close to a perfect laboratory version of one. A new underwriter is hired and given only a manual to decide from. There is no prior experience. Files arrive one at a time, and a senior marks up each one.

The manual is not the job. The job is the manual, plus the house practice that nobody ever wrote down.

## What the underwriter is actually given

Two things, and it is worth seeing both before the results.

**The file.** About fifteen structured fields, roughly a page. Here is one of the thirty-eight, shortened a little:

```text
Applicant:     M, age 37
Product:       30-year term, face $750,000
Build:         6'2", 206 lb, BMI 26.4; weight stable
Tobacco:       quit more than 5 years ago; nicotine screen negative
Blood pressure:121/76, untreated
Lipids:        total cholesterol 204, HDL 47, ratio 4.3
A1c:           5.7; no diabetes diagnosis
Occupation:    office administrator, class A
Driving:       0 moving violations in 3 years; DUI conviction 2024
Sleep apnea:   diagnosed, no CPAP in use
Financial:     income $175,000, $400,000 already in force
Also on file:  collects first-edition crime novels
```

Every file carries one detail that does not matter, because knowing what to ignore is part of the job.

**The manual.** The same one for everybody, about 900 words and roughly thirty-five rules, and every number is in it. A straightforward file can be rated exactly right from the manual alone. Four lines out of the thirty-five, to give you the flavour:

> **Build.** Read the BMI: up to 18.9, charge 25. 19.0 to 27.9, charge nothing. 28.0 to 30.9, charge 25. 31.0 to 33.9, charge 50.
>
> **Driving record.** Moving violations in the last 3 years: 0 to 1, nothing. 2, charge 25. 3 or more, charge 50. A DUI conviction: rate 50.
>
> **Sleep apnea.** Diagnosed sleep apnea, charge 50.
>
> **Classes.** Add the charges and read the class off the total: 0 to 49 Standard, 50 to 99 Table 2, 100 to 149 Table 4, 150 to 199 Table 6.

Work the file above with only that, and you get a clean answer: fifty for the DUI, fifty for the untreated apnea, one hundred in total, Table 4, accept. It is a defensible reading and it is wrong, which is the whole point of the exercise. What it is missing is coming up next.

## The twelve rules nobody is told

Frozen before anybody started and never shown to anyone. Things like: a treated and controlled blood pressure carries the treatment charge only, not the reading on top. Family history charges lapse once the applicant is over 60. Where the cholesterol band and the ratio band disagree, the ratio governs. A large face amount at a high multiple of income is postponed for financial evidence rather than rated.

And the one that decides the file above: **a recent DUI is postponed, not rated.** The correct answer is not Table 4. It is postpone, with the apnea noted underneath.

Each rule is discrete, so it is learnable from a single correction. Each one fires in at least three training files and in at least two different shapes, so nobody can learn it too narrowly and still pass.

The manual is honest about where it stops, the way real manuals are. Underneath the driving table it says *"For a recent motoring conviction, refer to underwriting judgement."* That tells you a gap exists. It does not tell you what fills it.

**Keeping score.** Rating classes sit in a fixed order: Preferred Plus, Preferred, Standard Plus, Standard, Table 2, Table 4, Table 6, Table 8, Decline. The score for a file is how many classes away from the senior's answer you landed. Zero is a perfect match. A postpone that should have been a rating, or the reverse, costs a flat two.

Thirty training files with a markup after each, then eight held-out files with memory frozen and no markup at all. Constant difficulty from file one. No gentle opening, because a gentle opening would make every line rise as the mix normalised, which is the opposite of the shape we are looking for.

## Four ways to close the loop

![What each design has, and what it keeps](assets/what_each_gets.png)
*Image by Author*

Underneath, all four are the same LangGraph state graph with a SQLite checkpointer. Every decision is answered by a **fresh model instance with no conversation history**. If the model remembered on its own, "new joiner" would mean nothing.

| The design | What they have when they open the file | What they keep when the file is done |
|---|---|---|
| **New joiner** | The manual, and nothing else | Nothing. Every file is day one again |
| **Running notebook** | The manual, plus every comment the senior has ever written, word for word | Pastes the senior's comment into the notebook exactly as written |
| **Written rules** | The manual, plus a rule book they have written themselves | Turns the new correction into a rule in their own words and rewrites the book |
| **Precedent file** | The manual, plus the three most similar past files and how each was rated | Files this case away with its correct answer |

The clearest way to think about the middle two is as **two different documents in an office**.

The **running notebook** is the team's shared record. It is the manual being extended as you go: every correction the senior writes is appended, nothing is interpreted, and anyone who walks in can pick it up and read it. It is institutional memory, and it costs nothing to maintain because no thinking is done to it.

The **written rules** book is one underwriter's own reflections. After every file they reread their whole book alongside the new correction and rewrite it in their own words, in the form *when this applies, do this, and here is why*. That is what specialisation looks like, and it costs a second model call every single file.

The **precedent file** is the third instinct, which is to not generalise at all and just find the closest previous case. It matches on attributes rather than meaning, using a weighted distance over age band, build, tobacco, each lab band, occupation class, avocation, driving record and the face-to-income multiple. Deterministic, explainable, and roughly how an underwriter actually searches.

## What happened over thirty-eight files

![Error falls as the files add up](assets/learning_curve.png)
*Image by Author*

This is the whole experiment in one picture. Each line is the running average of how far off the rating was, over every file done so far. It answers the question a manager actually asks: across everything this person has touched, how good have they been?

For the first seven files all four lines sit exactly on top of one another, which is why you only see one. That was designed, and registered in advance as a condition for the experiment to count. Every house rule that fires in those files fires there for the first time, so nobody has been corrected on anything yet and all four hold identical information. Had they separated there, something had leaked and the results would have been void. A second check was registered the same way: performance on straightforward files, which the manual fully covers, must not change with experience. It stayed flat at zero for all four, start to finish.

From file eight they fan out, and they never come back together.

| Design | Classes off, over 30 training files | Files rated exactly right | Decision correct |
|---|---|---|---|
| New joiner | 0.67 | 15 of 30 | 71% |
| Running notebook | 0.40 | 21 of 30 | 89% |
| Written rules | 0.33 | 23 of 30 | 89% |
| Precedent file | 0.47 | 20 of 30 | 84% |

*Decision correct means accept, accept with modification, postpone or decline matched exactly, across all 38 files.*

The new joiner's line is the control and it behaves like one. It drifts down a little, because a capable model does pick up some house practice from general knowledge and because a running average of a jagged series flattens by arithmetic alone. But it is wrong on the same kinds of file at file 28 as it was at file 8. Nothing is retained, because there is nowhere to retain it.

The three memory designs pull away and then **flatten out around file 25**. That flattening is not a stall, and it is worth being clear about why. Error cannot go below zero, the straightforward files were never going to be wrong, and by file 25 each design has been corrected on most of the twelve rules at least once. There is simply less left to learn. Where a line settles is the interesting number, not whether it is still falling.

## The held-out test

The shaded region on the right is where it gets interesting. Eight fresh files, memory frozen, nothing appended and no rules rewritten. One attempt each, no markup, no second chance. The new joiner sits this one as herself, because an agent that keeps nothing is a new joiner by construction.

Watch what the running average does when the feedback stops. The new joiner's line **turns upward**, from 0.67 to 0.71. The other three keep falling. That is the finding in one gesture: the designs that kept something walk into unseen work and do better than their own track record, and the one that kept nothing does worse.

![Held-out cases](assets/holdout.png)
*Image by Author*

| Design | Classes off, on the 8 held-out files | Rated exactly right |
|---|---|---|
| New joiner | 0.88 | 2 of 8 |
| Running notebook | 0.25 | 6 of 8 |
| Written rules | 0.25 | 6 of 8 |
| Precedent file | 0.38 | 5 of 8 |

Two things worth sitting with.

The new joiner's 0.88 is almost exactly the 0.88 that a careful, literal reader of the manual alone scores on the same eight files. Thirty files of experience existed in that office and she had access to none of it. That is the honest price of house practice nobody writes down: about two thirds of a class per file, forever.

And **every design missed the two files that turn on a house rule which never appeared in training.** All four, equally, by a full class each. Memory transfers what it has been corrected on and not one inch further. If you take one line from this article, take that one. It is the ceiling on every "our agent learns from your data" claim you will read this year.

## What actually got written down

The abstract claim is that memory carries house practice. Here is what that looks like in the files themselves.

**A page from the running notebook.** This is the senior's comment on the DUI file from the top of this article, pasted in exactly as written, and it is the whole of what the notebook keeps:

> UW-T06: This one needed postponing rather than rating. On review the file should have been postponed. The material factors are DUI and sleep apnea. A recent DUI is postponed, not rated.

Nothing is added and nothing is interpreted. Note what is absent: no threshold, no number, no "within N years". The senior states practice, never a parameter. Whoever reads this later has to work out how recent is recent.

**An entry from the written rules book.** The other design took the same correction and turned it into its own rule, which after thirty files reads:

> **2. DUI.** *When it applies:* a DUI conviction appears on the file.
>
> *Within two years of the application, postpone.* Settled at one year and at two. Decision postpone, class null, modifiers empty. Then finish the file and name 'DUI'.
>
> *Older than two years:* charge the manual's rate and say judgement was used on recency. Three years is untested: lean recent, postpone, and say judgement was used, because both corrections on this line were for accepting too soon.

That is exactly what you would want a junior to write. The real house rule is three years, and the book settled on two, because two is all it had ever been shown. What I find genuinely impressive is the last sentence. It knows the difference between what it was taught and what it inferred, it says which way to lean when it is outside its evidence, and it explains why. The finished book ran to about 48,000 characters across twenty entries, each one citing the files that taught it.

## Food for thought

> **Is a shared notebook as good as a specialist?** This is the question I would most like a reader to argue with me about. If a new joiner can walk in, pick up the team's updated notes and match the underwriter who spent thirty files writing their own, then specialisation buys nothing and only the shared record matters. On the held-out files the two scored the same. Over the training files, where both ran on the same model, the personal rule book was modestly ahead. I would not call that settled either way, and the honest reading is that the shared notebook gets you most of the distance for a fraction of the effort.

> **In this setup, nothing lives in the person.** That is worth saying plainly, because it bounds what the experiment can claim. Every file is decided by a fresh model instance with no memory of anything, so all of the experience has to live in a document. What is being compared is therefore which document carries experience best, not whether an experienced person beats a newcomer holding their notes. For anyone building agent systems that is the more useful comparison anyway, since your agents are stateless too.

> **Cheap memory did almost as well as clever memory.** The notebook does nothing smarter than paste every past comment in reverse order. The rule book needed a second model call after every single file, 68 calls against the notebook's 38. On a longer stretch the notebook's context will eventually burst and the rule book's will not, so a crossover exists. At thirty files it has not arrived. Before you build a summarisation and retrieval layer, check whether pasting the raw log gets you most of the way.

> **Precedent was the weakest of the three memories.** It carries answers, not rules. A near-identical past file helps enormously, and a merely similar one quietly misleads, which is why it finished behind both note-takers despite holding the richest thing of the three.

> **The gap that matters is not between the memory designs.** It is between having one and not: 0.25 against 0.88 on unseen work, same model, same manual, same eight files. Everything else here is a rounding error next to that.

## Learnings and future enhancement areas

- **One job repeated is the whole design.** The claims version of this experiment failed because six different tasks cannot produce a curve. If you are evaluating whether an agent improves, the first question is not which memory you use, it is whether your test set repeats.
- **Write down in advance what would void the results.** The dead heat over the first seven files, and flat performance on straightforward files, were both recorded before any code was written. Had either failed, the honest finding would have been "something leaked", and this article would have said so.
- **A fifth design did not make the cut, and the reason is instructive.** I also built an *ask a senior* design, which keeps no memory but may ask up to four questions before deciding. It scored a perfect zero on all thirty-eight files, which tells you about my senior rather than about the design. I had implemented the senior as a lookup that always knew the right answer, so it was an oracle, not a colleague. A real senior is an experienced average: the manual, somewhat more practice, and their own blind spots. Modelling that properly is a better experiment than the one I did, and it is the first thing I would add.
- **Each design did this once, so this is not a benchmark.** No error bars. The ordering is the finding, the exact decimals are not. Repeating each design five times is the obvious next step.
- **The manual is mine, so this measures learning a house style**, not learning underwriting. A real carrier's manual and real markups from a real senior would be a genuinely different and much harder test.
- **One honest wrinkle.** I ran out of model quota partway through. New joiner, running notebook and precedent file were rated end to end by Claude Fable 5.1. The written rules design finished its last two training files and its whole held-out test on Claude Opus 5. Every case record stores the model that produced it, so the results can be split by model straight from the logs. The clean three-way comparison is therefore the other three designs, and I would treat the written rules held-out number as indicative rather than like-for-like. I would rather say that plainly than quietly average it away.
- **What I would build next:** a retirement rule for memory, since nothing here ever forgets and a wrong early lesson would persist indefinitely. A cost-weighted score, so a Table 2 written as Table 4 is not penalised the same as a decline written as an accept. And a design that keeps a rule book and may also ask when the book is silent, which on this evidence is what an actual apprentice does.

## References

1. Madaan et al., *Self-Refine: Iterative Refinement with Self-Feedback* (2023), the self-review loop.
2. Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning* (2023), verbal feedback as memory.
3. Wang et al., *Voyager: An Open-Ended Embodied Agent with Large Language Models* (2023), the growing skill library.
4. Zhao et al., *ExpeL: LLM Agents Are Experiential Learners* (2023), insights extracted from past trials.
5. LangGraph documentation, `interrupt()` / `Command(resume=)` and checkpointers: https://langchain-ai.github.io/langgraph/

*Every number in this article comes from the per-file logs in `artifacts/uw/uw_001/<design>/cases.jsonl` and is reproduced by `scripts/summarize_uw_run.py`. The files, answers, manual and house rules are frozen by hash beforehand. The full manual and the complete rule list are in the repo.*
