# The Underwriting Apprentice - experiment design (v3, approved 2026-09-11)

Text export of the design artifact agreed with the lead before the build.

The Underwriting Apprentice
- 
- 
- 

 Loop engineering · experiment design · v2, for approval

# The Underwriting Apprentice

 Five ways to close a learning loop, tested on one job done thirty-eight times: rate a life insurance application.

 30training cases

 8held-out cases

 5loop designs

 12hidden house rules

 ~400model calls

 The claims version failed for one structural reason: six different jobs, each exercising a different handful of conventions. A learning curve needs the same job repeated. This design gives it one job, thirty-eight times, against a body of unwritten practice deep enough that thirty cases do not exhaust it.

 Every agent is a fresh Claude Haiku instance with no conversation history. The only thing separating the five designs is what each is handed before it decides, and what each keeps afterwards. The declining error curve is the validation. If the memory designs do not bend down, the honest finding is that these loops do not capture house knowledge, and that is what gets published.

 1

## The manual everyone gets

 The starter manual is a real working document, not a set of hints. It carries every number: the base debit tables for build, blood pressure, lipids, A1c, tobacco and family history, the occupation classes, the debit-to-class band mapping, and the decision vocabulary. About thirty-five rules. A straightforward case can be rated exactly right from it alone.

 It is also honest about its own gaps, the way real manuals are. Lines like "for combinations of cardiac risk factors, refer to underwriting judgement" tell the reader where the unwritten knowledge sits without saying what it is.

### Starter manual · extract
given to all five, unchanged

 BMI 19.0–27.9 → 0 · 28.0–30.9 → 25 · 31.0–33.9 → 50 · 34.0–36.9 → 100 · ≥ 40 → decline

 A1c ≤ 6.4 → 0 · 6.5–6.9 → 50 · 7.0–7.9 → 75 · 8.0–8.9 → 125 · ≥ 9.0 → decline

 Lipid ratio ≤ 5.0 → 0 · 5.1–6.5 → 25 · > 6.5 → 50

 Bands: 0–49 Standard · 50–99 Table 2 · 100–149 Table 4 · 150–199 Table 6

 "For combinations of cardiac risk factors, refer to underwriting judgement."

 2

## The twelve house rules nobody is told

 Frozen before the run and never shown. Each one is discrete, which is the whole point: a fact like this is learnable from a single correction, whereas a numeric band would have to be estimated from hundreds of entangled examples. That was the flaw in v1 of this design, and it would have produced a null result.

 House rule | The naive error it prevents | 

 Treated, controlled BP charges the treatment band only | Double-charging treatment and reading | 

 Private pilot under 100 hrs/yr is always a flat extra, never a rating | Rating the aviation, or declining it outright | 

 Family-history debits lapse once the applicant is over 60 | Charging a 63-year-old for a father's early MI | 

 Three or more cardiac factors together add a 25-debit interaction charge | Treating correlated risks as independent | 

 T2D diagnosed after 45 with A1c under 7.0 earns a 25-debit credit | Missing the late-onset allowance | 

 Occupation class C plus a hazardous avocation takes an exclusion, not a flat extra | Reaching for the wrong instrument | 

 Where total cholesterol and the ratio disagree, the ratio governs | Following the wrong number | 

 Face over $1M at more than 20× income is a postpone for financials | Rating a case that needs more paper | 

 Eight of twelve shown. Each fires in three different training cases, in at least two different case shapes, so a learner cannot capture it too narrowly and still succeed.

 3

## The cases

 About fifteen structured fields, roughly 150 words each, generated from the manuals so difficulty is controlled rather than accidental. Each carries a little detail that does not matter, so knowing what to ignore is part of the job.

 Difficulty does not ramp. The same mix runs from case 1 to case 30. If cases got harder as they went, difficulty and experience would move together and the curve would be unreadable: a flat line would secretly mean improvement. Holding the mix constant makes the new joiner's line flat and jagged, good on the easy ones and bad on the hard ones forever, while the learners' lines bend down.

 And no easy opening. Starting with clean cases would put every line low and then send it up as the mix normalised, which is the opposite of the shape we are looking for. Everyone starts high and together instead, because at case 1 the four non-asking designs hold exactly the same information.

 Tier | Share | What it takes | Who gets it right | 

 Clean | 30% | The starter manual alone | Everyone, throughout | 

 Judgement | 45% | Manual plus one house rule | Only someone corrected on that rule before | 

 Compound | 25% | Two or three house rules, interacting | Only someone who has accumulated several | 

### Case 14 · a compound case
shown to the agent

 ApplicantM, 47

 Product20-yr term, $750,000

 Build5'10", 214 lb · BMI 30.7

 Tobacconever

 BP138/86, treated 2021

 LipidsTC 232, HDL 41 · ratio 5.7

 A1c6.7 · T2D dx 2022, metformin

 Familyfather MI at 62, mother living

 Occupationregional sales mgr · class A

 Avocationprivate pilot, 80 hrs/yr, 640 total, no aerobatics

 MVRone speeding citation, 2024

 Financial$180k income, $250k in force

 The manual alone gets you to 150 debits and Table 6, with the aviation rated or declined. Two house rules move it: the treated-BP rule removes 25, and the aviation rule converts a rating into a flat extra.

 4

## The answer, and the one number we track

 Pref+0

 Pref1

 Std+2

 Std3

 Tab 24

 Tab 45

 Tab 66

 Tab 87

 Decline8

