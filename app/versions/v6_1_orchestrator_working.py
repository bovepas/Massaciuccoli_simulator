"""
Massaciuccoli Digital Twin
Orchestrator v6.8 — ENM Integrated
"""

import pandas as pd
import re

from versions.v6_main import route_question
from versions.v6_1_main import MODEL
from versions.v6_2_basin_engine import run_basin_simulation
from knowledge.rag_pipeline import generate_answer, call_llm

# 🔥 NUOVO IMPORT ENM
from enm.enm_engine import run_enm_analysis


# ======================================================
# CONFIG
# ======================================================

INTERPRETATION_MODE = "management"  # "scientific" | "management"


# ======================================================
# PRE-ROUTER
# ======================================================

def contains_numeric_stressor(question: str) -> bool:
    q = question.lower()

    stressor_keywords = [
        "temperature",
        "precipitation",
        "rain",
        "tree",
        "biodiversity",
        "productivity",
        "evapotranspiration"
    ]

    has_number = bool(re.search(r"\d", q))
    has_percent = "%" in q
    has_degree = "°c" in q or "celsius" in q

    has_stressor = any(s in q for s in stressor_keywords)

    return has_stressor and (has_number or has_percent or has_degree)


# ======================================================
# DETERMINISTIC CHANGE CLASSIFICATION
# ======================================================

def classify_change(relative_change: float) -> str:
    abs_change = abs(relative_change)

    if abs_change < 0.05:
        return "minor"
    elif abs_change < 0.20:
        return "moderate"
    else:
        return "substantial"


# ======================================================
# DETERMINISTIC INTERPRETATION CORE
# ======================================================

def build_quantitative_interpretation(results):

    baseline_mean = results["baseline"]["mean_risk"]
    scenario_mean = results["scenario"]["mean_risk"]

    baseline_high = results["baseline"]["high_share"]
    scenario_high = results["scenario"]["high_share"]

    delta_mean = results["delta_mean_risk"]
    delta_high = results["delta_high_risk_share"]

    relative_mean = delta_mean / baseline_mean if baseline_mean != 0 else 0
    relative_high = delta_high / baseline_high if baseline_high != 0 else 0

    mean_change_level = classify_change(relative_mean)
    high_change_level = classify_change(relative_high)

    if INTERPRETATION_MODE == "management":
        style_instruction = """
Explain in accessible language.
Do NOT prescribe management actions.
Do NOT suggest policies.
Focus only on ecological meaning and system stability.
"""
    else:
        style_instruction = """
Provide a formal scientific ecological interpretation.
Do NOT include policy recommendations.
"""

    prompt = f"""
You are an ecological risk interpretation engine.

The quantitative results are:

Baseline Mean Risk: {baseline_mean}
Scenario Mean Risk: {scenario_mean}
Absolute Change in Mean Risk: {delta_mean}
Relative Change in Mean Risk: {round(relative_mean * 100, 1)}%

Baseline High-Risk Share: {baseline_high}
Scenario High-Risk Share: {scenario_high}
Absolute Change in High-Risk Share: {delta_high}
Relative Change in High-Risk Share: {round(relative_high * 100, 1)}%

Deterministic classification:
- Mean risk change magnitude: {mean_change_level}
- High-risk area change magnitude: {high_change_level}

Tasks:
1. Explain what these changes mean ecologically.
2. Explain the implications for basin-level stability.
3. Use the deterministic classifications provided.
4. Do NOT perform new calculations.
5. Do NOT prescribe actions.

{style_instruction}
"""

    return call_llm(prompt)


# ======================================================
# MAIN HANDLER
# ======================================================

def handle_question(question: str):

    if contains_numeric_stressor(question):
        route = "regression_or_emulator"
    else:
        routing = route_question(question)
        print("ROUTING DEBUG:", routing)
        route = routing["route"]

    if route == "llm_only":
        return generate_answer(question)

    elif route == "regression_or_emulator":

        scenario = {}
        q = question.lower()

        if "temperature" in q:
            scenario["Change in average temperature compared to a recent past"] = 1

        if "precipitation" in q:
            scenario["Cumulative change in precipitation compared to a recent past"] = "-10%"

        if "tree" in q:
            scenario["Density of tree cover"] = "-10%"

        if "productivity" in q:
            scenario["Index of total productivity by plant phenology"] = "-10%"

        if "biodiversity" in q:
            scenario["Number of species potentially living in the cell"] = "-30%"

        # =========================
        # BASIN MODEL
        # =========================
        basin_results = run_basin_simulation(scenario)

        # =========================
        # ENM MODEL (MaxEnt)
        # =========================
        try:
            enm_results = run_enm_analysis("Alcedo atthis")
        except Exception as e:
            enm_results = {
                "species": "Alcedo atthis",
                "metrics": {"training_auc": None},
                "error": str(e)
            }

        # =========================
        # INTERPRETAZIONE
        # =========================
        interpretation = build_quantitative_interpretation(basin_results)

        return f"""
📊 Basin Simulation Results

Baseline Mean Risk: {basin_results["baseline"]["mean_risk"]}
Scenario Mean Risk: {basin_results["scenario"]["mean_risk"]}
Δ Mean Risk: {basin_results["delta_mean_risk"]}

Baseline High Risk Share: {basin_results["baseline"]["high_share"]}
Scenario High Risk Share: {basin_results["scenario"]["high_share"]}
Δ High Risk Share: {basin_results["delta_high_risk_share"]}

🧬 Habitat Suitability (MaxEnt)

Species: {enm_results.get("species")}
Training AUC: {enm_results.get("metrics", {}).get("training_auc")}

🧠 Interpretation

{interpretation}
""".strip()

    elif route == "refuse":
        return "Normative or prescriptive questions are outside the scope of this scientific digital twin."

    else:
        return "Routing not recognized."


# ======================================================
# CLI
# ======================================================

def run_cli():

    print("\n=== Massaciuccoli Digital Twin — Knowledge Engine v6.8 ===\n")
    print("Interpretation mode:", INTERPRETATION_MODE)
    print("Type 'exit' to quit.\n")

    while True:

        user_question = input("Ask a question: ")

        if user_question.lower() in ["exit", "quit"]:
            print("Exiting.")
            break

        print("\nProcessing...\n")

        answer = handle_question(user_question)

        print("\n=== Final Answer ===\n")
        print(answer)
        print("\n------------------------------------------------------------\n")


if __name__ == "__main__":
    run_cli()