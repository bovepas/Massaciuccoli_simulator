# -*- coding: utf-8 -*-

"""
Feature Mapping — v7
(Expanded canonical dataset coverage)

✔ Supports synonyms
✔ Supports partial matching
✔ Handles unknown variables
✔ Supports abstract concepts
✔ Human-readable semantic labels
✔ Expanded ecosystem variable coverage
✔ Backward compatible
"""

# ======================================================
# CANONICAL FEATURE NAMES
# ======================================================

FEATURE_MAPPING = {

    # --------------------------------------------------
    # CLIMATE
    # --------------------------------------------------

    "temperature":
        "Change in average temperature compared to a recent past",

    "precipitation":
        "Cumulative change in precipitation compared to a recent past",

    "evapotranspiration":
        "Relative change in the potential evapotranspiration compared to a recent past",

    # --------------------------------------------------
    # VEGETATION / HABITAT
    # --------------------------------------------------

    "tree cover":
        "Density of tree cover",

    "tree cover change":
        "Change in tree cover density in the past decade",

    "grassland":
        "Presence of grassland",

    "grassland change":
        "Change in grassland presence in the past decade",

    # --------------------------------------------------
    # LAND USE
    # --------------------------------------------------

    "land use":
        "Land use and cover",

    "land use change":
        "Change in land use and cover in the past decade",

    # --------------------------------------------------
    # PRODUCTIVITY
    # --------------------------------------------------

    "productivity":
        "Index of total productivity by plant phenology",

    "phenology":
        "Index of total productivity by plant phenology",

    # --------------------------------------------------
    # BIODIVERSITY
    # --------------------------------------------------

    "species":
        "Number of species potentially living in the cell",

    "biodiversity":
        "Number of species potentially living in the cell",

    # --------------------------------------------------
    # URBANIZATION
    # --------------------------------------------------

    "imperviousness":
        "Density change in land imperviousness",

    # --------------------------------------------------
    # RISK
    # --------------------------------------------------

    "risk":
        "ecosystem_risk",
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

    "Change in tree cover density in the past decade":
        "tree cover change",

    "Presence of grassland":
        "grassland presence",

    "Change in grassland presence in the past decade":
        "grassland change",

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
    "Land use and cover":
        "land use",

    "Change in land use and cover in the past decade":
        "land-use change",

    # Generic fallback
    "ecosystem_risk":
        "ecosystem risk"
}


# ======================================================
# SYNONYMS
# ======================================================

SYNONYMS = {

    # Climate
    "temp": "temperature",
    "warming": "temperature",
    "heat": "temperature",

    "rain": "precipitation",
    "rainfall": "precipitation",
    "aridity": "precipitation",

    "evaporation": "evapotranspiration",

    # Vegetation / habitat
    "tree density": "tree cover",
    "forest": "tree cover",
    "forest cover": "tree cover",

    "habitat": "grassland",

    # Biodiversity
    "species richness": "species",

    "biodiversity decline": "biodiversity",
    "biodiversity conservation": "biodiversity",
    "biodiversity stress": "biodiversity",

    #land use
    "land-use change": "land use change",

    # Productivity
    "ecosystem productivity": "productivity",
    "vegetation productivity": "productivity",
    "vegetation growth": "productivity",

    # Vegetation / habitat
    "tree-cover restoration": "tree cover",
    "tree cover restoration": "tree cover",
    "forest restoration": "tree cover",

    # Urbanization
    "urbanization": "imperviousness",
    "urbanisation": "imperviousness",
    "urban expansion": "imperviousness",
}


# ======================================================
# KEYWORD MATCHING
# ======================================================

KEYWORD_MATCH = {

    "temperature": [
        "temperature",
        "warming",
        "heat"
    ],

    "precipitation": [
        "precipitation",
        "rain",
        "rainfall",
        "aridity"
    ],

    "evapotranspiration": [
        "evapotranspiration",
        "evaporation"
    ],

    "tree cover": [
        "tree",
        "forest",
        "tree cover"
    ],

    "imperviousness": [
        "impervious",
        "sealing",
        "urbanization",
        "urbanisation",
        "urban"
    ],

    "species": [
        "species",
        "biodiversity",
        "richness"
    ],

    "productivity": [
        "productivity",
        "phenology",
        "vegetation",
        "growth"
    ],

    "grassland": [
        "grassland",
        "habitat"
    ],

    "land use": [
        "land use",
        "land cover"
    ]
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

    "climate stress": [

        "Change in average temperature compared to a recent past",

        "Cumulative change in precipitation compared to a recent past",

        "Relative change in the potential evapotranspiration compared to a recent past"
    ],

    "hydrological stress": [

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