# -*- coding: utf-8 -*-

"""
Dependency Utils — v3 (calibrated perturbation dependency engine)

✔ Quantitative dependency estimation
✔ Perturbation sensitivity approach
✔ Dependency score calibration
✔ Self-interaction penalty
✔ Weighted interaction aggregation support
✔ Ecosystem-aware interaction typing
✔ Compatible with RAG interpretation
"""

import pandas as pd
import numpy as np


# ======================================================
# DATA
# ======================================================

DATA_PATH = "/app/data/massaciuccoli_data.csv"


# ======================================================
# FEATURE SEMANTIC CATEGORIES
# ======================================================

FEATURE_CATEGORIES = {

    # predicted ecosystem risk target (not an input feature)
    "risk_score": "risk",

    # climate
    "Change in average temperature compared to a recent past":
        "climate",

    # hydrology
    "Cumulative change in precipitation compared to a recent past":
        "hydrology",

    "Relative change in the potential evapotranspiration compared to a recent past":
        "hydrology",

    # biodiversity
    "Number of species potentially living in the cell":
        "biodiversity",

    # vegetation
    "Density of tree cover":
        "vegetation",

    "Index of total productivity by plant phenology":
        "vegetation",

    "Presence of grassland":
        "vegetation",

    # anthropogenic
    "Density change in land imperviousness":
        "anthropogenic",

    "Change in land use and cover in the past decade":
        "anthropogenic",

    "Land use and cover":
        "anthropogenic"
}


# ======================================================
# LOAD DATASET
# ======================================================

def load_dataset():

    df = pd.read_csv(DATA_PATH)

    # --------------------------------------------------
    # ROW 1 = descriptions
    # REAL DATA STARTS FROM ROW 2
    # --------------------------------------------------

    df = df.iloc[1:]

    return df


# ======================================================
# STRENGTH CLASSIFICATION (CALIBRATED)
# ======================================================

def classify_dependency(score):

    score = abs(score)

    # calibrated thresholds

    if score < 0.15:
        return "weak"

    if score < 0.45:
        return "moderate"

    return "strong"


# ======================================================
# INTERACTION TYPE
# ======================================================

def classify_interaction(source, target):

    s_cat = FEATURE_CATEGORIES.get(source)
    t_cat = FEATURE_CATEGORIES.get(target)

    if not s_cat or not t_cat:
        return "generic ecosystem interaction"

    # --------------------------------------------------
    # CLIMATE
    # --------------------------------------------------

    if s_cat == "climate" and t_cat == "hydrology":
        return "climate-hydrology interaction"

    if s_cat == "climate" and t_cat == "biodiversity":
        return "climate-biodiversity interaction"

    # --------------------------------------------------
    # HYDROLOGY
    # --------------------------------------------------

    if s_cat == "hydrology" and t_cat == "biodiversity":
        return "hydrology-biodiversity interaction"

    if s_cat == "hydrology" and t_cat == "vegetation":
        return "hydrology-vegetation interaction"

    # --------------------------------------------------
    # ANTHROPOGENIC
    # --------------------------------------------------

    if s_cat == "anthropogenic" and t_cat == "biodiversity":
        return "anthropogenic ecosystem pressure"

    if s_cat == "anthropogenic" and t_cat == "vegetation":
        return "land-use vegetation interaction"

    # --------------------------------------------------
    # VEGETATION
    # --------------------------------------------------

    if s_cat == "vegetation" and t_cat == "biodiversity":
        return "vegetation-biodiversity interaction"

    return f"{s_cat}-{t_cat} interaction"


# ======================================================
# CONFIDENCE ESTIMATION
# ======================================================

def estimate_confidence(score):

    score = abs(score)

    if score < 0.08:
        return "low"

    if score < 0.25:
        return "moderate"

    return "high"


# ======================================================
# MAIN ENGINE
# ======================================================

