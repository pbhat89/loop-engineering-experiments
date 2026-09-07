---
skill_id: evolved_run_002_006
name: conventions_split_test_size_stratify_preprocessing_fit_on_mo
version: 1
status: active
kind: evolved
created_after_task: T6
created_after_task_index: 5
source_feedback_ids: [T6-split_stratified, T6-fit_on_train_only, T6-tree_model_present]
created_at: "2026-09-07T00:24:38+00:00"
reuse_count: 0
tags: [modeling, fraud, classification, leakage, splits, seeds, metrics, class_imbalance]
applicable_task_ids: [T7, T8]
run_id: run_002
condition: skill_learning
---

# Conventions split test size stratify preprocessing fit on mo

## Trigger
The task catalogue offers fit_on, models, preprocessing, split, stratify, test_size.

## Objective
House conventions learned from evaluator feedback: component:split; param:test_size=0.25; param:stratify=true; component:preprocessing; param:fit_on=train_only; component:models; list:models+=random_forest

## Procedure
1. Include the `split` component.
2. `test_size` = `0.25` on any component that has it.
3. `stratify` = `true` on any component that has it.
4. Include the `preprocessing` component.
5. `fit_on` = `train_only` on any component that has it.
6. Include the `models` component.
7. Add `random_forest` to any `models` list.

## Required checks
- component:split
- param:test_size=0.25
- param:stratify=true
- component:preprocessing
- param:fit_on=train_only
- component:models
- list:models+=random_forest

## Expected artifacts
- model_metrics.json
- confusion_matrices.png
- pr_curves.png

## Failure modes
- A convention applied by parameter name can be wrong for a task with a different target or population; that task's feedback overrides it.
- List additions may name fields or pairs a later task does not load.

## Example
Include the `split` component.

## Provenance
Evolved skill learned in run `run_002` (condition `skill_learning`) after task T6 (task index 5) from feedback ids T6-split_stratified, T6-fit_on_train_only, T6-tree_model_present. Evaluation score total at proposal time: 4.0. Proposed by operator `deterministic-rule-learner` via provider mode `rule_learner` (model `rule-learner-v1`). Declared applicable task ids: T7, T8.
