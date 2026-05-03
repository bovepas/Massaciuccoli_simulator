"""
Massaciuccoli Digital Twin
Task: INTERACTION v5 — scenario_parser + counterfactual
"""

import pandas as pd

from versions.v6_1_main import (
    MODEL,
    risk_level_from_score,
    explain_with_shap
)

from knowledge.rag_interaction import generate_interaction_explanation
from utils.scenario_parser import parse_single_scenario  # ✅ FIX IMPORT


# ======================================================
# DEFAULTS
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

def build_realistic_baseline(dataset):
    baseline = dataset.median(numeric_only=True).to_dict()

    baseline["Land use and cover"] = "rural_natural"
    baseline["Change in land use and cover in the past decade"] = "1"
    baseline["Change in grassland presence  in the past decade"] = "0"
    baseline["Change in tree cover density in the past decade"] = "0"

    return baseline


# ======================================================
# CLEAN NAMES
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

def handle_interaction(question, parsed_features=None):

    print("\n========== INTERACTION TASK (v5) ==========")

    dataset = pd.read_csv("data/massaciuccoli_data.csv", skiprows=[1])

    # --------------------------------------------------
    # BASELINE
    # --------------------------------------------------

    baseline = build_realistic_baseline(dataset)

    # --------------------------------------------------
    # SCENARIO PARSING (🔥 NEW)
    # --------------------------------------------------

    if not parsed_features:
        parsed_features = parse_single_scenario(question)

    print("[DEBUG] Parsed features:", parsed_features)

    # --------------------------------------------------
    # APPLY SCENARIO
    # --------------------------------------------------

    scenario = baseline.copy()
    user_modified = []

    for k, v in parsed_features.items():
        if v is not None:
            scenario[k] = v
            user_modified.append(k)

    baseline = ensure_model_features(baseline)
    scenario = ensure_model_features(scenario)

    df_base = pd.DataFrame([baseline])
    df_scen = pd.DataFrame([scenario])

    # --------------------------------------------------
    # MODEL
    # --------------------------------------------------

    score_base = float(MODEL.predict(df_base)[0])
    score_scen = float(MODEL.predict(df_scen)[0])

    delta = round(score_scen - score_base, 3)

    level_base = risk_level_from_score(score_base)
    level_scen = risk_level_from_score(score_scen)

    print(f"[DEBUG] Baseline: {score_base}")
    print(f"[DEBUG] Scenario: {score_scen}")
    print(f"[DEBUG] Delta: {delta}")

    # --------------------------------------------------
    # SHAP
    # --------------------------------------------------

    shap_expl = explain_with_shap(df_scen)
    shap_features = [x["feature"] for x in shap_expl]

    relevant_features = list(set(shap_features) & set(user_modified))
    irrelevant_features = list(set(user_modified) - set(shap_features))

    all_features = list(set(shap_features + user_modified))

    drivers = [clean_name(f) for f in all_features]

    # --------------------------------------------------
    # INTERPRETATION
    # --------------------------------------------------

    if abs(delta) < 0.01:
        base_text = (
            f"Ecosystem risk remains stable ({round(score_base,3)}), "
            "indicating limited sensitivity to the combined changes."
        )
    else:
        direction = "increases" if delta > 0 else "decreases"

        base_text = (
            f"Ecosystem risk {direction} from {round(score_base,3)} "
            f"to {round(score_scen,3)} (Δ = {delta})."
        )

    rag_text = generate_interaction_explanation(
        features=[(f, scenario.get(f, 0)) for f in all_features],
        relevant=relevant_features,
        irrelevant=irrelevant_features
    )

    interpretation = base_text
    if rag_text:
        interpretation += " " + rag_text

    print("========== INTERACTION TASK END ==========\n")

    return {
        "type": "interaction",
        "summary": "Counterfactual ecosystem simulation",
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