### Correct answer, case 14
never shown

 Decision  accept with modification

 Rating    Table 4  (125 debits: build 25 · BP 25 · ratio 25 · A1c 50)

 Modifier  flat extra $2.50 per $1,000 — aviation, no rating debits

 Drivers   A1c band · build · lipid ratio · aviation

 Rating distance in ladder steps is the headline metric, and it is what "degrees of risk off" means in practice. Postpone sits off the ladder and scores a fixed two steps when it is wrong either way.

 Also scored | How | 

 Decision | Exact match across accept / accept-with-modification / postpone / decline | 

 Modifiers | F1 over required flat extras and exclusion riders, band included | 

 Drivers | Recall of the factors the rulebook actually charged for | 

### What the reviewer says afterwards

 The correct answer and which factors were material. Never a threshold, never a point value. This is what a senior's markup looks like, and it is what keeps the house rules learnable without being copyable.

 Rating was one step too severe. The blood pressure is treated and controlled, so it should not carry the reading charge as well. Aviation at this level takes a flat extra, not a rating.

 5

## The five loop designs

 One attempt per case, then review. No retries inside a case, because underwriters do not resubmit. All the learning happens across cases, which is the only place we want to look.

### The shared spine, every case, every design

 1A fresh agent instance opens the case file. No history from any previous case.

 2It reads the starter manual, plus whatever its own design hands it.

 3It returns decision, rating, modifiers and drivers.

 4The reviewer scores it against the hidden house rules and writes the markup.

 5The design-specific memory is updated, or not.

 Design | Handed to it at step 2 | Kept at step 5 | 

 New joiner | The starter manual, nothing else | Nothing. Permanently on day one | 

 Running notebook | Every past markup, verbatim, newest first | Appends the markup as written | 

 Written rules | Its own house-rule book, the entries whose trigger matches | Writes or rewrites a rule in its own words | 

 Precedent file | The three nearest past cases with their correct answers | Files this case with its correct answer | 

 Ask a senior | Nothing extra, but may ask up to four questions, answered narrowly and literally from the hidden rules. It chooses how many; usage is recorded | Nothing. Pays the cost again every case | 

### Two design decisions worth challenging
my calls

 Precedent is matched on attributes, not meaning. A weighted distance over age band, build, tobacco, each lab band, condition flags, occupation class, avocation and driving record. Deterministic, explainable, and how an underwriter actually searches. The nearest-neighbour distance gets published for every held-out case, so we can see whether precedent is doing real work or has found a near-twin.

 Ask a senior keeps no memory on purpose, or it collapses into the notebook. Two things keep it honest. The budget is chosen by the agent up to four and recorded, so what a question is worth becomes a measurement rather than an assumption. And the senior answers narrowly and literally: ask about the build table and you get the build table, which was already in your manual and the question is wasted. Knowing what to ask is itself the expertise this design lacks, which is why it should sit well short of an experienced colleague rather than level with one.

 It is also the arm that prices the alternative to building memory. Thirty cases at two to four questions is sixty to a hundred and twenty interruptions of a senior's day, and it never stops, while the memory designs pay nothing after training. If scope has to be cut, this is still the first arm to go.

 6

## What success looks like, written down in advance

 Predictions, published before the run so the story cannot be fitted to the data afterwards. Mean rating distance in ladder steps, plotted continuously across all thirty cases as a trailing five-case mean. In the real chart the raw per-case results sit behind each line as faint dots, so nothing is smoothed away.

 2.01.51.00.50

 - - 
 - - 
 
 - 
 
 1510
 15202530
 
 case number
 mean rating error, ladder steps

 New joiner
 Running notebook
 Written rules
 Precedent file
 Ask a senior

 Flattening near the bottom is the success signal, not a stall. Error cannot fall below zero, and the clean cases were never going to be wrong.

 Design | Case 1–5 | Case 26–30 | Held-out | Shape | 

 New joiner | 1.8 | 1.8 | 1.9 | Flat and jagged. Never learns | 

 Running notebook | 1.8 | 0.6 | 0.8 | Steady decline, then the floor | 

 Written rules | 1.8 | 0.6 | 0.8 | Slower start, similar finish | 

 Precedent file | 1.8 | 0.9 | 1.1 | Good on repeats, weak on the novel | 

 Ask a senior | 1.3 | 1.2 | 1.2 | Helps at once, never improves, pays every case | 

 Ask-a-senior is the only design that legitimately starts below the rest, because it can buy help on case 1. It also stays clearly short of an experienced colleague: four questions cannot cover twelve house rules, and a compound case fires three at once.

### Built-in validation

 - Cases 1 to 3 must be a dead heat for the four non-asking designs. They hold identical information there. If they differ by more than sampling noise, something has leaked and the run is void.

 - The clean tier must stay flat for everyone. Experience should not change performance on cases the manual already covers. If it does, the memory is interfering rather than helping.

 - Two held-out cases fire a rule that never appeared in training. Everyone should miss those. That is the honest limit: memory transfers what it has been corrected on, and nothing else.

 7

## Held-out test

 Eight fresh cases, memories frozen, one attempt each, no feedback. Same difficulty mix. The new joiner runs it as herself, because an agent that keeps nothing is a new joiner by construction. Ask-a-senior may still ask, since that is the whole of what it is, and its question count is reported as its running cost.

 Two honest limits, stated up front in the write-up. The manual is realistic in shape but the numbers are mine, so this measures learning a house style rather than learning underwriting. And it is one run per design unless we repeat it, so the ordering is the finding and the exact sizes are not.

 Roughly sixty percent of the existing build carries over: the LangGraph loop, the memory arms, the seeding and leakage audit, the logging and the figure pipeline. Replaced: the executor and the scorer. About four hundred small-model calls, one unattended evening.
