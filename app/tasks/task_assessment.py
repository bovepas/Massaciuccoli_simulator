# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Task: ASSESSMENT v36 (structured logging)

✔ Added structured logging
✔ No logic changes
✔ Fully debuggable pipeline
"""

from versions.v6_1_main import explain_with_shap
from knowledge.rag_assessment import generate_assessment_explanation

from utils.logger import (
    log_section,
    log_data,
    log_error
)

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

    log_section("ASSESSMENT TASK")

    # --------------------------------------------------
    # BASELINE + SCENARIO
    # --------------------------------------------------

    try:
        baseline = build_baseline()
        scenario = baseline.copy()

        user_modified = []

        for k, v in parsed_features.items():
            if k in scenario and scenario[k] != v:
                scenario[k] = v
                user_modified.append(k)

        baseline = ensure_model_features(baseline)
        scenario = ensure_model_features(scenario)

        log_section("SCENARIO")
        log_data("baseline", baseline)
        log_data("scenario", scenario)
        log_data("user_modified", user_modified)

    except Exception as e:
        log_error("SCENARIO BUILD", e)
        raise

    # --------------------------------------------------
    # SHAP
    # --------------------------------------------------

    try:
        base_result = explain_with_shap(baseline)
        scen_result = explain_with_shap(scenario)

        score_base = base_result["risk_score"]
        score_scen = scen_result["risk_score"]

        delta = round(score_scen - score_base, 3)

        log_section("SHAP RESULTS")
        log_data("baseline_score", score_base)
        log_data("scenario_score", score_scen)
        log_data("delta", delta)
        log_data("top_features", scen_result.get("top_features", []))

    except Exception as e:
        log_error("SHAP", e)
        raise

    # --------------------------------------------------
    # DRIVER SELECTION
    # --------------------------------------------------

    try:
        shap_features = scen_result.get("top_features", [])

        impact_map = {}

        for f in shap_features:
            cname = clean_name(f["feature"])
            impact = f["impact"]

            if cname not in impact_map:
                impact_map[cname] = impact
            else:
                if abs(impact) > abs(impact_map[cname]):
                    impact_map[cname] = impact

        relevant = {}

        for f in user_modified:
            cname = clean_name(f)
            if cname in impact_map:
                relevant[cname] = impact_map[cname]

        if not relevant:
            for k, v in impact_map.items():
                if abs(v) > 0.01:
                    relevant[k] = v

        log_section("DRIVER SELECTION")
        log_data("impact_map", impact_map)
        log_data("relevant_drivers", relevant)

    except Exception as e:
        log_error("DRIVER SELECTION", e)
        raise

    # --------------------------------------------------
    # DRIVER ORDERING
    # --------------------------------------------------

    sorted_drivers = sorted(
        relevant.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    drivers = [d[0] for d in sorted_drivers]

    increasing = [d[0] for d in sorted_drivers if d[1] > 0]
    decreasing = [d[0] for d in sorted_drivers if d[1] < 0]

    log_section("DRIVER ORDERING")
    log_data("sorted", sorted_drivers)
    log_data("increasing", increasing)
    log_data("decreasing", decreasing)

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

    interpretation = base_text

    # --------------------------------------------------
    # CAUSAL LANGUAGE
    # --------------------------------------------------

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
    # RAG
    # --------------------------------------------------

    try:
        rag_input = [(d, relevant[d]) for d in drivers]
        rag_text = generate_assessment_explanation(rag_input)

        log_section("RAG")
        log_data("rag_input", rag_input)
        log_data("rag_text", rag_text)

        if rag_text:
            interpretation += " " + rag_text

    except Exception as e:
        log_error("RAG", e)

    log_section("ASSESSMENT END")

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