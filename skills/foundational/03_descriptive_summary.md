---
skill_id: foundational_003
name: descriptive_summary
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [descriptive, rates, denominators, trends, financial, distributions, quantiles, grouped, status_mix, prevalence]
applicable_task_ids: []
---

# Descriptive summary with explicit denominators

## Trigger
Use for any task that describes a portfolio or population — counts, distributions, quantiles, grouped summaries, monthly trends — and whenever a rate, share, or percentage is reported, including denial rate, fraud-label prevalence, status mix, and billed/allowed/paid financial summaries.

## Objective
Produce descriptive statistics a reader can verify: every rate carries its numerator, denominator, and the definition of both; skewed amounts are summarised with quantiles rather than a single mean; and time trends state the date column, the period grain, and the coverage of each period.

## Procedure
1. State the unit of analysis (claim, claim line, member, provider) and the row count that forms the base population; note any exclusions and their counts.
2. For every rate decide and write down the denominator definition before computing it (for example denial rate over adjudicated claims — paid plus denied — rather than over all claims including pending) and report numerator, denominator, and rate together.
3. For categorical fields (status, category, specialty) report counts and shares that sum to the base population, including a share for missing values.
4. For amounts (billed, allowed, paid) report count, mean, standard deviation, minimum, 25th, 50th, 75th and 95th percentiles, and maximum; report the share of zero and negative values separately.
5. For trends choose one date column, state it, aggregate to a monthly grain, and report claim count and amounts per month together with the number of days covered by the first and last months so partial months are visible.
6. For grouped summaries include the group size next to every group statistic and order groups by size or by a stated key, never by an unstated default.
7. Cross-check totals: category shares sum to the base, monthly counts sum to the total, and any rate recomputed from its numerator and denominator matches the reported value.
8. Save the summary as machine-readable metrics plus tables and charts, each labelled with the denominator definition used.

## Required checks
- Every rate is accompanied by numerator, denominator, and their definitions.
- Category and status shares sum to the base population (including a missing bucket).
- Trend tables and charts name the date column and the period grain and flag partial periods.
- Quantiles, not only means, are reported for skewed amount fields.
- Metrics are written to a machine-readable file with the same values shown in the report.

## Expected artifacts
- A metrics JSON with each rate as value, numerator, denominator, numerator definition, denominator definition.
- A status or category distribution table and chart.
- A monthly volume and amount trend table and chart.
- A financial summary table with quantiles.

## Failure modes
- Reporting a denial rate with no denominator, or computing it over all claims when pending claims should be excluded.
- Presenting a mean paid amount for a heavily skewed distribution without the median and upper quantiles.
- Monthly trends that mix two date columns or include a partial last month without flagging it.
- Grouped tables that omit group sizes, making small noisy groups look like large ones.

## Example
Of 12,800 synthetic claims, 11,500 are adjudicated (paid or denied). Denials number 1,150, so the denial rate is 1,150 / 11,500 = 10.0% of adjudicated claims (9.0% of all 12,800 claims, reported separately and labelled as such). Paid amount has median 420 and 95th percentile 6,800 while the mean is 1,150, so the median and quantiles lead the summary.

## Provenance
Foundational skill authored by the skill-system engineer from the project brief (counts, distributions, quantiles, grouped summaries, trends, rates with explicit denominators). Not derived from any task run; no feedback ids.
