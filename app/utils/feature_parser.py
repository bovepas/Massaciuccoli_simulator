# -*- coding: utf-8 -*-

"""
Feature Parser v22
- scala corretta
- parsing numerico
- parsing semantico (warmer, drier, ecc.)
"""

import re


# ======================================================
# FEATURE MAP
# ======================================================

FEATURE_MAP = {
    "temperature": "Change in average temperature compared to a recent past",
    "precipitation": "Cumulative change in precipitation compared to a recent past",
    "biodiversity": "Number of species potentially living in the cell",
    "tree cover": "Density of tree cover",
    "grassland": "Presence of grassland",
    "evapotranspiration": "Relative change in the potential evapotranspiration compared to a recent past"
}


# ======================================================
# SEMANTIC MAP (🔥 NEW)
# ======================================================

SEMANTIC_MAP = {
    "warmer": ("temperature", 1.0),
    "hotter": ("temperature", 1.0),
    "cooler": ("temperature", -1.0),

    "drier": ("precipitation", -1.0),
    "dryer": ("precipitation", -1.0),
    "wetter": ("precipitation", 1.0),

    "more biodiversity": ("biodiversity", 10.0),
    "less biodiversity": ("biodiversity", -10.0),
}


# ======================================================
# BASELINE
# ======================================================

def build_default_features():
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
# MAIN PARSER
# ======================================================

def parse_features(question: str):

    q = question.lower()
    features = build_default_features()

    # --------------------------------------------------
    # NUMERIC PARSING
    # --------------------------------------------------

    pattern = r"(temperature|precipitation|biodiversity|tree cover|grassland|evapotranspiration)\s+(increases|decreases)\s+by\s+(-?\d+\.?\d*)"

    matches = re.findall(pattern, q)

    for var, direction, value in matches:

        value = float(value)

        if direction == "decreases":
            value = -value

        mapped = FEATURE_MAP.get(var)

        if mapped:
            features[mapped] = features[mapped] + value

    # --------------------------------------------------
    # SEMANTIC PARSING (🔥 NEW)
    # --------------------------------------------------

    for word, (var, delta) in SEMANTIC_MAP.items():

        if word in q:
            mapped = FEATURE_MAP.get(var)

            if mapped:
                features[mapped] = features[mapped] + delta

    # --------------------------------------------------
    # FALLBACK SIMPLE
    # --------------------------------------------------

    for var in FEATURE_MAP:

        mapped = FEATURE_MAP[var]

        if f"{var} increases" in q:
            features[mapped] += 1.0

        if f"{var} decreases" in q:
            features[mapped] -= 1.0

    return features