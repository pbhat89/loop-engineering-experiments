# Build brief: the Underwriting Apprentice (experiment 7)

Owner of this brief: the lead (Fable 5.1 main session). Builder: an Opus subagent. Runner: a Sonnet orchestrator
spawning **Claude Fable 5.1** operators (model `fable`), one fresh instance per request. The approved design is
`docs/underwriting-apprentice-design.md`; where this brief is more specific than the design, this brief wins; where
it deviates from the design, the deviation is listed in the decision log (D-27) and in section 9 here.

## 0. Constraints that never move (from the original project brief)

- LLM calls only through Claude Code subagents on the user's subscription. No API key, no SDK client, no proxying or
  extraction of Claude Code session credentials. `anthropic_api` mode stays unused.
- Synthetic data only. Every applicant is generated. No PHI, no real names.
- No secrets in source, logs, artifacts or dashboards.
- Never report a live-LLM result that is not in the run logs. Stub results are labelled stub everywhere.
- Commit at phase boundaries with clear messages. Never push.
- The operator (the underwriter agent) never sees: house-rule text or ids, point values of hidden rules, tier
  labels, golden answers, or any test for what it is being measured on. A test asserts this on every request payload.

## 1. What is being built

One job repeated 38 times: rate a life-insurance application. 30 training cases with a reviewer markup after each,
then 8 held-out cases with memories frozen and no markup. Five loop designs (arms), identical in every respect
except what is handed to the agent before it decides and what is kept afterwards:

| arm id | handed at decide time | kept afterwards |
|---|---|---|
| `new_joiner` | starter manual | nothing |
| `notebook` | starter manual + every past markup verbatim, newest first | appends the markup as written (automatic, no LLM call) |
| `written_rules` | starter manual + its own house-rule book | a **reflection call** (fresh instance) rewrites the rule book in its own words |
| `precedent` | starter manual + the 3 nearest past cases with their correct answers | files this case with its correct answer (automatic) |
| `ask_senior` | starter manual; may first ask up to 4 questions, answered narrowly and literally by a deterministic oracle | nothing |

Headline metric: rating distance in ladder steps. Ladder: Pref+ 0, Pref 1, Std+ 2, Std 3, Table 2 4, Table 4 5,
Table 6 6, Table 8 7, Decline 8. Postpone is off the ladder: if exactly one of (agent, golden) is postpone the
distance is a fixed 2; both postpone = 0. Also scored per case: decision exact match (accept / accept with
modification / postpone / decline), modifier F1 (flat extras and exclusion riders, band included), driver recall.

Plot: mean rating distance per arm, continuous across cases 1-30 as a trailing 5-case mean (cases 1-4 use the
cases available so far), faint per-case dots behind each line; held-out shown separately (mean per arm, with the two
novel-rule cases broken out).

## 2. Reuse map (read these before writing anything)

Reuse, do not re-implement: the LangGraph loop pattern with `interrupt()` / `Command(resume=)` and `SqliteSaver`
(`src/claims_graph.py`, `src/graph_nodes.py`), the manual-mode request/response file protocol and polling runner
(`src/run_experiment.py`, `docs/OPERATOR_PROTOCOL.md`), the raw-log memory store shape (`src/feedback_memory.py`),
the skill-store idea for the rule book (`src/skill_store.py` if useful), the freeze manifest + SHA approach,
`scripts/archive_run.py`, `scripts/summarize_run.py`, the figure style in
`articles/loop-engineering-markdown-skills/assets/make_figures.py`, and the operator agent definition pattern in
`.claude/agents/experiment-operator-blind.md`. Import from the existing modules where the interface fits; otherwise
copy the pattern into the new package. Do not modify the claims experiment's behaviour or its tests.

New package: `src/underwriting/`. New config: `config/underwriting.yaml`, generated frozen data under
`data/underwriting/` (cases, goldens, manual, house rules, freeze manifest). New artifacts under
`artifacts/uw/<run_id>/`. New tests under `tests/underwriting/`.

## 3. The starter manual (`data/underwriting/starter_manual.md`, also as structured tables in code)

Roughly 35 rules, every number present, about 900 words. Generated from the same Python tables the golden engine
uses, so manual and engine cannot disagree. Sections:

