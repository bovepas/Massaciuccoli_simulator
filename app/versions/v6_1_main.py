# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
v6_1_main — FULL (MODEL + SHAP + ROUTER v63)
"""

# ======================================================
# MODEL
# ======================================================

def risk_level_from_score(score: float) -> str:
    if score < 0.33:
        return "Low Risk"
    elif score < 0.66:
        return "Medium Risk"
    else:
        return "High Risk"


class DummyModel:
    def predict(self, df):

        row = df.iloc[0]

        score = (
            row.get("Change in average temperature compared to a recent past", 0) * 0.2
            - row.get("Density of tree cover", 0) * 0.002
            + row.get("Index of total productivity by plant phenology", 0) * 0.001
            + row.get("Number of species potentially living in the cell", 0) * 0.001
        )

        score = max(0, min(1, score))
        return [score]


MODEL = DummyModel()


# ======================================================
# SHAP (SAFE VERSION — FIXED)
# ======================================================

def explain_with_shap(features: dict) -> dict:

    try:
        risk_score = (
            float(features.get("Change in average temperature compared to a recent past", 0)) * 0.2
            - float(features.get("Density of tree cover", 0)) * 0.002
            + float(features.get("Index of total productivity by plant phenology", 0)) * 0.001
            + float(features.get("Number of species potentially living in the cell", 0)) * 0.001
        )

        risk_score = max(0, min(1, risk_score))
        risk_level = risk_level_from_score(risk_score)

        feature_list = []

        for name, value in features.items():

            # 🔥 SAFE CAST
            try:
                val = float(value)
            except:
                continue

            lname = name.lower()

            if "tree cover" in lname:
                impact = -val * 0.01
            elif "temperature" in lname:
                impact = val * 0.2
            elif "precipitation" in lname:
                impact = -val * 0.01
            elif "grassland" in lname:
                impact = -val * 0.005
            else:
                impact = val * 0.01

            feature_list.append({
                "feature": name,
                "impact": impact,
                "type": "absolute"
            })

        feature_list = sorted(
            feature_list,
            key=lambda x: abs(x["impact"]),
            reverse=True
        )

        return {
            "risk_score": float(risk_score),
            "risk_level": risk_level,
            "top_features": feature_list
        }

    except Exception as e:
        print(f"[SHAP ERROR] {e}")

        return {
            "risk_score": 0.0,
            "risk_level": "Unknown",
            "top_features": []
        }


# ======================================================
# ROUTER v63 (FIXED)
# ======================================================

import os


def load_species_names():
    base_path = "/app/enm/presence"
    species = set()

    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.startswith("Presence_") and f.endswith(".csv"):
                name = f.replace("Presence_", "").replace(".csv", "")
                name = name.replace("_", " ").lower()
                species.add(name)

    return species


SPECIES_NAMES = load_species_names()


VARIABLE_KEYWORDS = [
    "temperature",
    "precipitation",
    "biodiversity",
    "evapotranspiration",
    "grassland",
    "tree cover",
    "land use",
    "productivity"
]

DRIVER_VERBS = [
    "drive", "drives",
    "cause", "causes",
    "produce", "produces",
    "lead to", "leads to",
    "contribute", "contributes",
    "result in", "results in",
    "determine", "determines"
]

DEGRADATION_WORDS = [
    "loss", "decline", "decrease",
    "reduction", "degradation",
    "degrade", "worsen", "drop"
]

IMPORTANCE_KEYWORDS = [
    "most", "top", "influential"
]

RISK_KEYWORDS = [
    "ecosystem risk", "risk"
]


def route_question(question: str):

    print("\n================ ROUTER v63 DEBUG ================")

    q = question.lower().strip()
    print("QUESTION:", q)

    var_count = sum(v in q for v in VARIABLE_KEYWORDS)
    has_risk = any(t in q for t in RISK_KEYWORDS)
    has_if = "if" in q

    # ENM
    if any(s in q for s in SPECIES_NAMES) or "habitat suitability" in q:
        return {"type": "enm"}

    # COMPARISON
    if any(p in q for p in ["compare", "vs", "versus"]) or " or " in q:
        return {"type": "comparison"}

    # DELTA
    if "from" in q and "to" in q:
        return {"type": "delta"}

    if "goes from" in q:
        return {"type": "delta"}

    # =========================
    # 🔥 NEW RULE (FIX CRITICO)
    # =========================

    if "variables" in q:
        if any(w in q for w in ["increase", "decrease"]):
            if any(var in q for var in VARIABLE_KEYWORDS):
                return {"type": "drivers"}

    # =========================
    # IMPORTANCE SPECIAL
    # =========================

    if "main factors driving" in q and has_risk:
        return {"type": "importance"}

    if has_if and "drivers" in q:
        return {"type": "importance"}

    if any(k in q for k in ["most", "influential"]):
        return {"type": "importance"}

    # =========================
    # ASSESSMENT
    # =========================

    if has_risk and var_count >= 1:
        if "how" in q or has_if:
            return {"type": "assessment"}

    # =========================
    # DEPENDENCY
    # =========================

    if "how does" in q:
        if not has_risk:
            return {"type": "dependency"}

    if any(v in q for v in ["affect", "impact", "influence"]):
        if not has_risk:
            return {"type": "dependency"}

    if ("effect of" in q or "impact of" in q) and " on " in q:
        return {"type": "dependency"}

    # =========================
    # DRIVERS
    # =========================

    if not has_risk:
        if any(v in q for v in DRIVER_VERBS) or any(w in q for w in DEGRADATION_WORDS):
            if any(var in q for var in VARIABLE_KEYWORDS):
                return {"type": "drivers"}

    # =========================
    # DEFAULT
    # =========================

    if has_risk:
        return {"type": "assessment"}

    return {"type": "assessment"}