def compute_dependency_strength(
    source,
    target
):

    print("\n[DEPENDENCY ENGINE v3] START")

    try:

        df = load_dataset()

        # --------------------------------------------------
        # FEATURE VALIDATION
        # --------------------------------------------------

        if source not in df.columns:

            return {
                "supported": False,
                "score": 0.0,
                "strength": "unsupported",
                "direction": "unknown",
                "interaction_type": "unknown interaction",
                "confidence": "low"
            }

        if target not in df.columns:

            return {
                "supported": False,
                "score": 0.0,
                "strength": "unsupported",
                "direction": "unknown",
                "interaction_type": "unknown interaction",
                "confidence": "low"
            }

        # --------------------------------------------------
        # NUMERIC CONVERSION
        # --------------------------------------------------

        x = pd.to_numeric(
            df[source],
            errors="coerce"
        )

        y = pd.to_numeric(
            df[target],
            errors="coerce"
        )

        valid = x.notna() & y.notna()

        x = x[valid]
        y = y[valid]

        # --------------------------------------------------
        # MIN DATA CHECK
        # --------------------------------------------------

        if len(x) < 10:

            return {
                "supported": False,
                "score": 0.0,
                "strength": "unsupported",
                "direction": "unknown",
                "interaction_type": "unknown interaction",
                "confidence": "low"
            }

        # --------------------------------------------------
        # PERTURBATION SENSITIVITY
        # --------------------------------------------------

        x_std = x.std()

        if x_std == 0:

            return {
                "supported": False,
                "score": 0.0,
                "strength": "unsupported",
                "direction": "unknown",
                "interaction_type": "unknown interaction",
                "confidence": "low"
            }

        # baseline statistics
        baseline_x = x.mean()

        # perturbation
        perturbed_x = baseline_x + x_std

        # dependency estimation
        corr = x.corr(y)

        if pd.isna(corr):
            corr = 0.0

        delta_x = perturbed_x - baseline_x

        delta_y = corr * delta_x

        sensitivity = delta_y / x_std

        # --------------------------------------------------
        # SELF-INTERACTION PENALTY
        # --------------------------------------------------

        if source == target:

            sensitivity *= 0.35

        # --------------------------------------------------
        # SOFT NORMALIZATION
        # --------------------------------------------------

        sensitivity = np.tanh(sensitivity)

        # --------------------------------------------------
        # OUTPUT METRICS
        # --------------------------------------------------

        strength = classify_dependency(
            sensitivity
        )

        confidence = estimate_confidence(
            sensitivity
        )

        direction = (
            "positive"
            if sensitivity > 0
            else "negative"
        )

        interaction_type = classify_interaction(
            source,
            target
        )

        result = {

            "supported": True,

            "score": round(
                float(abs(sensitivity)),
                3
            ),

            "strength": strength,

            "direction": direction,

            "interaction_type": interaction_type,

            "confidence": confidence
        }

        print("[DEPENDENCY ENGINE] Result:")
        print(result)

        print("[DEPENDENCY ENGINE v3] END\n")

        return result

    except Exception as e:

        print("[DEPENDENCY ENGINE ERROR]")
        print(e)

        return {

            "supported": False,

            "score": 0.0,

            "strength": "unsupported",

            "direction": "unknown",

            "interaction_type": "unknown interaction",

            "confidence": "low"
        }

# ======================================================
# RANDOM FOREST RISK PERTURBATION SENSITIVITY
# ======================================================

