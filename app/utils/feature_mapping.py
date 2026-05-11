# -*- coding: utf-8 -*-

"""
Feature Mapping — v4 (ROBUST NLP MATCHING)

✔ Supports synonyms
✔ Supports partial matching
✔ Handles unknown variables
✔ Backward compatible
"""

# ======================================================
# CANONICAL FEATURE NAMES
# ======================================================

FEATURE_MAPPING = {
    "temperature": "Change in average temperature compared to a recent past",
    "precipitation": "Cumulative change in precipitation compared to a recent past",
    "evapotranspiration": "Relative change in the potential evapotranspiration compared to a recent past",
    "tree cover": "Density of tree cover",
    "imperviousness": "Density change in land imperviousness",
    "species": "Number of species potentially living in the cell",
    "biodiversity": "Number of species potentially living in the cell",
    "productivity": "Index of total productivity by plant phenology",
    "phenology": "Index of total productivity by plant phenology",
    "grassland": "Presence of grassland",
    "risk": "ecosystem_risk",
}

# ======================================================
# SYNONYMS
# ======================================================

SYNONYMS = {
    "temp": "temperature",
    "rain": "precipitation",
    "rainfall": "precipitation",
    "evaporation": "evapotranspiration",
    "tree density": "tree cover",
    "forest": "tree cover",
    "species richness": "species",
    "ecosystem productivity": "productivity",
    "vegetation productivity": "productivity",
}

# ======================================================
# KEYWORD MATCHING (🔥 NEW)
# ======================================================

KEYWORD_MATCH = {
    "temperature": ["temperature", "warming", "heat"],
    "precipitation": ["precipitation", "rain", "rainfall"],
    "evapotranspiration": ["evapotranspiration", "evaporation"],
    "tree cover": ["tree", "forest"],
    "imperviousness": ["impervious", "sealing", "urbanization"],
    "species": ["species", "biodiversity", "richness"],
    "productivity": ["productivity", "phenology", "vegetation"],
    "grassland": ["grassland"],
}


# ======================================================
# NORMALIZATION
# ======================================================

def normalize_feature_name(name: str):

    if not name:
        return None

    name = name.lower().strip()

    # --------------------------------------------------
    # 1️⃣ SYNONYM DIRECT
    # --------------------------------------------------

    if name in SYNONYMS:
        name = SYNONYMS[name]

    # --------------------------------------------------
    # 2️⃣ EXACT MATCH
    # --------------------------------------------------

    if name in FEATURE_MAPPING:
        return FEATURE_MAPPING[name]

    # --------------------------------------------------
    # 3️⃣ PARTIAL MATCH (🔥 KEY FEATURE)
    # --------------------------------------------------

    for canonical, keywords in KEYWORD_MATCH.items():
        for kw in keywords:
            if kw in name:
                return FEATURE_MAPPING.get(canonical)

    # --------------------------------------------------
    # 4️⃣ FALLBACK
    # --------------------------------------------------

    return None