# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Task Handler - v22 (FIX scenario detection)
"""

from typing import Dict, Any
import re

from knowledge.retriever import retrieve_documents
from versions.v6_1_main import explain_with_shap


# ======================================================
# UTILS
# ======================================================

def extract_top_k(question: str, default: int = 5) -> int:
    match = re.search(r'\btop\s*(\d+)\b', question.lower())
    if match:
        return int(match.group(1))
    return default


def detect_mode(question: str) -> str:
    q = question.lower()

    if "reduce" in q or "decrease" in q:
        return "reduce"
    elif "increase" in q:
        return "increase"
    else:
        return "absolute"


def format_feature_statement(feature_data: Dict) -> str:
    name = feature_data["feature"]

    if "impact" in feature_data:
        impact = feature_data["impact"]
        if impact > 0:
            return f"{name} contributes to higher predicted ecosystem risk"
        else:
            return f"{name} contributes to lower predicted ecosystem risk"

    return f"{name} influences ecosystem risk"


# ======================================================
# BASELINE (🔥 FIX QUI)
# ======================================================

def get_baseline():
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
# MAIN HANDLER
# ======================================================

def handle_importance(question: str, features: Dict[str, Any]) -> Dict[str, Any]:

    print("\n========== IMPORTANCE TASK START ==========")

    # --------------------------------------------------
    # Parse intent
    # --------------------------------------------------
    top_k = extract_top_k(question)
    mode = detect_mode(question)

    print(f"[DEBUG] requested top_k: {top_k}")
    print(f"[DEBUG] mode: {mode}")

    # --------------------------------------------------
    # 🔥 FIX SCENARIO DETECTION
    # --------------------------------------------------
    baseline = get_baseline()

    scenario_mode = any(
        features.get(k) != v for k, v in baseline.items()
    )

    print(f"[DEBUG] scenario mode: {scenario_mode}")

    # --------------------------------------------------
    # SHAP
    # --------------------------------------------------
    shap_result = explain_with_shap(features)

    risk_score = shap_result.get("risk_score", 0.0)
    risk_level = shap_result.get("risk_level", "Unknown")
    all_features = shap_result.get("top_features", [])

    if not all_features:
        return {
            "summary": "No features available",
            "data": {},
            "drivers": [],
            "interpretation": "Model could not compute feature importance."
        }

    # --------------------------------------------------
    # FILTER
    # --------------------------------------------------
    if mode == "reduce":
        filtered = [f for f in all_features if f["impact"] < 0]

    elif mode == "increase":
        filtered = [f for f in all_features if f["impact"] > 0]

    else:
        filtered = all_features

    if not filtered:
        filtered = all_features

    # --------------------------------------------------
    # SORT + SELECT
    # --------------------------------------------------
    filtered = sorted(
        filtered,
        key=lambda x: abs(x["impact"]),
        reverse=True
    )

    top_features = filtered[:top_k]

    print("[DEBUG] top features:", [f["feature"] for f in top_features])

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------
    feature_names = ", ".join([f["feature"] for f in top_features])

    rag_query = (
        f"mechanisms linking {feature_names} to ecosystem risk, "
        f"including climate stress, biodiversity response, "
        f"land use change, and ecosystem resilience"
    )

    docs, _ = retrieve_documents(rag_query)
    rag_text = "\n".join([d["text"] for d in docs])

    # --------------------------------------------------
    # INTERPRETATION
    # --------------------------------------------------
    statements = [format_feature_statement(f) for f in top_features]

    interpretation = ""

    if scenario_mode:
        interpretation += "Under the specified scenario, "

    interpretation += "the model identifies the following drivers:\n\n"
    interpretation += "; ".join(statements) + ".\n\n"
    interpretation += "Scientific literature indicates:\n\n"
    interpretation += rag_text[:1200]

    print("\n========== IMPORTANCE TASK END ==========\n")

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------
    return {
        "summary": f"Top {len(top_features)} drivers of ecosystem risk",
        "data": {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "top_features": top_features
        },
        "drivers": [f["feature"] for f in top_features],
        "interpretation": interpretation
    }