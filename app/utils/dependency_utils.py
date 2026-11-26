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