"""
Massaciuccoli Digital Twin
Task: Comparison (v3 — STRUCTURED DRIVERS + CLEAN RAG)
"""

import pandas as pd

from utils.feature_mapping import normalize_feature_name
from utils.scenario_parser import parse_comparison_scenarios
from knowledge.rag_comparison import generate_comparison_explanation

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


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

def handle_comparison(question, model):

    print("\n========== COMPARISON TASK START ==========")

    scenario_A, scenario_B = parse_comparison_scenarios(question)
     # --------------------------------------------------
    # 🔥 GUARDRAIL: INCOMPLETE / TEMPLATE QUESTION
    # --------------------------------------------------

    if question.strip().lower() in [
        "compare two environmental scenarios",
        "compare scenarios",
        "compare two scenarios"
    ]:
        return {
            "summary": "Incomplete request",
            "data": {},
            "drivers": [],
            "interpretation": (
                "Your request is incomplete. To compare environmental scenarios, "
                "please specify the variables and their values. "
                "Example: 'Compare ecosystem risk when temperature increases by 2°C "
                "versus when precipitation decreases by 10%.'"
            )
        }

    debug_print("[DEBUG] Parsed Scenario A:", scenario_A)
    debug_print("[DEBUG] Parsed Scenario B:", scenario_B)

    if not scenario_A or not scenario_B:
        return {
            "summary": "Comparison not recognized",
            "data": {},
            "drivers": [],
            "interpretation": "Could not parse scenarios"
        }

    base = get_base_scenario()

    input_A = base.copy()
    input_B = base.copy()

    structured_drivers = []

    # --------------------------------------------------
    # APPLY CHANGES (STRUCTURED)
    # --------------------------------------------------

    for k, v in scenario_A.items():
        feature = normalize_feature_name(k)
        if feature:
            input_A[feature] = v
            structured_drivers.append((feature, v, None))

    for k, v in scenario_B.items():
        feature = normalize_feature_name(k)
        if feature:
            input_B[feature] = v

            # match with A
            found = False
            for i, (f, va, vb) in enumerate(structured_drivers):
                if f == feature:
                    structured_drivers[i] = (f, va, v)
                    found = True
                    break

            if not found:
                structured_drivers.append((feature, None, v))

    debug_print("[DEBUG] Structured drivers:", structured_drivers)

    # --------------------------------------------------
    # MODEL
    # --------------------------------------------------

    df_A = pd.DataFrame([input_A])
    df_B = pd.DataFrame([input_B])

    score_A = float(model.predict(df_A)[0])
    score_B = float(model.predict(df_B)[0])

    delta = round(score_B - score_A, 3)

    debug_print(f"[DEBUG] Scores: A={score_A} | B={score_B} | Δ={delta}")

    # --------------------------------------------------
    # RAG (NEW)
    # --------------------------------------------------

    interpretation = generate_comparison_explanation(
        drivers=structured_drivers,
        delta=delta
    )

    print("========== COMPARISON TASK END ==========\n")

    return {
        "summary": "Scenario comparison",
        "data": {
            "scenario_a": {"score": round(score_A, 3)},
            "scenario_b": {"score": round(score_B, 3)},
            "delta": delta
        },
        "drivers": structured_drivers,
        "interpretation": interpretation
    }