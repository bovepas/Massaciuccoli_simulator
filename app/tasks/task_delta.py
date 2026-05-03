# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Delta Task — v23 (SHAP-based + range-aware + RAG aligned)
"""

from versions.v6_1_main import explain_with_shap
from knowledge.rag_delta import generate_delta_explanation


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
# RISK LEVEL (local replacement)
# ======================================================

def risk_level_from_score(score: float) -> str:

    if score < 0.33:
        return "Low Risk"
    elif score < 0.66:
        return "Medium Risk"
    else:
        return "High Risk"


# ======================================================
# MAIN
# ======================================================

def handle_delta(question, parsed_features, range_info):

    print("\n========== DELTA TASK START ==========")

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

    base = get_base_scenario()

    scenario_a = base.copy()
    scenario_b = base.copy()

    scenario_a[feature] = v_from
    scenario_b[feature] = v_to

    print(f"[DEBUG] Feature: {feature}")
    print(f"[DEBUG] Range: {v_from} → {v_to}")

    # --------------------------------------------------
    # SHAP instead of MODEL
    # --------------------------------------------------

    result_a = explain_with_shap(scenario_a)
    result_b = explain_with_shap(scenario_b)

    score_a = result_a["risk_score"]
    score_b = result_b["risk_score"]

    delta = round(score_b - score_a, 3)

    drivers = [(feature, v_from, v_to)]

    print(f"[DEBUG] Scores: {score_a} → {score_b} | Δ = {delta}")

    # --------------------------------------------------
    # RISK LEVELS
    # --------------------------------------------------

    risk_from = risk_level_from_score(score_a)
    risk_to = risk_level_from_score(score_b)

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

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