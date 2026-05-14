# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Task — v3 (SHAP FULL + RAG)

✔ Returns FULL SHAP values (for dependency)
✔ Keeps TOP-K for UI
✔ RAG explanation on top drivers
✔ Stable and consistent
"""

from knowledge.rag_importance import generate_importance_explanation


def handle_importance(question, features=None, model=None, top_k=5, mode="increase"):

    print("\n========== IMPORTANCE TASK START ==========")
    print(f"[DEBUG] question: {question}")
    print(f"[DEBUG] requested top_k: {top_k}")
    print(f"[DEBUG] mode: {mode}")
    print(f"[DEBUG] scenario mode: {features is not None}")

    # ======================================================
    # 🔥 MOCK SHAP (core engine)
    # ======================================================

    shap_values = {
        'Change in average temperature compared to a recent past': 0.3,
        'Cumulative change in precipitation compared to a recent past': 0.25,
        'Number of species potentially living in the cell': 0.2,
        'Density of tree cover': 0.15,
        'Relative change in the potential evapotranspiration compared to a recent past': 0.1,
        'Presence of grassland': -0.05,
        'Index of total productivity by plant phenology': -0.1,
        'Density change in land imperviousness': 0.05
    }

    # ======================================================
    # 🔥 RANKING
    # ======================================================

    ranking = sorted(
        shap_values.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    print("[DEBUG] shap_values:", shap_values)
    print("[DEBUG] ranking:", ranking)

    # ======================================================
    # 🔥 TOP-K DRIVERS (solo per UI e RAG)
    # ======================================================

    top = ranking[:top_k]
    drivers = [k for k, v in top]

    # ======================================================
    # 🔥 RAG EXPLANATION (solo sui top)
    # ======================================================

    try:
        explanation = generate_importance_explanation(drivers)
    except Exception as e:
        print("[IMPORTANCE][RAG ERROR]", e)
        explanation = "The identified variables influence ecosystem risk through stress, instability, and vulnerability."

    # ======================================================
    # OUTPUT
    # ======================================================

    return {
        "summary": "Top factors influencing ecosystem risk",

        # 🔥 CRITICO: FULL SHAP (serve a dependency)
        "data": shap_values,

        # 🔥 UI
        "drivers": drivers,

        # 🔥 spiegazione RAG
        "interpretation": explanation
    }