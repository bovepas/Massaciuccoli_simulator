# -*- coding: utf-8 -*-

"""
Feature Mapping — v6 (SEMANTIC PRESENTATION LAYER)

✔ Supports synonyms
✔ Supports partial matching
✔ Handles unknown variables
✔ Supports abstract concepts
✔ Human-readable semantic labels
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
# HUMAN-READABLE LABELS
# ======================================================

FEATURE_LABELS = {

    # Climate
    "Change in average temperature compared to a recent past":
        "temperature change",

    "Cumulative change in precipitation compared to a recent past":
        "precipitation change",

    "Relative change in the potential evapotranspiration compared to a recent past":
        "evapotranspiration change",

    # Vegetation / habitat
    "Density of tree cover":
        "tree cover density",

    "Presence of grassland":
        "grassland presence",

    # Biodiversity
    "Number of species potentially living in the cell":
        "species richness",

    # Productivity
    "Index of total productivity by plant phenology":
        "vegetation productivity",

    # Urbanization
    "Density change in land imperviousness":
        "land imperviousness",

    # Land use
    "Change in land use and cover in the past decade anthropogenic change":
        "anthropogenic land-use change",

    "Change in land use and cover in the past decade no change or natural":
        "stable natural land-use",

    # Generic fallback
    "ecosystem_risk":
        "ecosystem risk"
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
# KEYWORD MATCHING
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
# ABSTRACT FEATURES
# ======================================================

ABSTRACT_FEATURES = {
    "water availability": [
        "Cumulative change in precipitation compared to a recent past",
        "Relative change in the potential evapotranspiration compared to a recent past"
    ],

    "water level": [
        "Cumulative change in precipitation compared to a recent past",
        "Relative change in the potential evapotranspiration compared to a recent past"
    ],

    "hydrology": [
        "Cumulative change in precipitation compared to a recent past",
        "Relative change in the potential evapotranspiration compared to a recent past"
    ]
}


# ======================================================
# ABSTRACT NORMALIZATION
# ======================================================

def normalize_abstract_feature(name: str):

    if not name:
        return None

    name = name.lower()

    for k, v in ABSTRACT_FEATURES.items():

        if k in name:
            return v

    return None


# ======================================================
# NORMALIZATION
# ======================================================

def normalize_feature_name(name: str):

    if not name:
        return None

    name = name.lower().strip()

    # --------------------------------------------------
    # ABSTRACT MATCH
    # --------------------------------------------------

    abstract = normalize_abstract_feature(name)

    if abstract:
        return abstract

    # --------------------------------------------------
    # SYNONYM DIRECT
    # --------------------------------------------------

    if name in SYNONYMS:
        name = SYNONYMS[name]

    # --------------------------------------------------
    # EXACT MATCH
    # --------------------------------------------------

    if name in FEATURE_MAPPING:
        return FEATURE_MAPPING[name]

    # --------------------------------------------------
    # PARTIAL MATCH
    # --------------------------------------------------

    for canonical, keywords in KEYWORD_MATCH.items():

        for kw in keywords:

            if kw in name:
                return FEATURE_MAPPING.get(canonical)

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------

    return None


# ======================================================
# SEMANTIC PRESENTATION
# ======================================================

def prettify_feature_name(name: str):

    """
    Converts canonical dataset feature names
    into concise human-readable labels.
    """

    if not name:
        return name

    # direct mapping
    if name in FEATURE_LABELS:
        return FEATURE_LABELS[name]

    # partial matching fallback
    for canonical, pretty in FEATURE_LABELS.items():

        if canonical.lower() in name.lower():
            return pretty

    # graceful fallback
    return name


# ======================================================
# BULK PRETTIFICATION
# ======================================================

def prettify_feature_dict(feature_dict):

    if not feature_dict:
        return {}

    pretty = {}

    for k, v in feature_dict.items():

        pretty_name = prettify_feature_name(k)

        pretty[pretty_name] = v

    return pretty