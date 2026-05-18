# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Task — v6 (CLEAN OUTPUT + SIGN SPLIT)

✔ Filters noise (low impact features)
✔ Separates increasing vs decreasing drivers
✔ Keeps SHAP logic unchanged
✔ Keeps RAG unchanged
"""

from knowledge.rag_importance import generate_importance_explanation
from utils.model_input_builder import build_input_df, compute_baseline


def handle_importance(question, features=None, model=None, dataset=None, top_k=5, mode="increase"):

    print("\n========== IMPORTANCE TASK START ==========")
    print(f"[DEBUG] question: {question}")
    print(f"[DEBUG] requested top_k: {top_k}")

    if model is None or dataset is None:
        return {
            "summary": "Model not available",
            "data": {},
            "drivers": [],
            "interpretation": "The model or dataset is missing."
        }

    # ======================================================
    # BASELINE INPUT
    # ======================================================

    baseline_values = compute_baseline(dataset)
    df_base = build_input_df({}, dataset)

    base_pred = float(model.predict(df_base)[0])

    print(f"[DEBUG] Baseline prediction: {base_pred}")

    # ======================================================
    # FEATURE IMPORTANCE (PERTURBATION)
    # ======================================================

    shap_values = {}

    for feature in baseline_values.keys():

        test_values = baseline_values.copy()
        val = baseline_values[feature]

        if isinstance(val, (int, float)):
            test_values[feature] = val * 1.1
        else:
            continue

        df_test = build_input_df(test_values, dataset)

        pred = float(model.predict(df_test)[0])

        impact = pred - base_pred

        shap_values[feature] = round(impact, 4)

    print("[DEBUG] shap_values:", shap_values)

    # ======================================================
    # 🔥 FILTER NOISE (NEW)
    # ======================================================

    shap_values = {
        k: v for k, v in shap_values.items()
        if abs(v) > 0.01
    }

    # ======================================================
    # RANKING
    # ======================================================

    ranking = sorted(
        shap_values.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    top = ranking[:top_k]

    # ======================================================
    # 🔥 SPLIT POSITIVE / NEGATIVE (NEW)
    # ======================================================

    positive = [(k, v) for k, v in top if v > 0]
    negative = [(k, v) for k, v in top if v < 0]

    # ======================================================
    # STRUCTURED DRIVERS
    # ======================================================

    structured_drivers = [
        {"name": k, "impact": round(v, 4)}
        for k, v in top
    ]

    print("[DEBUG] structured_drivers:", structured_drivers)

    # ======================================================
    # UI DRIVERS (CLEAN FORMAT)
    # ======================================================

    drivers = []

    if positive:
        drivers.append("📈 Increasing risk:")
        drivers.extend([
            f"{k} (impact={round(v, 3)})"
            for k, v in positive
        ])

    # ======================================================
    # 🔥 OPTIONAL: show negative only if question is generic
    # ======================================================

    if negative and "increase" not in question.lower():
        drivers.append("📉 Reducing risk:")
        drivers.extend([
            f"{k} (impact={round(v, 3)})"
            for k, v in negative
        ])

    # ======================================================
    # RAG EXPLANATION
    # ======================================================

    try:
        explanation = generate_importance_explanation(structured_drivers, question)
    except Exception as e:
        print("[IMPORTANCE][RAG ERROR]", e)
        explanation = "The identified variables influence ecosystem risk through environmental stress and system imbalance."

    # ======================================================
    # OUTPUT
    # ======================================================

    return {
        "summary": "Top factors influencing ecosystem risk",
        "data": shap_values,
        "drivers": drivers,
        "interpretation": explanation
    }