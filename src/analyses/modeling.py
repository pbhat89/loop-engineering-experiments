"""Shared modelling helpers for T6/T7: feature frames, preprocessing with ``fit_on`` semantics, estimators.

Estimators are exactly the skeleton's: ``LogisticRegression(max_iter=1000, random_state=seed)``,
``RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=1)``,
``HistGradientBoostingClassifier(random_state=seed)``; categoricals -> ``OneHotEncoder(handle_unknown="ignore")``;
numerics -> ``StandardScaler`` only when ``scaling == "standard"``.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.analyses.common import ID_FIELDS, Ctx, ExecutorError, InvalidParamError

CATEGORICAL_FEATURES = {
    "claim_type", "cpt_category", "place_of_service", "provider_specialty", "network_status", "primary_icd10_cm",
    "claim_id", "member_id", "rendering_npi", "fraud_pattern_type",
}
NUMERIC_FEATURES = {
    "billed_amount", "allowed_amount", "paid_amount", "member_oop", "cob_amount", "service_units", "length_of_stay",
    "er_flag", "elective_flag", "preventive_flag", "auth_required_flag", "drg_present", "high_cost_flag",
}
DENSE_CELL_LIMIT = 40_000_000  # guard for estimators that need a dense matrix


def build_features(mc: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Feature frame in plan order; ``drg_present = drg_code.notna()``; categoricals as str with ``missing`` fill."""
    if not features:
        raise InvalidParamError("features must contain at least one feature")
    X = pd.DataFrame(index=mc.index)
    cat_cols, num_cols = [], []
    for f in features:
        if f == "drg_present":
            if "drg_code" not in mc.columns:
                raise ExecutorError("medical_claims: missing column drg_code (needed for drg_present)")
            X[f] = mc["drg_code"].notna().astype(int)
            num_cols.append(f)
        elif f in CATEGORICAL_FEATURES:
            if f not in mc.columns:
                raise ExecutorError(f"medical_claims: missing column {f}")
            col = mc[f].astype(object)
            X[f] = col.where(mc[f].notna(), "missing").astype(str)
            cat_cols.append(f)
        else:
            if f not in mc.columns:
                raise ExecutorError(f"medical_claims: missing column {f}")
            X[f] = pd.to_numeric(mc[f], errors="coerce").astype(float)
            num_cols.append(f)
    return X, cat_cols, num_cols


def feature_set_metric(features: list[str], cat_cols: list[str], num_cols: list[str], derived_key: str, derived_set: set[str]) -> dict:
    return {
        "features": list(features),
        "n_categorical": len(cat_cols),
        "n_numeric": len(num_cols),
        "id_fields_present": [f for f in features if f in ID_FIELDS],
        derived_key: [f for f in features if f in derived_set],
    }


def make_preprocessor(cat_cols: list[str], num_cols: list[str], scaling: str) -> ColumnTransformer:
    transformers = []
    if cat_cols:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols))
    if num_cols:
        steps = [("impute", SimpleImputer(strategy="median"))]
        if scaling == "standard":
            steps.append(("scale", StandardScaler()))
        transformers.append(("num", Pipeline(steps), num_cols))
    return ColumnTransformer(transformers, remainder="drop")


def run_preprocessing(ctx: Ctx, params: dict) -> None:
    """Shared ``preprocessing`` component: fit on the training partition only (``train_only``) or on all
    rows before splitting (``all_data``); transform train and test partitions."""
    X, cat_cols, num_cols = ctx.state["X"], ctx.state["cat_cols"], ctx.state["num_cols"]
    train_idx, test_idx = ctx.state["train_idx"], ctx.state["test_idx"]
    fit_on, scaling = params["fit_on"], params["scaling"]
    pre = make_preprocessor(cat_cols, num_cols, scaling)
    if fit_on == "train_only":
        pre.fit(X.iloc[train_idx])
    elif fit_on == "all_data":
        pre.fit(X)
    else:
        raise InvalidParamError(f"unknown fit_on {fit_on!r}")
    X_train = pre.transform(X.iloc[train_idx])
    X_test = pre.transform(X.iloc[test_idx])
    n_out = int(X_train.shape[1])
    ctx.state.update({"X_train": X_train, "X_test": X_test, "preprocessor": pre})
    ctx.metrics["preprocessing"] = {"fit_on": fit_on, "scaling": scaling, "n_features_out": n_out}
    ctx.result("preprocessing", f"fit_on={fit_on}, scaling={scaling}; features after encoding", value=n_out, source="metrics.json#preprocessing")


def make_model(name: str, seed: int, class_weight: str | None = None):
    cw = None if class_weight in (None, "none") else class_weight
    if name == "logistic_regression":
        return LogisticRegression(max_iter=1000, random_state=seed, class_weight=cw)
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=200, random_state=seed, n_jobs=1, class_weight=cw)
    if name == "gradient_boosting":
        return HistGradientBoostingClassifier(random_state=seed, class_weight=cw)
    raise InvalidParamError(f"unknown model {name!r}")


def model_input(name: str, X):
    """HistGradientBoosting needs a dense matrix; refuse absurd one-hot widths instead of exhausting memory."""
    if name == "gradient_boosting" and sparse.issparse(X):
        if X.shape[0] * X.shape[1] > DENSE_CELL_LIMIT:
            raise ExecutorError(f"gradient_boosting needs a dense matrix but the encoded design is {X.shape[0]}x{X.shape[1]}; drop high-cardinality id features")
        return X.toarray()
    return X


def fit_and_score(name: str, seed: int, class_weight: str | None, X_train, y_train, X_test) -> np.ndarray:
    model = make_model(name, seed, class_weight)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(model_input(name, X_train), y_train)
        scores = model.predict_proba(model_input(name, X_test))[:, 1]
    return np.asarray(scores, dtype=float)
