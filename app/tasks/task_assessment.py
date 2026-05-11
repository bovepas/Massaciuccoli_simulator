# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Task: ASSESSMENT v35 (driver ordering + causal interpretation)
"""

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

    print("\n========== ASSESSMENT TASK (v35) ==========")

    # --------------------------------------------------
    # BASELINE + SCENARIO
    # --------------------------------------------------

    baseline = build_baseline()
    scenario = baseline.copy()

    user_modified = []

    for k, v in parsed_features.items():
        if k in scenario and scenario[k] != v:
            scenario[k] = v
            user_modified.append(k)

    baseline = ensure_model_features(baseline)
    scenario = ensure_model_features(scenario)

    # --------------------------------------------------
    # SHAP
    # --------------------------------------------------

    base_result = explain_with_shap(baseline)
    scen_result = explain_with_shap(scenario)

    score_base = base_result["risk_score"]
    score_scen = scen_result["risk_score"]

    delta = round(score_scen - score_base, 3)

    print(f"[DEBUG] Baseline: {score_base}")
    print(f"[DEBUG] Scenario: {score_scen}")
    print(f"[DEBUG] Delta: {delta}")

    # --------------------------------------------------
    # DRIVER SELECTION (ONLY RELEVANT)
    # --------------------------------------------------

    shap_features = scen_result.get("top_features", [])

    # map cleaned names → best impact
    impact_map = {}

    for f in shap_features:
        cname = clean_name(f["feature"])
        impact = f["impact"]

        if cname not in impact_map:
            impact_map[cname] = impact
        else:
            # keep strongest version
            if abs(impact) > abs(impact_map[cname]):
                impact_map[cname] = impact

    # keep only user-modified variables
    relevant = {}

    for f in user_modified:
        cname = clean_name(f)
        if cname in impact_map:
            relevant[cname] = impact_map[cname]

    # fallback (no parsed change)
    if not relevant:
        for k, v in impact_map.items():
            if abs(v) > 0.01:
                relevant[k] = v

    # --------------------------------------------------
    # DRIVER ORDERING 🔥
    # --------------------------------------------------

    sorted_drivers = sorted(
        relevant.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    drivers = [d[0] for d in sorted_drivers]

    # split positive / negative
    increasing = [d[0] for d in sorted_drivers if d[1] > 0]
    decreasing = [d[0] for d in sorted_drivers if d[1] < 0]

    # --------------------------------------------------
    # INTERPRETATION CORE
    # --------------------------------------------------

    if abs(delta) < 0.01:
        base_text = f"Ecosystem risk remains stable at {round(score_scen,3)}."
    else:
        direction = "increases" if delta > 0 else "decreases"
        base_text = (
            f"Ecosystem risk {direction} from {round(score_base,3)} "
            f"to {round(score_scen,3)} (Δ = {delta})."
        )

    # --------------------------------------------------
    # CAUSAL LANGUAGE 🔥
    # --------------------------------------------------

    interpretation = base_text

    if increasing:
        if len(increasing) == 1:
            interpretation += f" The change is primarily driven by {increasing[0]}."
        else:
            interpretation += (
                f" The increase in risk is primarily driven by {', '.join(increasing[:-1])} "
                f"and {increasing[-1]}."
            )

    if decreasing:
        if len(decreasing) == 1:
            interpretation += f" Mitigating effects are associated with {decreasing[0]}."
        else:
            interpretation += (
                f" Mitigating effects are associated with {', '.join(decreasing[:-1])} "
                f"and {decreasing[-1]}."
            )

    # --------------------------------------------------
    # RAG (FILTERED)
    # --------------------------------------------------

    rag_input = [(d, relevant[d]) for d in drivers]
    rag_text = generate_assessment_explanation(rag_input)

    if rag_text:
        interpretation += " " + rag_text

    print("========== ASSESSMENT TASK END ==========\n")

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    return {
        "type": "assessment",
        "summary": "Ecosystem risk assessment",
        "data": {
            "baseline_score": round(score_base, 3),
            "scenario_score": round(score_scen, 3),
            "delta": delta
        },
        "drivers": drivers,
        "interpretation": interpretation
    }