"""T6 — Baseline fraud model: feature_set -> split -> preprocessing -> models (target fraud_label)."""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import average_precision_score, confusion_matrix, f1_score, precision_recall_curve, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split

from src.analyses.common import LABEL_DERIVED_FIELDS, Ctx, ExecutorError, rate
from src.analyses.modeling import build_features, feature_set_metric, fit_and_score, run_preprocessing

TARGET = "fraud_label"
THRESHOLD = 0.5


def feature_set(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    features = list(params["features"])
    X, cat_cols, num_cols = build_features(mc, features)
    ctx.state.update({"X": X, "cat_cols": cat_cols, "num_cols": num_cols})
    out = feature_set_metric(features, cat_cols, num_cols, "label_derived_present", set(LABEL_DERIVED_FIELDS))
    ctx.metrics["feature_set"] = out
    ctx.write_json("feature_list.json", {**out, "target": TARGET, "categorical": cat_cols, "numeric": num_cols})
    ctx.result("feature_set", f"Features ({out['n_categorical']} categorical, {out['n_numeric']} numeric): {', '.join(features)}", source=ctx.artifact_rel("feature_list.json"))
    ctx.result("feature_set", f"Identifier fields present: {out['id_fields_present'] or 'none'}; label-derived fields present: {out['label_derived_present'] or 'none'}", source="metrics.json#feature_set")


def split(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    ctx.require_columns(mc, [TARGET], "medical_claims")
    y = mc[TARGET].astype(int).to_numpy()
    test_size, stratify = float(params["test_size"]), bool(params["stratify"])
    idx = np.arange(len(mc))
    train_idx, test_idx = train_test_split(idx, test_size=test_size, random_state=ctx.seed, shuffle=True, stratify=y if stratify else None)
    ctx.state.update({"y": y, "train_idx": train_idx, "test_idx": test_idx})
    out = {
        "test_size": test_size,
        "stratify": stratify,
        "seed": ctx.seed,
        "n_train": int(len(train_idx)),
        "n_test": int(len(test_idx)),
        "prevalence_train": rate(int(y[train_idx].sum()), len(train_idx)),
        "prevalence_test": rate(int(y[test_idx].sum()), len(test_idx)),
    }
    ctx.metrics["split"] = out
    ctx.result("split", f"test_size={test_size}, stratify={stratify}, seed={ctx.seed}: train / test rows = {out['n_train']} / {out['n_test']}", source="metrics.json#split")
    ctx.result("split", "Prevalence in train", value=out["prevalence_train"], numerator=int(y[train_idx].sum()), denominator=out["n_train"], source="metrics.json#split.prevalence_train")
    ctx.result("split", "Prevalence in test", value=out["prevalence_test"], numerator=int(y[test_idx].sum()), denominator=out["n_test"], source="metrics.json#split.prevalence_test")


def models(ctx: Ctx, params: dict) -> None:
    y, train_idx, test_idx = ctx.state["y"], ctx.state["train_idx"], ctx.state["test_idx"]
    X_train, X_test = ctx.state["X_train"], ctx.state["X_test"]
    y_train, y_test = y[train_idx], y[test_idx]
    class_weight = params["class_weight"]
    names = list(params["models"])
    results: dict[str, dict] = {}
    curves: dict[str, tuple] = {}
    failures: list[str] = []
    for name in names:
        try:
            scores = fit_and_score(name, ctx.seed, class_weight, X_train, y_train, X_test)
        except Exception as exc:  # noqa: BLE001 - one model failing must not hide the others
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        pred = (scores >= THRESHOLD).astype(int)
        cm = confusion_matrix(y_test, pred, labels=[0, 1])
        results[name] = {
            "precision": float(precision_score(y_test, pred, zero_division=0)),
            "recall": float(recall_score(y_test, pred, zero_division=0)),
            "f1": float(f1_score(y_test, pred, zero_division=0)),
            "pr_auc": float(average_precision_score(y_test, scores)),
            "roc_auc": float(roc_auc_score(y_test, scores)),
            "confusion_matrix": [[int(cm[0, 0]), int(cm[0, 1])], [int(cm[1, 0]), int(cm[1, 1])]],
            "threshold": THRESHOLD,
            "n_test": int(len(y_test)),
        }
        curves[name] = precision_recall_curve(y_test, scores)
    ctx.metrics["models"] = results
    ctx.write_json("model_metrics.json", results)
    _confusion_figure(ctx, results)
    _pr_figure(ctx, curves, rate(int(y_test.sum()), len(y_test)))
    for name, r in results.items():
        ctx.result("models", f"{name}: precision / recall / f1 at threshold {THRESHOLD} = {r['precision']:.4f} / {r['recall']:.4f} / {r['f1']:.4f}", source=ctx.artifact_rel("model_metrics.json"))
        ctx.result("models", f"{name}: ROC-AUC", value=r["roc_auc"], source=f"metrics.json#models.{name}.roc_auc")
        ctx.result("models", f"{name}: PR-AUC (average precision)", value=r["pr_auc"], source=f"metrics.json#models.{name}.pr_auc")
        ctx.result("models", f"{name}: confusion matrix [[tn, fp], [fn, tp]] = {r['confusion_matrix']} on n_test={r['n_test']}", source=ctx.artifact_rel("confusion_matrices.png"))
    if failures and not results:
        raise ExecutorError("all models failed: " + " | ".join(failures))
    for f in failures:
        ctx.soft_error("models", f"model failed: {f}")


def _confusion_figure(ctx: Ctx, results: dict) -> None:
    names = list(results) or ["(no model)"]
    fig, axes = plt.subplots(1, len(names), figsize=(4 * len(names), 4), squeeze=False)
    for ax, name in zip(axes[0], names):
        cm = np.array(results.get(name, {}).get("confusion_matrix", [[0, 0], [0, 0]]))
        ax.imshow(cm, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center", color="black")
        ax.set_xticks([0, 1]), ax.set_yticks([0, 1])
        ax.set_xticklabels(["pred 0", "pred 1"]), ax.set_yticklabels(["true 0", "true 1"])
        ax.set_title(f"{name} (threshold {THRESHOLD})")
    ctx.save_fig(fig, "confusion_matrices.png")


def _pr_figure(ctx: Ctx, curves: dict, baseline: float) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, (precision, recall, _) in curves.items():
        ax.plot(recall, precision, label=name)
    ax.axhline(baseline, color="grey", linestyle="--", label=f"prevalence {baseline:.4f}")
    ax.set_xlabel("recall"), ax.set_ylabel("precision"), ax.set_title("Precision-recall curves (test partition)")
    ax.set_ylim(0, 1.02), ax.legend(loc="best")
    ctx.save_fig(fig, "pr_curves.png")


HANDLERS = {"feature_set": feature_set, "split": split, "preprocessing": run_preprocessing, "models": models}
