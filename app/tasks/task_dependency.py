# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Dependency Task — v23 (SHAP-based + dataset hybrid)
"""

import pandas as pd
import numpy as np

from versions.v6_1_main import explain_with_shap
from knowledge.rag_dependency import generate_dependency_explanation


# ======================================================
# HELPERS
# ======================================================

def classify_strength(corr):

    abs_corr = abs(corr)

    if abs_corr < 0.05:
        return "negligible"
    elif abs_corr < 0.2:
        return "weak"
    elif abs_corr < 0.4:
        return "moderate"
    else:
        return "strong"


def classify_direction(corr):

    if corr > 0:
        return "positive"
    elif corr < 0:
        return "negative"
    else:
        return "neutral"


# ======================================================
# BASE SCENARIO
# ======================================================

def get_base_scenario():
    return {
        'Density change in land imperviousness': 0,
        'Density of tree cover': 50,
        'Index of total productivity by plant phenology': 200,
        'Change in average temperature compared to a recent past': 0,
        'Relative change in the potential evapotranspiration compared to a recent past': 0,
        'Cumulative change in precipitation compared to a recent past': 0,
        'Number of species potentially living in the cell': 200,
        'Presence of grassland': 1,
        'Land use and cover': 'rural_natural',
        'Change in land use and cover in the past decade': '1',
        'Change in grassland presence  in the past decade': '0',
        'Change in tree cover density in the past decade': '0'
    }


# ======================================================
# MAIN
# ======================================================

def handle_dependency(question, route):

    print("\n========== DEPENDENCY TASK START ==========")

    source = route.get("source")
    target = route.get("target")
    delta = route.get("delta")

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Delta:", delta)

    # ==================================================
    # 🔥 CASE 1: TARGET = RISK → SHAP MODEL
    # ==================================================

    if target == "ecosystem_risk":

        base = get_base_scenario()

        scenario_a = base.copy()
        scenario_b = base.copy()

        if delta is None:
            delta = 1.0

        scenario_b[source] += delta

        print(f"[DEBUG] Applying delta: {source} += {delta}")

        # ✅ SHAP instead of MODEL
        result_a = explain_with_shap(scenario_a)
        result_b = explain_with_shap(scenario_b)

        score_a = result_a["risk_score"]
        score_b = result_b["risk_score"]

        change = score_b - score_a

        # fix -0.0
        if abs(change) < 1e-6:
            change = 0.0

        direction = (
            "positive" if change > 0 else
            "negative" if change < 0 else
            "neutral"
        )

        strength = "moderate" if abs(change) > 0.1 else "weak"

        explanation = generate_dependency_explanation(
            source=source,
            target="ecosystem risk",
            strength=strength,
            direction=direction,
            drivers=[f"model_delta={round(change,3)}"]
        )

        print("========== DEPENDENCY TASK END ==========\n")

        return {
            "summary": "Dependency analysis (model-based)",
            "data": {
                "delta": round(delta, 3),
                "risk_change": round(change, 3),
                "direction": direction,
                "strength": strength
            },
            "drivers": [f"{source} → ecosystem risk"],
            "interpretation": explanation
        }

    # ==================================================
    # 🔥 CASE 2: DATASET-BASED
    # ==================================================

    dataset = pd.read_csv("data/massaciuccoli_data.csv", skiprows=[1])

    if source not in dataset.columns or target not in dataset.columns:
        return {
            "summary": "Dependency not computable",
            "data": {},
            "drivers": [],
            "interpretation": "Variables not found in dataset"
        }

    df = dataset[[source, target]].copy()

    df[source] = pd.to_numeric(df[source], errors="coerce")
    df[target] = pd.to_numeric(df[target], errors="coerce")

    df = df.dropna()

    if len(df) == 0:
        return {
            "summary": "Dependency not computable",
            "data": {},
            "drivers": [],
            "interpretation": "No valid numeric data"
        }

    x = df[source].values
    y = df[target].values

    # --------------------------------------------------
    # GLOBAL RELATION
    # --------------------------------------------------

    corr = np.corrcoef(x, y)[0, 1]

    if np.isnan(corr):
        corr = 0.0

    strength = classify_strength(corr)
    direction = classify_direction(corr)

    print(f"[DEBUG] Correlation: {corr:.3f}")
    print(f"[DEBUG] Strength: {strength}")
    print(f"[DEBUG] Direction: {direction}")

    # --------------------------------------------------
    # LOCAL EFFECT
    # --------------------------------------------------

    std_x = np.std(x)
    std_y = np.std(y)

    if delta is None:
        delta = std_x * 0.1
    else:
        max_delta = std_x * 2
        delta = max(-max_delta, min(delta, max_delta))

    if std_x == 0:
        change = 0.0
    else:
        change = corr * (std_y / std_x) * delta

    if strength == "negligible":
        change *= 0.1

    if abs(change) < 1e-6:
        change = 0.0

    print(f"[DEBUG] Expected change: {change:.6f}")

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

    explanation = generate_dependency_explanation(
        source=source,
        target=target,
        strength=strength,
        direction=direction,
        drivers=[
            f"correlation={round(corr,3)}",
            f"scaled_change={round(change,3)}"
        ]
    )

    print("========== DEPENDENCY TASK END ==========\n")

    return {
        "summary": "Dependency analysis",
        "data": {
            "correlation": round(float(corr), 3),
            "strength": strength,
            "direction": direction,
            "expected_change": round(float(change), 3)
        },
        "drivers": [
            f"{source} → {target} ({strength}, {direction})"
        ],
        "interpretation": explanation
    }