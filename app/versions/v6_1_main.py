# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
v6_1_main — STABLE PROTOTYPE (signed impacts FIXED)
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
            - row.get("Density of tree cover", 0) * 0.002   # 🔥 più forte
            + row.get("Index of total productivity by plant phenology", 0) * 0.001
            + row.get("Number of species potentially living in the cell", 0) * 0.001
        )

        score = max(0, min(1, score))
        return [score]


MODEL = DummyModel()


# ======================================================
# SHAP (FAKE ma con SEGNI CORRETTI)
# ======================================================

def explain_with_shap(features: dict) -> dict:

    try:
        # ----------------------------
        # Risk score
        # ----------------------------
        risk_score = (
            features.get("Change in average temperature compared to a recent past", 0) * 0.2
            - features.get("Density of tree cover", 0) * 0.002
            + features.get("Index of total productivity by plant phenology", 0) * 0.001
            + features.get("Number of species potentially living in the cell", 0) * 0.001
        )

        risk_score = max(0, min(1, risk_score))
        risk_level = risk_level_from_score(risk_score)

        # ----------------------------
        # FAKE SHAP con segno
        # ----------------------------
        feature_list = []

        for name, value in features.items():

            lname = name.lower()

            # 🔥 SEGNI REALISTICI
            if "tree cover" in lname:
                impact = -float(value) * 0.01

            elif "temperature" in lname:
                impact = float(value) * 0.2

            elif "precipitation" in lname:
                impact = -float(value) * 0.01

            elif "grassland" in lname:
                impact = -float(value) * 0.005

            else:
                impact = float(value) * 0.01

            feature_list.append({
                "feature": name,
                "impact": impact,
                "type": "absolute"
            })

        # sort
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
# ROUTER (lasciato invariato)
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

CATEGORY_KEYWORDS = [
    "fish", "birds", "mammals", "insects",
    "molluscs", "reptiles", "amphibians", "crustaceans"
]

VARIABLE_KEYWORDS = [
    "temperature",
    "precipitation",
    "biodiversity",
    "evapotranspiration",
    "grassland",
    "tree cover",
    "land use"
]

SYSTEM_TARGETS = [
    "ecosystem",
    "risk",
    "ecosystem risk"
]

IMPORTANCE_KEYWORDS = [
    "most important",
    "most influential",
    "most relevant",
    "top",
    "main factors",
    "key drivers",
    "driving",
    "what drives",
    "which variables",
    "which factors",
    "drivers"
]


def detect_enm(q):
    for s in SPECIES_NAMES:
        if s in q:
            return True

    enm_keywords = [
        "habitat suitability",
        "species distribution",
        "distribution",
        "suitability"
    ]

    has_enm_intent = any(k in q for k in enm_keywords)
    has_bio_ref = any(c in q for c in CATEGORY_KEYWORDS)

    return has_enm_intent and has_bio_ref


def route_question(question: str):

    q = question.lower().strip()

    var_count = sum(v in q for v in VARIABLE_KEYWORDS)
    has_system = any(t in q for t in SYSTEM_TARGETS)
    has_importance = any(p in q for p in IMPORTANCE_KEYWORDS)

    if detect_enm(q):
        return {"type": "enm"}

    if any(p in q for p in ["compare", "vs", "versus", "difference between"]):
        return {"type": "comparison"}

    if "which" in q and " or " in q:
        return {"type": "comparison"}

    if "from" in q and "to" in q:
        return {"type": "delta"}

    if has_importance:
        return {"type": "importance"}

    if var_count >= 2 and has_system:
        return {"type": "assessment"}

    if "how does" in q and "if" in q:
        return {"type": "dependency"}

    if any(v in q for v in ["affect", "impact", "influence"]):
        return {"type": "dependency"}

    if "if" in q:
        if var_count == 1:
            return {"type": "dependency"}
        return {"type": "assessment"}

    return {"type": "assessment"}