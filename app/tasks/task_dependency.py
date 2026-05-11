# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Dependency Task — v24 (parser integrated FIX)
"""

import pandas as pd
import numpy as np

# 🔥 FIX QUI
from utils.dependency_parser import parse_dependency

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
# MAIN
# ======================================================

def handle_dependency(question, route):

    print("\n========== DEPENDENCY TASK START ==========")

    parsed = parse_dependency(question)

    source = parsed.get("source")
    target = parsed.get("target")
    delta = parsed.get("delta")

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Delta:", delta)

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if not source or not target:
        return {
            "summary": "Dependency not computable",
            "data": {},
            "drivers": [],
            "interpretation": (
                "The variables mentioned in the question are not available "
                "in the ecosystem dataset."
            )
        }

    # --------------------------------------------------
    # LOAD DATASET
    # --------------------------------------------------

    dataset = pd.read_csv("data/massaciuccoli_data.csv", skiprows=[1])

    if source not in dataset.columns or target not in dataset.columns:
        return {
            "summary": "Dependency not computable",
            "data": {},
            "drivers": [],
            "interpretation": (
                f"The relationship between '{source}' and '{target}' "
                "cannot be evaluated because one or both variables "
                "are not present in the dataset."
            )
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
            "interpretation": "No valid numeric data available."
        }

    # --------------------------------------------------
    # CORRELATION
    # --------------------------------------------------

    x = df[source].values
    y = df[target].values

    corr = np.corrcoef(x, y)[0, 1]

    if np.isnan(corr):
        corr = 0.0

    strength = classify_strength(corr)
    direction = classify_direction(corr)

    print(f"[DEBUG] Correlation: {corr:.3f}")
    print(f"[DEBUG] Strength: {strength}")
    print(f"[DEBUG] Direction: {direction}")

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

    explanation = generate_dependency_explanation(
        source=source,
        target=target,
        strength=strength,
        direction=direction,
        drivers=[f"correlation={round(corr,3)}"]
    )

    print("========== DEPENDENCY TASK END ==========\n")

    return {
        "summary": "Dependency analysis",
        "data": {
            "correlation": round(float(corr), 3),
            "strength": strength,
            "direction": direction
        },
        "drivers": [
            f"{source} → {target} ({strength}, {direction})"
        ],
        "interpretation": explanation
    }