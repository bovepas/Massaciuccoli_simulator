# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Delta Task — v29 (final with implicit range support)
"""

import pandas as pd

from knowledge.rag_delta import generate_delta_explanation
from utils.feature_mapping import normalize_feature_name


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
# RISK LEVEL
# ======================================================

def risk_level_from_score(score: float) -> str:

    if score < 0.33:
        return "Low Risk"
    elif score < 0.66:
        return "Medium Risk"
    else:
        return "High Risk"


# ======================================================
# 🔥 GENERIC FALLBACK (IMPLICIT DELTA)
# ======================================================

def infer_simple_range(question):

    q = question.lower()

    keywords = [
        "temperature",
        "precipitation",
        "evapotranspiration",
        "biodiversity",
        "species",
        "tree cover",
        "impervious",
        "productivity",
        "land use"
    ]

    detected = None

    for k in keywords:
        if k in q:
            detected = k
            break

    if not detected:
        return None

    feature = normalize_feature_name(detected)

    if not feature:
        return None

    # direction
    if any(w in q for w in ["decrease", "reduce", "drop"]):
        direction = -1
    elif any(w in q for w in ["increase", "rise"]):
        direction = 1
    else:
        return None

    # magnitude (safe generic)
    magnitude = 10
    if "temperature" in detected:
        magnitude = 2

    return {
        "feature": feature,
        "from": 0,
        "to": direction * magnitude
    }


# ======================================================
# 🔥 FEATURE RECOVERY
# ======================================================

def recover_feature_from_question(question):

    q = question.lower()

    if "tree cover" in q:
        return normalize_feature_name("tree_cover")

    if "biodiversity" in q or "species" in q:
        return normalize_feature_name("biodiversity")

    if "evapotranspiration" in q:
        return normalize_feature_name("evapotranspiration")

    if "temperature" in q:
        return normalize_feature_name("temperature")

    if "precipitation" in q:
        return normalize_feature_name("precipitation")

    return None


# ======================================================
# MAIN
# ======================================================

def handle_delta(question, range_info, model):

    print("\n========== DELTA TASK START ==========")

    # 🔥 FALLBACK ATTIVO
    if not range_info:
        print("[DEBUG] No range detected → using implicit range")
        range_info = infer_simple_range(question)

        if not range_info:
            return {
                "summary": "Range not recognized",
                "data": {},
                "drivers": [],
                "interpretation": "Could not parse range"
            }

    feature = range_info["feature"]
    v_from = range_info["from"]
    v_to = range_info["to"]

    # 🔥 RECOVERY
    if feature is None:
        print("[DEBUG] Recovering feature from question...")
        feature = recover_feature_from_question(question)

    if feature is None:
        return {
            "summary": "Feature not recognized",
            "data": {},
            "drivers": [],
            "interpretation": "Could not identify the environmental variable."
        }

    base = get_base_scenario()

    scenario_a = base.copy()
    scenario_b = base.copy()

    scenario_a[feature] = v_from
    scenario_b[feature] = v_to

    print(f"[DEBUG] Feature: {feature}")
    print(f"[DEBUG] Range: {v_from} → {v_to}")

    df_a = pd.DataFrame([scenario_a])
    df_b = pd.DataFrame([scenario_b])

    score_a = float(model.predict(df_a)[0])
    score_b = float(model.predict(df_b)[0])

    delta = round(score_b - score_a, 3)

    print(f"[DEBUG] Scores: {score_a} → {score_b} | Δ = {delta}")

    drivers = [(feature, v_from, v_to)]

    risk_from = risk_level_from_score(score_a)
    risk_to = risk_level_from_score(score_b)

    interpretation = generate_delta_explanation(
        question,
        drivers,
        delta
    )

    print("========== DELTA TASK END ==========\n")

    return {
        "summary": "Change in ecosystem risk (range analysis)",
        "data": {
            "score_from": round(score_a, 3),
            "score_to": round(score_b, 3),
            "delta": delta,
            "risk_from": risk_from,
            "risk_to": risk_to
        },
        "drivers": drivers,
        "interpretation": interpretation
    }