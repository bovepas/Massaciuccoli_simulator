# -*- coding: utf-8 -*-

"""
Drivers Parser — v4
(Canonical dataset coverage)

✔ Robust goal detection
✔ Canonical ecosystem variable aliases
✔ Cleaner semantic matching
✔ Backward compatible
"""

# ======================================================
# FEATURE ALIASES
# ======================================================

FEATURE_ALIASES = {

    # --------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------

    "temperature": "temperature",
    "warming": "temperature",
    "heat": "temperature",

    # --------------------------------------------------
    # PRECIPITATION
    # --------------------------------------------------

    "precipitation": "precipitation",
    "rainfall": "precipitation",
    "rain": "precipitation",

    # --------------------------------------------------
    # EVAPOTRANSPIRATION
    # --------------------------------------------------

    "evapotranspiration": "evapotranspiration",
    "evaporation": "evapotranspiration",
    "water loss": "evapotranspiration",

    # --------------------------------------------------
    # BIODIVERSITY
    # --------------------------------------------------

    "biodiversity": "biodiversity",
    "species richness": "biodiversity",
    "species": "biodiversity",

    # --------------------------------------------------
    # TREE COVER
    # --------------------------------------------------

    "tree cover": "tree_cover",
    "forest cover": "tree_cover",
    "trees": "tree_cover",

    # --------------------------------------------------
    # GRASSLAND
    # --------------------------------------------------

    "grassland": "grassland",
    "grass": "grassland",

    # --------------------------------------------------
    # PHENOLOGY
    # --------------------------------------------------

    "phenology": "phenology",
    "vegetation productivity": "phenology",
    "productivity": "phenology",

    # --------------------------------------------------
    # IMPERVIOUSNESS
    # --------------------------------------------------

    "imperviousness": "imperviousness",
    "urbanization": "imperviousness",
    "urbanisation": "imperviousness",
    "urban expansion": "imperviousness",

    # --------------------------------------------------
    # LAND USE
    # --------------------------------------------------

    "land use": "land_use",
    "land cover": "land_use"
}


# ======================================================
# GOAL KEYWORDS
# ======================================================

DEGRADE_KEYWORDS = [

    "degrade",
    "degradation",
    "decrease",
    "reduce",
    "reduction",
    "decline",
    "loss",
    "losing",
    "worsen",
    "drop"
]

INCREASE_KEYWORDS = [

    "increase",
    "increasing",
    "improve",
    "improvement",
    "enhance",
    "growth",
    "grow",
    "rise"
]


# ======================================================
# TARGET DETECTION
# ======================================================

def parse_drivers_target(
    question: str
):

    q = question.lower()

    for alias, canonical in FEATURE_ALIASES.items():

        if alias in q:
            return canonical

    return None


# ======================================================
# GOAL DETECTION
# ======================================================

def parse_drivers_goal(
    question: str
):

    q = question.lower()

    if any(

        k in q

        for k in DEGRADE_KEYWORDS
    ):

        return "decrease"

    if any(

        k in q

        for k in INCREASE_KEYWORDS
    ):

        return "increase"

    return "neutral"