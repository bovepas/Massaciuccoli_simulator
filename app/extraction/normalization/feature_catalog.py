FEATURES = [
    "Density change in land imperviousness",
    "Density of tree cover",
    "Change in tree cover density in the past decade",
    "Presence of grassland",
    "Change in grassland presence in the past decade",
    "Land use and cover",
    "Index of total productivity by plant phenology",
    "Change in average temperature compared to a recent past",
    "Relative change in the potential evapotranspiration compared to a recent past",
    "Cumulative change in precipitation compared to a recent past",
    "Number of species potentially living in the cell",
    "Change in land use and cover in the past decade",
]


FEATURE_WEIGHTS = {
    feature: 1.0
    for feature in FEATURES
}

FEATURE_WEIGHTS["Change in land use and cover in the past decade"] = 0.90


FEATURE_DISAMBIGUATION = {

    (
        "Land use and cover",
        "Change in land use and cover in the past decade",
    ): {

        "default": "Land use and cover",

        "historical_keywords": [
            "historical",
            "past",
            "decade",
            "over time",
            "in the last",
            "in the past",
        ],

        "transition_keywords": [
            "rural",
            "naturalistic",
            "industrial",
            "commercial",
            "military",
            "agricultural",
            "agriculture",
            "conversion",
            "transition",
        ],
    }
}


def get_features() -> list[str]:
    return FEATURES.copy()


def get_feature_weights() -> dict[str, float]:
    return FEATURE_WEIGHTS.copy()


def get_feature_disambiguation() -> dict:
    return FEATURE_DISAMBIGUATION.copy()