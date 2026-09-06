---
skill_id: foundational_006
name: evaluation_and_charting
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [metrics, charts, caveats, communication, evaluation, traceability, executive_brief, limitations, figures, rubric]
applicable_task_ids: []
---

# Evidence-backed evaluation and charting

## Trigger
Use when scoring an analysis against a frozen rubric, when producing charts that describe results, and when writing any summary or executive brief in which numeric statements must trace to saved metrics or artifacts.

## Objective
Keep evaluation and communication honest and traceable: scores come from a frozen rubric applied to saved artifacts, every chart is generated from logged data rather than from memory, every number in prose cites its source metric, and limitations and synthetic-data caveats are stated explicitly.

## Procedure
1. Identify the rubric version and the golden or expected values that apply; treat them as frozen — they stay exactly as they were before the output was seen.
2. For each rubric dimension (correctness, completeness, reproducibility, statistical discipline, communication) list the deterministic checks to apply and the artifact each check reads.
3. Score each dimension on the fixed 0–4 scale from the check results, record every check with its observed and expected values, and compute the overall score as the mean of the five dimension scores.
4. Build every chart from a saved data source (metrics file, log, or CSV); label axes with units, name the denominator for any rate, and state the sample size in the caption.
5. Prefer simple chart types: bars for category comparisons with group sizes annotated, lines for monthly trends with partial periods marked, and confusion matrices or precision–recall curves for classifiers with prevalence in the title.
6. In prose, attach every numeric statement to its source (metric key or artifact filename) so a reader can find it; a number that has no saved source is left out.
7. Write a limitations section covering data limitations (synthetic data, single snapshot), statistical limitations (class imbalance, small groups, no uncertainty from repeated runs), and what would be needed to strengthen the finding.
8. Describe comparisons between conditions or models as illustrative unless repeated runs and a suitable analysis support a stronger statement.

## Required checks
- Rubric version and golden identifiers are recorded with every evaluation.
- Each chart names its data source, axis units, denominator, and sample size.
- Every numeric statement in the brief maps to a metric key or artifact.
- A limitations and synthetic-data caveat section is present.
- No claim of statistical significance is made without repeated runs.

## Expected artifacts
- An evaluation record (rubric version, checks with observed and expected values, dimension scores, overall score).
- Charts saved as files, each generated from a named data source.
- A brief or report with a limitations section and per-number source references.

## Failure modes
- Rubric or golden values that drift after the output is seen.
- Charts drawn from remembered numbers that no longer match the metrics file.
- An executive brief that states a rate "improved" with no artifact behind it.
- Presenting a one-run difference between two conditions as significant.

## Example
An executive brief states "denial rate 10.0% of 11,500 adjudicated claims (metrics.json: denial_rate)" and "PR-AUC 0.41 at 3.1% prevalence (model_metrics.json: pr_auc)". Each figure caption names its CSV source and sample size, and the limitations section notes that the data are synthetic, the model was evaluated on a single split, and the condition comparison is illustrative.

## Provenance
Foundational skill authored by the skill-system engineer from the project brief (frozen-rubric evaluation and charts generated exclusively from logs and artifacts). Not derived from any task run; no feedback ids.
