# -*- coding: utf-8 -*-

"""
Importance Compare Parser

Estrae i due driver da confrontare.
"""

from utils.feature_mapping import (
    FEATURE_MAPPING,
    ABSTRACT_FEATURES,
    SYNONYMS
)


# ======================================================
# ALL KNOWN CONCEPTS
# ======================================================

KNOWN_CONCEPTS = (

    list(FEATURE_MAPPING.keys())

    +

    list(ABSTRACT_FEATURES.keys())

    +

    list(SYNONYMS.keys())
)


# ======================================================
# PARSER
# ======================================================

def parse_importance_compare(question: str):

    q = question.lower()

    matches = []

    # --------------------------------------------------
    # RAW MATCHING
    # --------------------------------------------------

    for concept in KNOWN_CONCEPTS:

        if concept in q:

            matches.append(
                concept
            )

    # remove duplicates
    matches = list(
        dict.fromkeys(matches)
    )

    # --------------------------------------------------
    # REMOVE TARGETS
    # --------------------------------------------------

    matches = [

        m

        for m in matches

        if m != "risk"
    ]

    # --------------------------------------------------
    # KEEP MOST SPECIFIC MATCHES
    # --------------------------------------------------

    matches = sorted(
        matches,
        key=len,
        reverse=True
    )

    filtered = []

    for candidate in matches:

        if not any(

            candidate in existing

            for existing in filtered
        ):

            filtered.append(
                candidate
            )

    matches = filtered

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------

    print(
        "\n[IMPORTANCE_COMPARE PARSER]"
    )

    print(
        "matches =",
        matches
    )

    # --------------------------------------------------
    # VALIDATION
    # --------------------------------------------------

    if len(matches) < 2:

        return None

    # --------------------------------------------------
    # OUTPUT
    # --------------------------------------------------

    return {

        "entity_a":
            matches[0],

        "entity_b":
            matches[1]
    }