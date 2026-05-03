# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Task: ASSESSMENT v23 (scenario + delta + SHAP unified)
"""

import pandas as pd

from versions.v6_1_main import explain_with_shap
from knowledge.rag_assessment import generate_assessment_explanation


# ======================================================
# REQUIRED DEFAULTS
# ======================================================

REQUIRED_DEFAULTS = {
    "Land use and cover": "rural_natural",
    "Change in land use and cover in the past decade": "1",
    "Change in grassland presence  in the past decade": "0",
    "Change in tree cover density in the past decade": "0",
}


def ensure_model_features(features: dict) -> dict:

    full = features.copy()

    for k, v in REQUIRED_DEFAULTS.items():
        if k not in full:
            full[k] = v

    return full


# ======================================================
# BASELINE
# ======================================================

def build_baseline():

    return {
        'Density change in land imperviousness': 0,
        'Density of tree cover': 50,
        'Index of total productivity by plant phenology': 200,
        'Change in average temperature compared to a recent past': 0,
        'Relative change in the potential evapotranspiration compared to a recent past': 0,
        'Cumulative change in precipitation compared to a recent past': 0,
        'Number of species potentially living in the cell': 200,
        'Presence of grassland': 1,
    }


# ======================================================
# RISK LEVEL (replacing old function)
# ======================================================

def risk_level_from_score(score: float) -> str:

    if score < 0.33:
        return "Low Risk"
    elif score < 0.66:
        return "Medium Risk"
    else:
        return "High Risk"


# ======================================================
# CLEAN NAME
# ======================================================

def clean_name(name):

    name = name.lower()

    if "temperature" in name:
        return "temperature"
    if "precipitation" in name:
        return "precipitation"
    if "evapotranspiration" in name:
        return "evapotranspiration"
    if "tree cover" in name:
        return "tree cover"
    if "species" in name:
        return "biodiversity"
    if "phenology" in name:
        return "ecosystem productivity"
    if "grassland" in name:
        return "grassland"

    return name


# ======================================================
# MAIN
# ======================================================

def handle_assessment(question, parsed_features):

    print("\n========== ASSESSMENT TASK (v23) ==========")

    # --------------------------------------------------
    # BASELINE + SCENARIO
    # --------------------------------------------------

    baseline = build_baseline()
    scenario = baseline.copy()

    user_modified = []

    for k, v in parsed_features.items():
        if v != 0:
            scenario[k] = v
            user_modified.append(k)

    baseline = ensure_model_features(baseline)
    scenario = ensure_model_features(scenario)

    # --------------------------------------------------
    # SHAP instead of MODEL
    # --------------------------------------------------

    base_result = explain_with_shap(baseline)
    scen_result = explain_with_shap(scenario)

    score_base = base_result["risk_score"]
    score_scen = scen_result["risk_score"]

    delta = round(score_scen - score_base, 3)

    level_base = risk_level_from_score(score_base)
    level_scen = risk_level_from_score(score_scen)

    print(f"[DEBUG] Baseline: {score_base}")
    print(f"[DEBUG] Scenario: {score_scen}")
    print(f"[DEBUG] Delta: {delta}")

    # --------------------------------------------------
    # SHAP FEATURES
    # --------------------------------------------------

    shap_features = [f["feature"] for f in scen_result["features"]]

    # --------------------------------------------------
    # DRIVER UNION
    # --------------------------------------------------

    all_features = list(set(shap_features + user_modified))
    drivers = [clean_name(f) for f in all_features]

    # --------------------------------------------------
    # INTERPRETATION CORE
    # --------------------------------------------------

    if abs(delta) < 0.01:
        base_text = (
            f"Ecosystem risk remains stable at {round(score_scen,3)}."
        )
    else:
        direction = "increases" if delta > 0 else "decreases"

        base_text = (
            f"Ecosystem risk {direction} from {round(score_base,3)} "
            f"to {round(score_scen,3)} (Δ = {delta})."
        )

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

    rag_text = generate_assessment_explanation(
        [(f, scenario.get(f, 0)) for f in all_features]
    )

    interpretation = base_text

    if rag_text:
        interpretation += " " + rag_text

    print("========== ASSESSMENT TASK END ==========\n")

    return {
        "type": "assessment",
        "summary": "Ecosystem risk assessment",
        "data": {
            "baseline_score": round(score_base, 3),
            "scenario_score": round(score_scen, 3),
            "delta": delta,
            "baseline_level": level_base,
            "scenario_level": level_scen
        },
        "drivers": drivers,
        "interpretation": interpretation
    }