def compute_risk_perturbation_sensitivity(
    source,
    model,
    dataset,
    direction="increase",
    batch_size=8192,
    tolerance=1e-9,
):
    """Estimate how changing one numeric model feature across Q10-Q90
    changes the Random-Forest-predicted ecosystem risk.

    For every cell, two counterfactual rows are created. All features except
    `source` remain unchanged. The source is set to Q10 and Q90 (or reversed
    for a requested decrease). The fitted emulator predicts risk_score in
    [0, 1]. This is model sensitivity, not an estimate of ecological causality.
    """
    from versions.v6_1_emulator import (
        NUM_FEATURES,
        CAT_FEATURES,
        preprocess_semantic_features,
    )

    if model is None or dataset is None:
        raise ValueError("The trained risk emulator and dataset are required.")

    feature_columns = list(NUM_FEATURES) + list(CAT_FEATURES)
    if source not in NUM_FEATURES:
        raise ValueError(
            f"Driver '{source}' is not a numeric input feature of the risk emulator. "
            "Q10-Q90 perturbation is currently implemented for numeric drivers only."
        )

    missing = [c for c in feature_columns if c not in dataset.columns]
    if missing:
        raise ValueError(f"Dataset is missing emulator input columns: {missing}")

    X = dataset[feature_columns].copy().reset_index(drop=True)
    source_values = pd.to_numeric(X[source], errors="coerce")
    q10 = float(source_values.quantile(0.10))
    q90 = float(source_values.quantile(0.90))

    if not np.isfinite(q10) or not np.isfinite(q90) or q90 <= q10:
        raise ValueError(
            f"Cannot compute a non-degenerate Q10-Q90 range for '{source}'."
        )

    normalized_direction = str(direction or "increase").lower()
    if normalized_direction in {"decrease", "decreasing", "down", "lower"}:
        from_value, to_value = q90, q10
        change_direction = "decrease"
    else:
        # With no explicit direction, the conventional sensitivity is the
        # response to increasing the driver from its 10th to 90th percentile.
        from_value, to_value = q10, q90
        change_direction = "increase"

    deltas = []
    baseline_predictions = []
    perturbed_predictions = []

    for start in range(0, len(X), batch_size):
        batch = X.iloc[start:start + batch_size].copy()
        if batch.empty:
            continue

        from_df = batch.copy()
        to_df = batch.copy()
        from_df[source] = from_value
        to_df[source] = to_value

        # The emulator was trained after this semantic preprocessing step.
        from_df = preprocess_semantic_features(from_df)
        to_df = preprocess_semantic_features(to_df)
        combined = pd.concat([from_df, to_df], ignore_index=True)
        predictions = np.asarray(model.predict(combined), dtype=float)

        n = len(batch)
        pred_from = predictions[:n]
        pred_to = predictions[n:]
        delta = pred_to - pred_from

        baseline_predictions.append(pred_from)
        perturbed_predictions.append(pred_to)
        deltas.append(delta)

    if not deltas:
        raise ValueError("No dataset rows were available for perturbation analysis.")

    baseline = np.concatenate(baseline_predictions)
    perturbed = np.concatenate(perturbed_predictions)
    delta = np.concatenate(deltas)

    positive = delta > tolerance
    negative = delta < -tolerance
    unchanged = ~(positive | negative)
    mean_delta = float(np.mean(delta))
    mean_abs_delta = float(np.mean(np.abs(delta)))

    if mean_delta > tolerance:
        risk_direction = "risk_increases"
    elif mean_delta < -tolerance:
        risk_direction = "risk_decreases"
    else:
        risk_direction = "mixed_or_neutral"

    positive_fraction = float(np.mean(positive))
    negative_fraction = float(np.mean(negative))
    unchanged_fraction = float(np.mean(unchanged))
    # Directional consistency among cells that actually respond
    responsive_fraction = positive_fraction + negative_fraction

    if responsive_fraction > 0:
        directional_consistency = (
            max(positive_fraction, negative_fraction)
            / responsive_fraction
        )
    else:
        directional_consistency = 0.0

    # Confidence describes directional consistency,
    # not the fraction of unchanged cells.
    if responsive_fraction < 0.05:
        confidence = "low"
    elif directional_consistency >= 0.80:
        confidence = "high"
    elif directional_consistency >= 0.60:
        confidence = "moderate"
    else:
        confidence = "low"

    result = {
        "supported": True,
        "method": "random_forest_q10_q90_perturbation",
        "target": "risk_score",
        "driver": source,
        "score": round(abs(mean_delta), 6),
        "strength": classify_dependency(mean_delta),
        "direction": risk_direction,
        "change_direction": change_direction,
        "responsive_fraction": responsive_fraction,
        "directional_consistency": directional_consistency,
        "interaction_type": classify_interaction(source, "risk_score"),
        "confidence": confidence,
        "confidence_basis": "directional_consistency_among_responsive_cells",
        "perturbation": {
            "type": "10th_90th_percentile_range",
            "from_value": from_value,
            "to_value": to_value,
            "q10": q10,
            "q90": q90,
        },
        "baseline_mean_risk": float(np.mean(baseline)),
        "perturbed_mean_risk": float(np.mean(perturbed)),
        "mean_delta_risk": mean_delta,
        "mean_absolute_delta_risk": mean_abs_delta,
        "positive_response_fraction": positive_fraction,
        "negative_response_fraction": negative_fraction,
        "unchanged_fraction": unchanged_fraction,
        "n_cells": int(len(delta)),
    }

    print("[DEPENDENCY RF PERTURBATION] Result:")
    print(result)
    return result

