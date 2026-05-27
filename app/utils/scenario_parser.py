# -*- coding: utf-8 -*-

"""
Scenario Parser — v8
(Canonical dataset coverage)

Supporta:
- comparison (vs / versus / or)
- first / second
- one with ... and one with ...
- delta (from X to Y)
- implicit numeric scenarios
- canonical ecosystem variables

Design goals:
✔ Full dataset variable coverage
✔ Centralized feature aliases
✔ Cleaner semantic parsing
✔ Backward compatible
✔ Easier future extension
"""

import re


# ======================================================
# CANONICAL FEATURES
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

    # --------------------------------------------------
    # PHENOLOGY / VEGETATION PRODUCTIVITY
    # --------------------------------------------------

    "phenology": "phenology",
    "vegetation productivity": "phenology",
    "productivity": "phenology",

    # --------------------------------------------------
    # IMPERVIOUSNESS / URBANIZATION
    # --------------------------------------------------

    "imperviousness": "imperviousness",
    "urbanization": "imperviousness",
    "urbanisation": "imperviousness",
    "urban expansion": "imperviousness",
    "land imperviousness": "imperviousness",

    # --------------------------------------------------
    # LAND USE
    # --------------------------------------------------

    "land use": "land_use",
    "land cover": "land_use",
    "land use change": "land_use",
}


# ======================================================
# HELPERS
# ======================================================

def extract_numbers(text):

    return [

        float(x)

        for x in re.findall(
            r"[+-]?\d+(?:\.\d+)?",
            text
        )
    ]


def normalize_question(text):

    text = text.lower()

    # unicode minus
    text = text.replace("−", "-")

    return text


# ======================================================
# FEATURE DETECTION
# ======================================================

def detect_feature(text):

    text = normalize_question(text)

    for alias, canonical in FEATURE_ALIASES.items():

        if alias in text:
            return canonical

    # --------------------------------------------------
    # fallback by unit
    # --------------------------------------------------

    if "°c" in text:
        return "temperature"

    return None


# ======================================================
# VALUE SIGN INTERPRETATION
# ======================================================

def apply_directional_sign(
    value,
    text
):

    text = normalize_question(text)

    negative_markers = [

        "decrease",
        "decreased",
        "decreasing",
        "reduced",
        "reduction",
        "loss",
        "lower",
        "-"
    ]

    for marker in negative_markers:

        if marker in text:
            return -abs(value)

    return value


# ======================================================
# SPLIT HELPERS
# ======================================================

def split_vs(q):

    parts = re.split(
        r"\bvs\b|\bversus\b|\bor\b",
        q
    )

    if len(parts) >= 2:
        return parts[0], parts[1]

    return None, None


def split_first_second(q):

    pattern = (
        r"(?:first[^:,.]*[:,-]?)(.*?)"
        r"(?:second[^:,.]*[:,-]?)(.*)"
    )

    match = re.search(pattern, q)

    if match:
        return match.group(1), match.group(2)

    return None, None


def split_one_and_one(q):

    pattern = (
        r"one\s+with\s+(.*?)"
        r"\s+and\s+one\s+with\s+(.*)"
    )

    match = re.search(pattern, q)

    if match:
        return match.group(1), match.group(2)

    return None, None


# ======================================================
# GENERIC SCENARIO PARSER
# ======================================================

def parse_simple(text):

    text = normalize_question(text)

    result = {}

    feature = detect_feature(text)

    if not feature:
        return None

    numbers = extract_numbers(text)

    if not numbers:
        return None

    value = numbers[0]

    value = apply_directional_sign(
        value,
        text
    )

    result[feature] = value

    return result


# ======================================================
# PARSE FROM → TO
# ======================================================

def parse_from_to(q):

    match = re.search(

        r"from\s+([+-]?\d+\.?\d*)"
        r"\s*(?:°c|%)?\s+to\s+"
        r"([+-]?\d+\.?\d*)",

        q
    )

    if not match:
        return None, None

    v1 = float(match.group(1))
    v2 = float(match.group(2))

    feature = detect_feature(q)

    if not feature:
        return None, None

    scen_A = {
        feature: v1
    }

    scen_B = {
        feature: v2
    }

    return scen_A, scen_B


# ======================================================
# MAIN
# ======================================================

def parse_comparison_scenarios(
    question: str
):

    q = normalize_question(question)

    print("[PARSER v8 DEBUG]")

    # --------------------------------------------------
    # 1. FROM → TO
    # --------------------------------------------------

    scen_A, scen_B = parse_from_to(q)

    if scen_A and scen_B:

        print(
            "Detected FROM→TO pattern"
        )

        print(
            "Parsed A:",
            scen_A
        )

        print(
            "Parsed B:",
            scen_B
        )

        return scen_A, scen_B

    # --------------------------------------------------
    # 2. FIRST / SECOND
    # --------------------------------------------------

    a, b = split_first_second(q)

    if a and b:

        scen_A = parse_simple(a)
        scen_B = parse_simple(b)

        print(
            "Detected FIRST/SECOND"
        )

        print(
            "Parsed A:",
            scen_A
        )

        print(
            "Parsed B:",
            scen_B
        )

        if scen_A and scen_B:
            return scen_A, scen_B

    # --------------------------------------------------
    # 3. ONE / AND ONE
    # --------------------------------------------------

    a, b = split_one_and_one(q)

    if a and b:

        scen_A = parse_simple(a)
        scen_B = parse_simple(b)

        print(
            "Detected ONE/AND"
        )

        print(
            "Parsed A:",
            scen_A
        )

        print(
            "Parsed B:",
            scen_B
        )

        if scen_A and scen_B:
            return scen_A, scen_B

    # --------------------------------------------------
    # 4. VS / OR
    # --------------------------------------------------

    a, b = split_vs(q)

    if a and b:

        scen_A = parse_simple(a)
        scen_B = parse_simple(b)

        print(
            "Detected VS/OR"
        )

        print(
            "Parsed A:",
            scen_A
        )

        print(
            "Parsed B:",
            scen_B
        )

        if scen_A and scen_B:
            return scen_A, scen_B

    # --------------------------------------------------
    # FAIL
    # --------------------------------------------------

    print("A text:", a)
    print("B text:", b)

    return None, None