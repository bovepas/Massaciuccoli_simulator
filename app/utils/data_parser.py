# -*- coding: utf-8 -*-

"""
Data Parser — v2
(Canonical dataset coverage)

Maps user requests to canonical ecosystem variables.

✔ Full dataset coverage
✔ Centralized aliases
✔ Cleaner semantic matching
✔ Backward compatible
"""

# ======================================================
# CANONICAL VARIABLE MAP
# ======================================================

VARIABLE_ALIASES = {

    # --------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------

    "temperature": "temperature change",
    "warming": "temperature change",
    "heat": "temperature change",

    # --------------------------------------------------
    # PRECIPITATION
    # --------------------------------------------------

    "precipitation": "water from rain",
    "rain": "water from rain",
    "rainfall": "water from rain",

    # --------------------------------------------------
    # EVAPOTRANSPIRATION
    # --------------------------------------------------

    "evapotranspiration": "evapotranspiration change",
    "evaporation": "evapotranspiration change",
    "water loss": "evapotranspiration change",

    # --------------------------------------------------
    # TREE COVER
    # --------------------------------------------------

    "tree": "tree cover",
    "trees": "tree cover",
    "tree cover": "tree cover",
    "forest": "tree cover",
    "forest cover": "tree cover",

    # --------------------------------------------------
    # GRASSLAND
    # --------------------------------------------------

    "grass": "grassland",
    "grassland": "grassland",

    # --------------------------------------------------
    # BIODIVERSITY
    # --------------------------------------------------

    "species": "species richness",
    "species richness": "species richness",
    "biodiversity": "species richness",

    # --------------------------------------------------
    # PHENOLOGY
    # --------------------------------------------------

    "phenology": "vegetation productivity",
    "vegetation productivity": "vegetation productivity",
    "productivity": "vegetation productivity",

    # --------------------------------------------------
    # IMPERVIOUSNESS
    # --------------------------------------------------

    "imperviousness": "land imperviousness",
    "urbanization": "land imperviousness",
    "urbanisation": "land imperviousness",
    "urban expansion": "land imperviousness",

    # --------------------------------------------------
    # LAND USE
    # --------------------------------------------------

    "land use": "land use change",
    "land cover": "land use change",
}


# ======================================================
# MAIN
# ======================================================

def parse_data_request(
    question: str
):

    q = question.lower()

    for alias, variable in VARIABLE_ALIASES.items():

        if alias in q:

            return {
                "variable": variable
            }

    # --------------------------------------------------
    # fallback → latest system conditions
    # --------------------------------------------------

    return {
        "variable": None
    }