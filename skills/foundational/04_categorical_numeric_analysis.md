---
skill_id: foundational_004
name: categorical_numeric_analysis
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [categorical, numeric, small_groups, association, comparison, group_sizes, denials, providers, network_status, uncertainty]
applicable_task_ids: []
---

# Categorical and numeric comparisons with small-group discipline

## Trigger
Use when comparing an outcome (denial rate, paid amount, fraud-label rate, claim count) across categories such as provider specialty, network status, claim type, place of service, denial code, or authorization requirement, and when describing differences between flagged and unflagged claims.

## Objective
Make group comparisons that are statistically honest: the right summary for the variable type, group sizes shown next to every estimate, unstable small groups flagged rather than ranked, and wording that describes association without implying causation.

## Procedure
1. Classify each variable as categorical or numeric and pick the comparison accordingly: counts and rates with denominators for categorical outcomes; median, interquartile range, and mean for numeric outcomes (report both when skewed).
2. Build one table per comparison with columns group, group size, numerator, denominator, rate or median, and a stability flag.
3. Set and state a minimum group size (a common default is 30 claims); mark groups below it as unstable and exclude them from rankings while still listing them.
4. Where a rate is reported for a group, add an uncertainty indication (for example a Wilson interval or the standard error) so that differences between small groups are not over-read.
5. Rank groups only among stable groups and say what the ranking is by (rate, count, or amount) and over which denominator.
6. Report missing category values as their own bucket with size and rate instead of dropping them silently.
7. Write findings as associations ("denial rate is higher among out-of-network claims in this sample") and list the plausible confounders (specialty mix, claim type) a causal reading would need to rule out.
8. When the outcome is a synthetic fraud label, say that it is synthetic and that no real fraud conclusion follows; never use protected attributes (age band, sex, region) as targeting variables.

## Required checks
- Every group row shows the group size and the denominator used.
- The minimum group size threshold is stated once and applied consistently; small groups carry a visible flag.
- Rankings include only stable groups and name the ranking metric.
- Comparison text uses association language and lists confounders.
- Missing category values appear as an explicit bucket.

## Expected artifacts
- One comparison table per dimension (CSV) with size, numerator, denominator, rate, and flag columns.
- A bar chart per key comparison with group sizes annotated.
- A findings section that separates stable and unstable groups.

## Failure modes
- Ranking a specialty with five claims and a very high denial rate above one with nine hundred claims and a moderate rate.
- Comparing means of paid amounts across groups when a few very large claims dominate.
- Writing that network status "drives" denials from a cross-tabulation.
- Dropping claims with missing specialty and reporting shares over the reduced base without saying so.

## Example
Denial rate by network status on synthetic claims: in-network 8,900 claims, 801 denied (9.0%); out-of-network 2,600 claims, 349 denied (13.4%); unknown 300 claims, 30 denied (10.0%). All groups exceed the 30-claim threshold, so all are stable; the report describes the out-of-network rate as higher in this sample and notes that specialty mix differs between the groups.

## Provenance
Foundational skill authored by the skill-system engineer from the project brief (appropriate categorical/numeric comparisons, small-group flags, association-versus-causation language). Not derived from any task run; no feedback ids.
