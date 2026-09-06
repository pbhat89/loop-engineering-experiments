---
skill_id: foundational_005
name: reproducible_python_analysis
version: 1
status: active
kind: foundational
created_after_task: null
created_after_task_index: null
source_feedback_ids: []
created_at: "2026-09-06T00:00:00+00:00"
reuse_count: 0
tags: [reproducibility, seeds, splits, leakage, modeling, metrics, artifacts, machine_readable, fraud, high_cost]
applicable_task_ids: []
---

# Reproducible analysis pipeline

## Trigger
Use whenever an analysis produces numbers that will be cited, compared across runs or conditions, or used to train and evaluate a model — in particular any task with random sampling, train/test splits, model fitting, or threshold selection such as a high-cost percentile.

## Objective
Ensure that the same inputs and the same analysis code produce the same outputs: fixed seeds, explicit named inputs and outputs, preprocessing and thresholds fitted on training data only, and every reported number saved in a machine-readable metrics file alongside the saved figures.

## Procedure
1. Declare inputs explicitly: table names, the data snapshot hash from the manifest, the columns used, and the exclusion rules (identifier columns, label-derived columns such as `fraud_pattern_type`, post-outcome fields).
2. Fix one integer seed for the task and pass it to every random operation (sampling, splitting, model initialisation); record the seed in the metrics file.
3. Create the train/test split once, stratified on the target when the target is a class label, and save the split sizes and class counts per split with denominators.
4. Fit every preprocessing step (imputation, scaling, encoding, percentile thresholds such as a high-cost cut-off) on the training split only, then apply it unchanged to the test split.
5. Keep the analysis as a single script or module with named output paths under the task's output directory; do not depend on interactive state or hand-edited intermediates.
6. Write metrics to a machine-readable JSON (metric name, value, numerator and denominator where applicable, split, seed) and take the values shown in the report from that file, not from memory.
7. Save every figure to a file with a descriptive name and record the list of artifacts produced; a figure that is not saved does not exist for evaluation purposes.
8. Repeat the pipeline from scratch with the same inputs and seed and confirm the metrics file is identical or within a stated floating-point tolerance; record the check result.

## Required checks
- The seed and the data snapshot hash appear in the metrics file.
- No identifier or label-derived column is in the model feature list.
- Preprocessing and thresholds are fitted on the training split only.
- Every number in the report has a matching key in the metrics file.
- A repeat of the pipeline reproduces the metrics within tolerance.

## Expected artifacts
- A metrics JSON with seed, snapshot hash, split sizes, and all reported metrics.
- Saved figures with descriptive filenames.
- The analysis script or module and a list of produced artifacts.

## Failure modes
- Computing a high-cost percentile threshold on the full dataset and then evaluating on a test set that helped define it (leakage).
- Leaving `fraud_pattern_type` in the features and reporting a near-perfect model.
- Different seeds across split, sampling, and model, so no two repeats agree.
- Figures shown once and never saved, or metrics typed into the report by hand.

## Example
A baseline fraud model uses seed 42, a stratified 80/20 split (10,240 train / 2,560 test; positives 3.1% in both), a scaler fitted on the training split only, and excludes `claim_id`, `member_id`, `provider_id`, and `fraud_pattern_type`. The metrics JSON records seed, split sizes, prevalence, precision, recall, F1, PR-AUC, and ROC-AUC; the report quotes each value from that file.

## Provenance
Foundational skill authored by the skill-system engineer from the project brief (fixed seeds, explicit inputs/outputs, saved figures, reproducible scripts, machine-readable metrics). Not derived from any task run; no feedback ids.
