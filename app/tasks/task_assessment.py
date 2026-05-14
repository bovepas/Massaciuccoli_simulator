# task_assessment.py

from tasks.task_importance import handle_importance
from knowledge.rag_assessment import generate_assessment_explanation

def handle_assessment(question, features=None):

    print("\n========== ASSESSMENT TASK ==========")

    # ======================================================
    # 🛡️ SAFE BASELINE (fallback)
    # ======================================================

    if features is None:
        features = {}

    # ======================================================
    # 🔥 MOCK SHAP (come importance)
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

    top = ranking[:5]
    drivers = [k for k, v in top]

    print("[DEBUG] shap_values:", shap_values)
    print("[DEBUG] ranking:", ranking)

    # ======================================================
    # 🔥 RAG EXPLANATION
    # ======================================================

    explanation = generate_assessment_explanation(
        question=question,
        drivers=drivers
    )

    # ======================================================
    # OUTPUT
    # ======================================================

    return {
        "summary": "Assessment of ecosystem risk drivers",
        "data": dict(top),
        "drivers": drivers,
        "interpretation": explanation
    }