1. Decision vocabulary: accept, accept with modification (flat extra and/or exclusion rider), postpone, decline.
2. Debit-to-class bands: 0-49 Standard, 50-99 Table 2, 100-149 Table 4, 150-199 Table 6, 200-249 Table 8, 250+ decline.
   Std+ / Pref / Pref+ eligibility: zero debits, plus all-labs-in-preferred-limits criteria you define (BMI, BP,
   lipids, A1c, tobacco never / quit > 5 yr, no ratable impairment, clean MVR). Give the three preferred tiers
   distinct criteria so they are decidable from the manual.
3. Build: BMI 19.0-27.9 -> 0, 28.0-30.9 -> 25, 31.0-33.9 -> 50, 34.0-36.9 -> 100, 37.0-39.9 -> 150, >= 40 -> decline,
   < 19.0 -> 25. Height/weight given; BMI is given too.
4. Blood pressure, untreated reading bands, and a treatment band ("on treatment: 25") - written so a naive reader
   would charge both the reading and the treatment.
5. Lipids: total cholesterol bands AND ratio bands (TC/HDL <= 5.0 -> 0, 5.1-6.5 -> 25, > 6.5 -> 50), both present,
   with no statement about which governs when they disagree.
6. A1c: <= 6.4 -> 0, 6.5-6.9 -> 50, 7.0-7.9 -> 75, 8.0-8.9 -> 125, >= 9.0 -> decline. Type 2 diabetes: "rate on A1c".
7. Tobacco: never / quit > 5 yr = non-smoker; quit 1-5 yr = 25; current = smoker rates (decide how the smoker class
   maps onto the ladder for scoring and document it). Nicotine-positive lab with "never" declared = smoker. Say
   nothing about cannabis.
8. Family history: parent or sibling with MI / stroke / cancer before 60: 25 per event, max 50. No age qualifier.
9. Occupation classes A (0), B (25), C (50, "hazardous"). Examples for each.
10. Avocations: private aviation ("refer to underwriting judgement"), scuba (depth bands), climbing, motorsport,
    with debits or flat extras stated for the ones that are not hidden rules.
11. MVR: moving violations bands; DUI "rate 50" with no recency qualifier.
12. Alcohol / liver: elevated liver enzymes 25; alcohol treatment history 50.
13. Sleep apnea: 50. Say nothing about treatment.
14. Financial: income multiples by age band for face amount; "refer" language above the multiple.
15. Modifiers: flat-extra bands ($ per $1,000: 2.50 / 5.00 / 7.50) and exclusion-rider wording.
16. Honest gap lines, one per hidden-rule area, e.g. "For combinations of cardiac risk factors, refer to underwriting
    judgement." These say where the gap is, never what fills it.

## 4. The house rules (`src/underwriting/house_rules.py`, `data/underwriting/house_rules.json`; never shown)

Twelve training rules. Each has: id, trigger (code over case fields), effect (debit change / decision change /
modifier change), a markup sentence in words with no numbers, and oracle keyword sets (see 7). 1-8 are from the
approved design; 9-12 are the lead's additions in the same spirit; 13-14 appear only in held-out cases.

1. Treated, controlled BP charges the treatment band only (no reading charge on top).
2. Private pilot under 100 hrs/yr: flat extra $2.50/1,000, never rating debits, never decline.
3. Family-history debits lapse once the applicant is over 60.
4. Three or more cardiac risk factors together (from: BP debit, lipid debit, A1c debit, BMI >= 31, current smoker,
   family cardiac history) add a 25-debit interaction charge.
5. T2D diagnosed after 45 with A1c under 7.0 earns a 25-debit credit (floor 0).
6. Occupation class C plus a hazardous avocation takes an exclusion rider for the avocation, not a flat extra.
7. Where total cholesterol and the ratio disagree, the ratio governs (charge the ratio band only).
8. Face over $1M at more than 20x income is a postpone for financials.
9. Weight lost in the past 12 months is added back at half before the BMI band is read.
10. A DUI inside the last 3 years is a postpone, not a rating.
11. Sleep apnea on documented CPAP compliance carries no debit.
12. Elevated liver enzymes under 2x normal with no alcohol history carry no debit.
13. (held-out only) Two first-degree relatives with the same cancer before 60 add a second 25 on top of the cap.
14. (held-out only) Scuba below 100 ft or any cave/wreck penetration takes a flat extra $5.00/1,000 regardless of dives.

If any of 9-14 cannot be made consistent with the manual, replace it with something equally discrete and realistic
and record why in D-27. Every rule must be decidable from the case fields alone.

