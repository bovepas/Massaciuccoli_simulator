# -*- coding: utf-8 -*-

"""
Drivers Task — v6 (clean + demo-ready + semantic fix)

✔ Removes noisy variables
✔ Filters weak correlations
✔ Improves output readability
✔ Adds scientific disclaimer
✔ 🔥 Aligns wording with "loss / increase"
"""

import pandas as pd
import os

from utils.feature_mapping import normalize_feature_name
from utils.drivers_parser import parse_drivers_target, parse_drivers_goal
from knowledge.rag_drivers import generate_drivers_explanation


DATA_PATH = "/app/data/massaciuccoli_data.csv"


EXCLUDED_FEATURES = [
    "Latitude",
    "Longitude"
]

MIN_CORRELATION = 0.1  # 🔥 threshold


def load_data():

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # skip description row
    df = df.iloc[1:]

    return df


def classify_strength(corr):
    abs_corr = abs(corr)

    if abs_corr < 0.1:
        return "weak"
    elif abs_corr < 0.3:
        return "moderate"
    else:
        return "strong"


# ======================================================
# 🔥 UPDATED DRIVER FORMAT (SEMANTIC FIX)
# ======================================================

def format_driver(d, target, goal):
    feature = d["feature"]
    strength = d["strength"]
    direction = d["direction"]

    # 👉 caso biodiversità → linguaggio naturale "loss"
    if "species" in target.lower() and goal == "decrease":
        return f"{feature} (associated with biodiversity decline, {strength})"

    if "species" in target.lower() and goal == "increase":
        return f"{feature} (associated with biodiversity increase, {strength})"

    # 👉 fallback generico
    return f"{feature} ({direction}, {strength} influence)"


def handle_drivers(question: str):

    print("\n========== DRIVERS TASK START ==========")

    df = load_data()

    target_raw = parse_drivers_target(question)
    target = normalize_feature_name(target_raw) if target_raw else None

    print("[DEBUG] Target:", target)

    if target is None or target not in df.columns:
        return {
            "summary": "Drivers not computable",
            "data": {},
            "drivers": [],
            "interpretation": "Target variable not found in dataset."
        }

    goal = parse_drivers_goal(question)
    print("[DEBUG] Goal:", goal)

    results = []

    for col in df.columns:

        if col == target or col in EXCLUDED_FEATURES:
            continue

        try:
            x = pd.to_numeric(df[col], errors="coerce")
            y = pd.to_numeric(df[target], errors="coerce")

            corr = x.corr(y)

            if pd.notna(corr) and abs(corr) >= MIN_CORRELATION:

                results.append({
                    "feature": col,
                    "correlation": float(corr),
                    "abs_corr": abs(float(corr)),
                    "direction": "positive" if corr > 0 else "negative",
                    "strength": classify_strength(corr)
                })

        except Exception:
            continue

    # 🔥 GOAL FILTER
    if goal == "decrease":
        results = [r for r in results if r["correlation"] < 0]

    elif goal == "increase":
        results = [r for r in results if r["correlation"] > 0]

    # 🔥 SORT
    results = sorted(results, key=lambda x: x["abs_corr"], reverse=True)
    top = results[:5]

    print("[DEBUG] Top drivers:", [d["feature"] for d in top])

    # 🔥 UPDATED DRIVER OUTPUT
    drivers = [format_driver(d, target, goal) for d in top]

    # 🔥 SUMMARY
    if goal == "decrease" and "species" in target.lower():
        summary = "Drivers of biodiversity degradation"
    elif goal == "increase" and "species" in target.lower():
        summary = "Drivers of biodiversity increase"
    else:
        summary = f"Drivers of {target}"

    data = {
        "target": target,
        "drivers": top
    }

    # 🔥 RAG
    explanation = generate_drivers_explanation(target, top)

    # ======================================================
    # 🔥 POST-PROCESS FIX (GRAMMAR SAFE)
    # ======================================================

    if "species" in target.lower():

        explanation = explanation.replace(
            "shows a negative relationship with",
            "is negatively affected by"
        )

        explanation = explanation.replace(
            "exhibits negative associations with",
            "is further negatively influenced by"
        )

        explanation = explanation.replace(
            "linked to a decrease in the potential for species to live in the cell",
            "acting as drivers of biodiversity loss in the system"
        )

    # 🔥 DISCLAIMER
    explanation += (
        "\n\nNote: These relationships are based on statistical correlations "
        "and do not necessarily imply causation."
    )

    print("========== DRIVERS TASK END ==========\n")

    return {
        "summary": summary,
        "data": data,
        "drivers": drivers,
        "interpretation": explanation
    }