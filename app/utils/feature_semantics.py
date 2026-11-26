# -*- coding: utf-8 -*-

"""
Feature Semantics — v1
(Ecological interpretation layer)

This module provides semantic ecological context
for ecosystem variables used across the system.

The goal is NOT factual retrieval,
but ecological interpretation grounding
for RAG generation.

Derived from:
- CSV variable descriptions
- ecosystem risk methodology
- ecological preservation semantics
"""

FEATURE_SEMANTICS = {

    # ==================================================
    # IMPERVIOUSNESS
    # ==================================================

    "Density change in land imperviousness": {

        "ecological_role":
            "anthropogenic pressure indicator",

        "risk_interpretation":
            "Increasing land imperviousness reflects growing anthropogenic pressure and ecosystem sealing, which may contribute to environmental degradation.",

        "system_relevance":
            "Urban expansion and surface sealing may reduce ecological resilience and alter hydrological dynamics.",

        "risk_direction":
            "higher values are generally harmful"
    },

    # ==================================================
    # TREE COVER
    # ==================================================

    "Density of tree cover": {

        "ecological_role":
            "habitat structure indicator",

        "risk_interpretation":
            "Areas with high tree cover may represent ecologically valuable and fragile habitats that require preservation.",

        "system_relevance":
            "Tree cover contributes to biodiversity support, ecological stability, and climate regulation.",

        "risk_direction":
            "high values may indicate ecologically sensitive areas"
    },

    "Change in tree cover density in the past decade": {

        "ecological_role":
            "habitat change indicator",

        "risk_interpretation":
            "Loss of tree cover is considered environmentally harmful and may reflect habitat degradation.",

        "system_relevance":
            "Changes in tree cover may influence biodiversity, ecosystem resilience, and land stability.",

        "risk_direction":
            "tree cover loss is harmful"
    },

    # ==================================================
    # GRASSLAND
    # ==================================================

    "Presence of grassland": {

        "ecological_role":
            "natural habitat indicator",

        "risk_interpretation":
            "Grassland presence may identify ecologically valuable green areas that should be preserved.",

        "system_relevance":
            "Grasslands may support biodiversity and ecosystem connectivity.",

        "risk_direction":
            "high values may indicate fragile ecological areas"
    },

    "Change in grassland presence in the past decade": {

        "ecological_role":
            "habitat transformation indicator",

        "risk_interpretation":
            "Grassland loss is considered environmentally harmful and may reflect ecosystem degradation.",

        "system_relevance":
            "Changes in grassland coverage may alter habitat quality and biodiversity support.",

        "risk_direction":
            "grassland loss is harmful"
    },

    # ==================================================
    # LAND USE
    # ==================================================

    "Land use and cover": {

        "ecological_role":
            "territorial use indicator",

        "risk_interpretation":
            "Highly modified land-use scenarios may reflect anthropogenic alteration of ecosystems.",

        "system_relevance":
            "Industrial, artificial, or heavily modified land uses may increase ecological stress.",

        "risk_direction":
            "high anthropogenic modification may be harmful"
    },

    "Change in land use and cover in the past decade": {

        "ecological_role":
            "territorial transformation indicator",

        "risk_interpretation":
            "Increasing land-use modification may represent growing anthropogenic pressure on ecosystems.",

        "system_relevance":
            "Land-use change may alter habitat continuity and ecological resilience.",

        "risk_direction":
            "higher anthropogenic transformation is harmful"
    },

    # ==================================================
    # PRODUCTIVITY / PHENOLOGY
    # ==================================================

    "Index of total productivity by plant phenology": {

        "ecological_role":
            "vegetation productivity indicator",

        "risk_interpretation":
            "Highly productive ecosystems may represent ecologically valuable and fragile environments requiring preservation.",

        "system_relevance":
            "Vegetation productivity may reflect ecosystem functioning and ecological integrity.",

        "risk_direction":
            "high productivity may indicate ecologically sensitive areas"
    },

    # ==================================================
    # CLIMATE
    # ==================================================

    "Change in average temperature compared to a recent past": {

        "ecological_role":
            "climate stress indicator",

        "risk_interpretation":
            "Temperature increase is considered environmentally harmful and may reflect climate-related ecosystem stress.",

        "system_relevance":
            "Warming conditions may influence biodiversity, hydrology, vegetation, and ecosystem stability.",

        "risk_direction":
            "temperature increase is harmful"
    },

    "Relative change in the potential evapotranspiration compared to a recent past": {

        "ecological_role":
            "water balance indicator",

        "risk_interpretation":
            "Reduced water availability and evapotranspiration imbalance may contribute to ecological stress and aridity.",

        "system_relevance":
            "Evapotranspiration dynamics influence hydrological balance and ecosystem functioning.",

        "risk_direction":
            "reduced water availability is harmful"
    },

    "Cumulative change in precipitation compared to a recent past": {

        "ecological_role":
            "hydrological stress indicator",

        "risk_interpretation":
            "Reduced precipitation and increasing aridity are considered environmentally harmful.",

        "system_relevance":
            "Precipitation changes may influence water resources, vegetation, and ecological resilience.",

        "risk_direction":
            "precipitation decrease is harmful"
    },

    # ==================================================
    # BIODIVERSITY
    # ==================================================

    "Number of species potentially living in the cell": {

        "ecological_role":
            "biodiversity indicator",

        "risk_interpretation":
            "Areas with high species richness may represent ecologically fragile ecosystems that require preservation.",

        "system_relevance":
            "Species richness may reflect ecosystem resilience, habitat quality, and ecological integrity.",

        "risk_direction":
            "high biodiversity may indicate ecologically sensitive areas"
    },

    # ==================================================
    # ECOSYSTEM RISK
    # ==================================================

    "ecosystem_risk": {

        "ecological_role":
            "integrated ecosystem stress classification",

        "risk_interpretation":
            "Ecosystem risk emerges from the combined interaction of climatic, environmental, biodiversity, phenological, and anthropogenic stressors.",

        "system_relevance":
            "The classification identifies anomalous ecosystem conditions associated with ecological stress and fragility.",

        "risk_direction":
            "higher values indicate greater ecosystem stress"
    }
}


# ======================================================
# HELPERS
# ======================================================

def get_feature_semantics(feature_name):

    return FEATURE_SEMANTICS.get(
        feature_name,
        None
    )


def build_semantic_context(features):

    """
    Builds a concise semantic context block
    for RAG prompts.
    """

    if not features:
        return ""

    lines = []

    for feature in features:

        info = FEATURE_SEMANTICS.get(feature)

        if not info:
            continue

        lines.append(
            f"- {feature}: "
            f"{info['risk_interpretation']}"
        )

    if not lines:
        return ""

    return "\n".join(lines)