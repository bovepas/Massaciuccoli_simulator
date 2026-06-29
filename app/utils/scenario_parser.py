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

from utils.feature_mapping import (
    normalize_feature_name
)

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
        r"(?:a\s+scenario\s+with|one\s+with)\s+(.*?)"
        r"\s+and\s+one\s+with\s+(.*)"
    )

    match = re.search(pattern, q)

    if match:

        print("[DEBUG split_one_and_one MATCH]")
        print("A =", match.group(1))
        print("B =", match.group(2))

        return match.group(1), match.group(2)

    print("[DEBUG split_one_and_one NO MATCH]")
    print(q)

    return None, None


# ======================================================
# GENERIC SCENARIO PARSER
# ======================================================

def scenario_to_legacy_dict(
    modifications,
    feature_stats=None
):

    print(
        "[DEBUG] scenario_to_legacy_dict:",
        modifications
    )

    result = {}

    for mod in modifications:

        print(
            "[DEBUG] Processing mod:",
            mod
        )

        # ------------------------------
        # Numeric / percentage modifications
        # ------------------------------

        if mod.get("type") in [

            "numeric",

            "percentage_change"

        ]:

            result[
                mod["variable"]
            ] = mod

        # ------------------------------
        # Qualitative modifications
        # ------------------------------

        elif "direction" in mod:

            if feature_stats is None:

                continue

            result[
                mod["variable"]
            ] = {

                "type": "qualitative",

                "value": qualitative_to_delta(

                    variable=mod["variable"],

                    direction=mod["direction"],

                    magnitude=mod.get(
                        "magnitude",
                        "default"
                    ),

                    feature_stats=feature_stats
                )
            }

    print(
        "[DEBUG] scenario_to_legacy_dict result:",
        result
    )

    return result

def qualitative_to_delta(
    variable,
    direction,
    magnitude,
    feature_stats
):

    MAGNITUDE_MULTIPLIER = {

        "slight": 0.5,

        "default": 1.0,

        "significant": 2.0,

        "extreme": 3.0
    }

    SPECIAL_DELTAS = {

        "temperature": 1.0,

        "precipitation": 10.0,

        "evapotranspiration": 10.0
    }

    # ----------------------------------
    # NORMALIZE FEATURE NAME
    # ----------------------------------

    variable = variable.replace(
        "_",
        " "
    )

    dataset_feature = normalize_feature_name(
        variable
    )

    if not dataset_feature:

        raise ValueError(
            f"Unknown feature: {variable}"
        )

    # ----------------------------------
    # BASE DELTA
    # ----------------------------------

    if variable in SPECIAL_DELTAS:

        delta = (
            SPECIAL_DELTAS[variable]
            *
            MAGNITUDE_MULTIPLIER.get(
                magnitude,
                1.0
            )
        )

    else:

        delta = (
            feature_stats[
                dataset_feature
            ]["std"]
            *
            MAGNITUDE_MULTIPLIER.get(
                magnitude,
                1.0
            )
        )

    # ----------------------------------
    # DIRECTION
    # ----------------------------------

    if direction == "decrease":

        delta = -delta

    return delta


def parse_numeric_modifications(text):

    modifications = []

    feature = detect_feature(text)

    if not feature:
        return modifications

    numbers = extract_numbers(text)

    if not numbers:
        return modifications

    value = apply_directional_sign(
        numbers[0],
        text
    )

    modification_type = "numeric"

    if "%" in text:

        modification_type = (
            "percentage_change"
        )

    print("\n[DEBUG NUMERIC PARSER]")
    print("text:", text)
    print("feature:", feature)
    print("numbers:", numbers)
    print("value:", value)
    print("type:", modification_type)

    modifications.append({

        "variable": feature,

        "type": modification_type,

        "value": value
    })

    return modifications




def parse_scenario(text):

    text = normalize_question(text)

    modifications = []

    modifications.extend(
        parse_numeric_modifications(text)
    )

    for alias, canonical in FEATURE_ALIASES.items():

        if alias not in text:
            continue

        direction = None

        if any(x in text for x in [
            "increase",
            "increased",
            "increasing",
            "higher",
            "rise",
            "rising"
        ]):

            direction = "increase"

        elif any(x in text for x in [
            "decrease",
            "decreased",
            "decreasing",
            "reduced",
            "reduction",
            "lower",
            "loss",
            "decline"
        ]):

            direction = "decrease"

        if not direction:
            continue

        magnitude = "default"

        if any(x in text for x in [
            "slight",
            "slightly",
            "small"
        ]):

            magnitude = "slight"

        elif any(x in text for x in [
            "significant",
            "strong",
            "substantial"
        ]):

            magnitude = "significant"

        elif any(x in text for x in [
            "extreme",
            "dramatic",
            "very large"
        ]):

            magnitude = "extreme"

        # ----------------------------------
        # Skip qualitative modification
        # if numeric modification already
        # exists for the same variable
        # ----------------------------------

        # ----------------------------------
        # Skip qualitative modification
        # if a numeric-like modification
        # already exists for the same variable
        # ----------------------------------

        if any(

            m["variable"] == canonical

            and m.get("type") in [

                "numeric",

                "percentage_change"

            ]

            for m in modifications

        ):
            continue

        modifications.append({

            "variable": canonical,

            "direction": direction,

            "magnitude": magnitude
        })

    return modifications
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
def split_scenario_and_scenario(q):

    pattern = (
        r"scenario\s+with\s+(.*?)"
        r"\s+and\s+(?:a\s+)?scenario\s+with\s+(.*)"
    )

    match = re.search(pattern, q)

    if match:
        return match.group(1), match.group(2)

    return None, None