## 5. Cases (`src/underwriting/cases.py` -> `data/underwriting/cases.json`, `goldens.json`)

Seeded generator (seed 42), about 15 fields, about 150 words when rendered. Fields: applicant sex/age, product,
face amount, height/weight/BMI, weight change last 12 months, tobacco (declared + lab), BP reading + treatment status
+ year, lipids TC/HDL/ratio, A1c + diabetes dx year + medication, family history, occupation + class, avocation with
detail, MVR, alcohol/liver, sleep apnea + CPAP, financials (income, in-force), and one irrelevant detail per case.

Two engines: `rate_manual_only(case)` (what a careful reader of the manual alone produces) and `rate_house(case)`
(manual + house rules) = the golden. Tier is derived, not assigned: clean = no house rule changes the outcome;
judgement = exactly one rule changes the outcome; compound = two or three. The generator draws candidates and keeps
those that satisfy the schedule:

- Training: 30 cases: 9 clean, 14 judgement, 7 compound. Each of rules 1-12 fires in >= 3 training cases and in >= 2
  distinct shapes (shape = the set of other rules firing with it, or a different tier). Rules 13-14 never fire in
  training. The mix is constant: every window of 10 consecutive cases has 3 clean (+/-1), 4-5 judgement, 2-3
  compound; case 1 is not clean.
- Held-out: 8 cases: 2 clean, 4 judgement (2 of which fire only rule 13 or 14), 2 compound. Same field distributions.
- Every case's golden has: decision, rating class, debit breakdown, modifiers, drivers (the factors charged),
  fired rule ids, tier. Goldens and rule ids live only in `data/underwriting/goldens.json`, never in a request.

Freeze: SHA-256 of manual, house rules, cases, goldens -> `data/underwriting/freeze_manifest.json`. A test asserts
the manifest matches. Commit before the live run.

## 6. Scoring and the reviewer markup (`src/underwriting/scorer.py`, `markup.py`)

Per case: ladder distance (section 1), decision match, modifier F1, driver recall, plus the raw answer. The markup
is templated from the golden and the fired rules: the correct decision and class and modifiers in words, the
material factors, and each fired rule's markup sentence; direction words ("one step too severe") computed from the
distance sign. Never a threshold, never a point value. A test asserts the markup contains no digits other than the
case id and the class names ("Table 2" etc. are allowed). For a wrong clean case: "The manual covers this case; the
<factor> band was misread." For a correct case: a one-line confirmation naming the material factors.

## 7. Arm mechanics (`src/underwriting/memory.py`, `precedent.py`, `senior.py`)

- notebook: `artifacts/uw/<run>/notebook/markups.jsonl`; shown newest first, all of them (30 max, no cap needed).
- written_rules: `artifacts/uw/<run>/written_rules/rulebook.md` plus a version history. After each training case a
  **reflection request** (phase `reflect`) hands a fresh instance: the current rule book, the case as shown, its own
  answer, the markup; it returns the full rewritten rule book (markdown, <= 25 entries, each entry: when / do / why
  in the operator's own words). The whole book is shown at decide time (deviation from the design's "entries whose
  trigger matches"; recorded in D-27 - the book is small and retrieval failures would confound the arm).
- precedent: `artifacts/uw/<run>/precedent/cases.jsonl`. Distance = weighted sum over: age band (|band diff|),
  BMI band, tobacco status, BP band + treated flag, lipid band, A1c band, diabetes flag, family-history flag,
  occupation class, avocation category, MVR band, DUI recency flag, sleep-apnea flag, liver flag, face/income
  multiple band. Weights documented in code; deterministic; ties broken by recency. Shows the 3 nearest with their
  correct answers (decision, class, modifiers, drivers) and the distance. Logs the nearest distance for every case.
- ask_senior: phase `ask` first: the operator returns 0-4 questions. The oracle answers each deterministically:
  if a house rule's required keyword set (e.g. rule 1: {"blood pressure"|"bp"} and {"treated"|"medication"|
  "controlled"}) is fully present AND that rule is relevant to the case, return the rule's literal statement
  (numbers allowed - a senior may say them); else if a manual topic matches, return that manual section verbatim
  (already in the manual: the question was wasted); else "Not something I can answer from here; use the manual."
  The senior knows rules 13-14 too. Then phase `decide` with the answers appended. Question count recorded per case.

## 8. Graph, runner, protocol, stub

