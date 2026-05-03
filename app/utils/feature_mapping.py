"""
Feature Mapping — v3 (COMPATIBILITY FIX)

✔ Backward compatible with old parsers (FEATURE_MAPPING)
✔ Clean mapping layer
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
    "risk": "ecosystem_risk",  # 🔥 NEW (fondamentale)
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
    "species richness": "species",
}

# ======================================================
# NORMALIZATION
# ======================================================

def normalize_feature_name(name: str):

    name = name.lower().strip()

    if name in SYNONYMS:
        name = SYNONYMS[name]

    return FEATURE_MAPPING.get(name, None)