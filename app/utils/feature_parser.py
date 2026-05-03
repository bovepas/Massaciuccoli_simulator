"""
Feature Parser — v2 (CLEAN & ROBUST)

Estrae valori numerici dalle domande utente
→ usato da assessment / interaction

Output:
{
    "Change in average temperature compared to a recent past": 2.0,
    "Cumulative change in precipitation compared to a recent past": -20.0,
    ...
}
"""

import re


# ======================================================
# BASE FEATURES (DEFAULT SCENARIO)
# ======================================================

def get_default_features():
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
# HELPERS
# ======================================================

def extract_number(pattern, text):
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


# ======================================================
# MAIN PARSER
# ======================================================

def parse_features(question: str):

    q = question.lower()
    features = get_default_features()

    # --------------------------------------------------
    # 🌡️ TEMPERATURE
    # --------------------------------------------------
    temp = extract_number(r"(-?\d+(\.\d+)?)\s*°c", q)

    if temp is None:
        temp = extract_number(r"temperature.*?(-?\d+(\.\d+)?)", q)

    if temp is not None:
        features["Change in average temperature compared to a recent past"] = temp

    # --------------------------------------------------
    # 🌧️ PRECIPITATION
    # --------------------------------------------------
    precip = extract_number(r"(-?\d+(\.\d+)?)\s*%", q)

    if precip is not None:
        # attenzione: se c'è "decrease"
        if "decrease" in q or "drop" in q:
            precip = -abs(precip)
        elif "increase" in q:
            precip = abs(precip)

        features["Cumulative change in precipitation compared to a recent past"] = precip

    # --------------------------------------------------
    # 💧 EVAPOTRANSPIRATION
    # --------------------------------------------------
    et = extract_number(r"evapotranspiration.*?(-?\d+(\.\d+)?)\s*%", q)

    if et is not None:
        features["Relative change in the potential evapotranspiration compared to a recent past"] = et

    # --------------------------------------------------
    # 🌳 TREE COVER
    # --------------------------------------------------
    tree = extract_number(r"tree cover.*?(-?\d+(\.\d+)?)\s*%", q)

    if tree is not None:
        features["Density of tree cover"] = tree

    # --------------------------------------------------
    # 🏙️ IMPERVIOUSNESS
    # --------------------------------------------------
    imp = extract_number(r"imperviousness.*?(-?\d+(\.\d+)?)\s*%", q)

    if imp is not None:
        features["Density change in land imperviousness"] = imp

    # --------------------------------------------------
    # 🧬 BIODIVERSITY
    # --------------------------------------------------
    bio = extract_number(r"(\d+)\s*(species)", q)

    if bio is not None:
        features["Number of species potentially living in the cell"] = bio

    # --------------------------------------------------
    # 🌱 PRODUCTIVITY (fallback semplice)
    # --------------------------------------------------
    if "high productivity" in q:
        features["Index of total productivity by plant phenology"] = 300

    if "low productivity" in q:
        features["Index of total productivity by plant phenology"] = 100

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------
    print("[DEBUG] Parsed features:", features)

    return features