- `src/underwriting/graph.py`: one `StateGraph`, condition-aware routers: `load_case -> [ask_senior] -> decide ->
  score -> markup -> [reflect] -> update_memory -> advance`. `interrupt()` at `ask`, `decide`, `reflect`. Held-out
  phase: no markup shown, memory read-only, no reflect. `SqliteSaver` under `artifacts/uw/<run>/checkpoints/`.
- `src/underwriting/run.py`: `python -m src.underwriting.run --run-id uw_001 --condition <arm> --phase train|holdout
  [--mode manual|stub]`. Manual mode writes `artifacts/uw/<run>/requests/<arm>/<phase>_case<NN>_<step>.json` and
  polls for `.../responses/<same name>.json`, exactly as the claims runner does. Response validation with Pydantic;
  an invalid response is re-requested (suffix `_r2`), counted, capped at 2 re-requests then scored as postpone-
  equivalent distance 2 and flagged. Arms are independent so five runner processes can run concurrently.
- Request payload: `{run_id, condition, phase, case_index, case (rendered text + fields), manual (text),
  memory (design-specific block or null), senior_answers (ask_senior only), instructions, response_schema}`.
  Response: `{decision, rating_class, modifiers: [{type: flat_extra|exclusion, detail}], drivers: [str],
  rationale: str <= 80 words}`; ask phase: `{questions: [str]}`; reflect phase: `{rulebook_markdown: str}`.
- Operator prompt template (verbatim, in `docs/OPERATOR_PROTOCOL.md` under a new "Underwriter operator" section)
  and `.claude/agents/underwriter-operator.md` (frontmatter `model: fable`, stateless, reads one request file,
  writes one response file, JSON only, no conventions list, no memory of other cases). Keep the template lean: the
  manual is about 900 words and every request carries it.
- Stub mode: two deterministic stub operators for the smoke test only: `naive` (returns `rate_manual_only`) and
  `learner` (applies any house rule whose markup sentence appears in its memory block, by matching the sentence).
  Run all five arms end to end on 6 training + 2 held-out cases as the smoke; archive as
  `archive/experiment-7_stub_smoke/`, labelled stub.
- Logging: `artifacts/uw/<run>/<arm>/cases.jsonl` (one record per case: index, phase, scores, question count,
  memory size, nearest distance, request/response file names, timestamps, model identifier from config; tier is
  NOT written here - join from goldens at analysis time). `scripts/summarize_uw_run.py` prints per-arm tables and
  the trailing-5 series, and the three validation checks from the design (cases 1-3 dead heat across the four
  non-asking arms; clean tier flat for all; novel-rule held-out cases).

## 9. Deviations from the approved design (also to D-27)

1. Operators are Claude Fable 5.1, not Haiku (lead's instruction on 2026-09-11).
2. Written rules: whole rule book shown, not trigger-matched entries.
3. Reflection is one extra call per training case for `written_rules` only; notebook and precedent update
   automatically. Expected live call count: new_joiner 38, notebook 38, written_rules 68, precedent 38,
   ask_senior 76 (two calls per case) = about 258, not 400.

## 10. Tests and docs

Tests (pytest, `tests/underwriting/`): engine tables match the manual text; each rule 1-12 fires >= 3 training
cases in >= 2 shapes; 13-14 only in held-out; tier counts and the window mix; clean cases: manual-only == golden;
markups have no forbidden digits; ladder distance incl. postpone; precedent distance is symmetric and zero on self;
oracle narrowness (a manual-topic question returns manual text, a rule-specific question returns the rule); request
payload leakage audit (no rule ids, no golden fields, no point values from hidden rules, no tier words) on every
request file the stub smoke produced; graph routes per arm; stub end-to-end for all five arms.

Docs: `docs/decision-log.md` D-27 (why the revamp, what carried over, deviations, predictions restated, validation
checks); `docs/OPERATOR_PROTOCOL.md` addendum; `README.md` section "Experiment 7: the underwriting apprentice" with
the exact commands the orchestrator runs; `docs/verification-log.md` entries for every command you ran with its
result. Do not edit the claims article.

Commits (no push): (a) engine + manual + house rules + cases + goldens + freeze + tests; (b) graph + runner + stub
smoke + archive; (c) docs. Run the full test suite before each commit; report the counts exactly as printed.

## 11. Report back

Return: file list, test counts, the stub smoke table, the rule-firing matrix (rule x training case), the tier
schedule for the 30 + 8 cases, the exact runner commands for the orchestrator, and anything you could not do.
