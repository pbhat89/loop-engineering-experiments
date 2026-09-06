"""T7 — High-cost claim identification: plain random split -> percentile threshold -> features -> models.

The split is a plain random split of rows (no stratification: the target does not exist yet); the
threshold is ``numpy.percentile`` of the amount column on the training partition (``train_only``) or on
all rows (``all_data``); positive = amount > threshold.
"""
from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import train_test_split

from src.analyses.common import Ctx, ExecutorError, rate
from src.analyses.modeling import build_features, feature_set_metric, fit_and_score, run_preprocessing

TARGET_DERIVED = {"billed_amount", "allowed_amount", "paid_amount", "member_oop", "cob_amount", "high_cost_flag"}
TOP_FRACTION = 0.05


def split(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    test_size = float(params["test_size"])
    idx = np.arange(len(mc))
    train_idx, test_idx = train_test_split(idx, test_size=test_size, random_state=ctx.seed, shuffle=True)
    ctx.state.update({"train_idx": train_idx, "test_idx": test_idx})
    out = {"test_size": test_size, "seed": ctx.seed, "n_train": int(len(train_idx)), "n_test": int(len(test_idx))}
    ctx.metrics["split"] = out
    ctx.result("split", f"Plain random split test_size={test_size}, seed={ctx.seed}: train / test rows = {out['n_train']} / {out['n_test']}", source="metrics.json#split")


def target_definition(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    col, pct, source = params["amount_column"], int(params["percentile"]), params["threshold_source"]
    ctx.require_columns(mc, [col], "medical_claims")
    train_idx, test_idx = ctx.state["train_idx"], ctx.state["test_idx"]
    amounts = pd.to_numeric(mc[col], errors="coerce").to_numpy(dtype=float)
    basis = amounts[train_idx] if source == "train_only" else amounts
    basis = basis[~np.isnan(basis)]
    threshold = float(np.percentile(basis, pct))
    y = (amounts > threshold).astype(int)
    ctx.state["y"] = y
    n_pos_train, n_pos_test = int(y[train_idx].sum()), int(y[test_idx].sum())
    out = {
        "amount_column": col,
        "percentile": pct,
        "threshold_source": source,
        "threshold_value": threshold,
        "positive_rate_train": rate(n_pos_train, len(train_idx)),
        "positive_rate_test": rate(n_pos_test, len(test_idx)),
        "n_positive_train": n_pos_train,
        "n_positive_test": n_pos_test,
    }
    ctx.metrics["target_definition"] = out
    ctx.write_json("threshold.json", {**out, "definition": f"positive = {col} > threshold_value; threshold_value = numpy.percentile({source} {col}, {pct})", "n_rows_used": int(len(basis)), "seed": ctx.seed})
    ctx.result("target_definition", f"Threshold = p{pct} of {col} on {source} rows", value=threshold, source=ctx.artifact_rel("threshold.json"))
    ctx.result("target_definition", "Positive rate in train", value=out["positive_rate_train"], numerator=n_pos_train, denominator=len(train_idx), source="metrics.json#target_definition.positive_rate_train")
    ctx.result("target_definition", "Positive rate in test", value=out["positive_rate_test"], numerator=n_pos_test, denominator=len(test_idx), source="metrics.json#target_definition.positive_rate_test")


def feature_set(ctx: Ctx, params: dict) -> None:
    mc = ctx.table("medical_claims")
    features = list(params["features"])
    X, cat_cols, num_cols = build_features(mc, features)
    ctx.state.update({"X": X, "cat_cols": cat_cols, "num_cols": num_cols})
    out = feature_set_metric(features, cat_cols, num_cols, "target_derived_present", TARGET_DERIVED)
    ctx.metrics["feature_set"] = out
    ctx.write_json("feature_list.json", {**out, "target": "high_cost (amount > threshold)", "categorical": cat_cols, "numeric": num_cols})
    ctx.result("feature_set", f"Features ({out['n_categorical']} categorical, {out['n_numeric']} numeric): {', '.join(features)}", source=ctx.artifact_rel("feature_list.json"))
    ctx.result("feature_set", f"Identifier fields present: {out['id_fields_present'] or 'none'}; target-derived amount fields present: {out['target_derived_present'] or 'none'}", source="metrics.json#feature_set")


def _top_k_metrics(y_test: np.ndarray, scores: np.ndarray, k: int) -> tuple[float, float]:
    order = np.lexsort((np.arange(len(scores)), -scores))  # score desc, index asc for ties
    hits = int(y_test[order[:k]].sum())
    return rate(hits, k), rate(hits, int(y_test.sum()))


def models(ctx: Ctx, params: dict) -> None:
    y, train_idx, test_idx = ctx.state["y"], ctx.state["train_idx"], ctx.state["test_idx"]
    X_train, X_test = ctx.state["X_train"], ctx.state["X_test"]
    y_train, y_test = y[train_idx], y[test_idx]
    n_test = int(len(y_test))
    k = max(1, int(math.ceil(TOP_FRACTION * n_test)))
    results: dict[str, dict] = {}
    curves: dict[str, np.ndarray] = {}
    failures: list[str] = []
    for name in list(params["models"]):
        try:
            scores = fit_and_score(name, ctx.seed, None, X_train, y_train, X_test)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        p_at_k, r_at_k = _top_k_metrics(y_test, scores, k)
        results[name] = {
            "pr_auc": float(average_precision_score(y_test, scores)),
            "roc_auc": float(roc_auc_score(y_test, scores)),
            "precision_at_top_5pct": p_at_k,
            "recall_at_top_5pct": r_at_k,
            "n_test": n_test,
        }
        order = np.lexsort((np.arange(n_test), -scores))
        curves[name] = np.cumsum(y_test[order]) / np.arange(1, n_test + 1)
    ctx.metrics["models"] = results
    ctx.write_json("model_metrics.json", {**results, "top_k": k, "top_fraction": TOP_FRACTION})
    fig, ax = plt.subplots(figsize=(7, 5))
    for name, prec in curves.items():
        ax.plot(np.arange(1, n_test + 1) / n_test, prec, label=name)
    ax.axvline(TOP_FRACTION, color="grey", linestyle="--", label=f"top {int(TOP_FRACTION * 100)}% (k={k})")
    ax.axhline(rate(int(y_test.sum()), n_test), color="black", linestyle=":", label="test positive rate")
    ax.set_xlabel("fraction of test rows ranked by score"), ax.set_ylabel("precision@k"), ax.set_title("Precision at k (test partition)")
    ax.set_xlim(0, 1), ax.set_ylim(0, 1.02), ax.legend(loc="best")
    ctx.save_fig(fig, "precision_at_k.png")
    for name, r in results.items():
        ctx.result("models", f"{name}: ROC-AUC", value=r["roc_auc"], source=f"metrics.json#models.{name}.roc_auc")
        ctx.result("models", f"{name}: PR-AUC (average precision)", value=r["pr_auc"], source=f"metrics.json#models.{name}.pr_auc")
        ctx.result("models", f"{name}: precision at top 5% (k={k}) of test rows", value=r["precision_at_top_5pct"], source=ctx.artifact_rel("model_metrics.json"))
        ctx.result("models", f"{name}: recall at top 5% (k={k}) of test rows", value=r["recall_at_top_5pct"], source=ctx.artifact_rel("model_metrics.json"))
    if failures and not results:
        raise ExecutorError("all models failed: " + " | ".join(failures))
    for f in failures:
        ctx.soft_error("models", f"model failed: {f}")


HANDLERS = {"split": split, "target_definition": target_definition, "feature_set": feature_set, "preprocessing": run_preprocessing, "models": models}