def parse_comparison_scenarios(
    question: str,
    feature_stats=None
):

    q = normalize_question(question)

    print("[PARSER v8 DEBUG]")

    a = None
    b = None

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

        print("\n[DEBUG] Scenario A text:")
        print(a)

        print("\n[DEBUG] Scenario B text:")
        print(b)

        mods_A = parse_scenario(a)
        mods_B = parse_scenario(b)

        print("\n[DEBUG] Scenario A modifications:")
        print(mods_A)

        print("\n[DEBUG] Scenario B modifications:")
        print(mods_B)

        scen_A = scenario_to_legacy_dict(
            mods_A,
            feature_stats
        )

        scen_B = scenario_to_legacy_dict(
            mods_B,
            feature_stats
        )

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

        print("\n[DEBUG] Scenario A text:")
        print(a)

        print("\n[DEBUG] Scenario B text:")
        print(b)

        mods_A = parse_scenario(a)
        mods_B = parse_scenario(b)

        print("\n[DEBUG] Scenario A modifications:")
        print(mods_A)

        print("\n[DEBUG] Scenario B modifications:")
        print(mods_B)

        scen_A = scenario_to_legacy_dict(
            mods_A,
            feature_stats
        )

        scen_B = scenario_to_legacy_dict(
            mods_B,
            feature_stats
        )

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
    # 4. SCENARIO / SCENARIO
    # --------------------------------------------------

    a, b = split_scenario_and_scenario(q)

    if a and b:

        print("\n[DEBUG] Scenario A text:")
        print(a)

        print("\n[DEBUG] Scenario B text:")
        print(b)

        mods_A = parse_scenario(a)
        mods_B = parse_scenario(b)

        print("\n[DEBUG] Scenario A modifications:")
        print(mods_A)

        print("\n[DEBUG] Scenario B modifications:")
        print(mods_B)

        scen_A = scenario_to_legacy_dict(
            mods_A,
            feature_stats
        )

        scen_B = scenario_to_legacy_dict(
            mods_B,
            feature_stats
        )

        print(
            "Detected SCENARIO/SCENARIO"
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
    # 5. VS / OR
    # --------------------------------------------------

    a, b = split_vs(q)

    if a and b:

        print("\n[DEBUG] Scenario A text:")
        print(a)

        print("\n[DEBUG] Scenario B text:")
        print(b)

        mods_A = parse_scenario(a)
        mods_B = parse_scenario(b)

        print("\n[DEBUG] Scenario A modifications:")
        print(mods_A)

        print("\n[DEBUG] Scenario B modifications:")
        print(mods_B)

        scen_A = scenario_to_legacy_dict(
            mods_A,
            feature_stats
        )

        scen_B = scenario_to_legacy_dict(
            mods_B,
            feature_stats
        )

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
    # 6. BASELINE → SCENARIO
    # --------------------------------------------------

    m = re.search(
        r"(?:current ecosystem|current conditions|baseline).*?"
        r"scenario\s+"
        r"(?:where|with|combining|including|that\s+combines)?"
        r"\s*(.*)",
        q,
        flags=re.IGNORECASE | re.DOTALL
    )

    if m:

        print("Detected BASELINE/SCENARIO")

        scenario_text = m.group(1).strip()

        print("\n[DEBUG] Scenario B text:")
        print(scenario_text)

        mods_B = parse_scenario(
            scenario_text
        )

        print("\n[DEBUG] Scenario B modifications:")
        print(mods_B)

        scen_A = {}

        scen_B = scenario_to_legacy_dict(
            mods_B,
            feature_stats
        )

        print("Parsed A:", scen_A)
        print("Parsed B:", scen_B)

        if scen_B:

            return scen_A, scen_B

    # --------------------------------------------------
    # FAIL
    # --------------------------------------------------

    print("A text:", a)
    print("B text:", b)

    return None, None