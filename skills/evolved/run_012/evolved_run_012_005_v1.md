---
skill_id: evolved_run_012_005
name: include_no_operational_use_caveat_in_healthcare_predictive_m
version: 1
status: active
kind: evolved
created_after_task: T7
created_after_task_index: 4
source_feedback_ids: [T7-caveat_no_operational_use]
created_at: "2026-09-09T03:54:53+00:00"
reuse_count: 0
tags: [caveat, healthcare, predictive_models, governance, communication, claims]
applicable_task_ids: [T8]
run_id: run_012
condition: skill_learning
---

# Include no operational use caveat in healthcare predictive m

## Trigger
When writing a report for any predictive ranking or classification model built on claims or healthcare data, evaluate whether the model output is being proposed for operational use and include the 'no_operational_use' caveat if scores are analytical-only and require clinical validation and governance review before deployment.

## Objective
Prevent operational deployment of analytical models without proper clinical validation, governance review, and risk assessment by explicitly documenting that model scores are analytical tools and must not be used operationally without additional vetting.

## Procedure
1. When using the write_report component for any predictive or classification task on healthcare or claims data, assess whether the model output is analytical-only or intended for operational decision-making.
2. If the model is analytical-only (scoring for review, not automatic decisions), include the 'no_operational_use' caveat in the report component's caveats parameter.
3. Phrase the caveat to clearly state that the model output is analytical in nature and that scores require clinical validation, governance review, and organizational risk assessment before any operational use, such as automated coverage decisions or claim payment instructions.
4. Place this caveat early in the Caveats section so readers understand this critical limitation before interpreting or acting on results.

## Required checks
- Verify that 'no_operational_use' is listed among the report component's caveats or that equivalent language about analytical-only status and requirement for validation before operational use is present in the report text.
- Confirm that the caveat language explicitly distinguishes between analytical use (for review or investigation) and operational use (for automated decisions or process changes).
- Check that the caveat mentions validation and governance review as prerequisites for operational deployment.

## Expected artifacts
- report.md

## Failure modes
- Omitting the caveat, allowing stakeholders to misinterpret analytical scores as production-ready without understanding validation and governance requirements.
- Phrasing the caveat weakly or generically, failing to convey that operational use requires clinical validation and organizational review.
- Including the caveat only in the methodology section rather than the Caveats section, reducing visibility to decision-makers.

## Example
In a high-cost claims ranking model report, the no_operational_use caveat states: 'Model scores are analytical tools for identifying claims requiring clinical review. Scores must not be used operationally to make coverage or payment decisions without clinical validation, claims governance review, and organizational risk assessment.'

## Provenance
Evolved skill learned in run `run_012` (condition `skill_learning`) after task T7 (task index 4) from feedback ids T7-caveat_no_operational_use. Evaluation score total at proposal time: 3.6. Proposed by operator `claude-code-subagent` via provider mode `manual` (model `claude-haiku-4-5-20251001`). Declared applicable task ids: T8.
