# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Delta Task — v29 (final with implicit range support)
"""

import pandas as pd

from knowledge.rag_delta import generate_delta_explanation
from utils.feature_mapping import normalize_feature_name


# ======================================================
# BASE SCENARIO
# ======================================================

def get_base_scenario():
    return {
        'Density change in land imperviousness': 0,
        'Density of tree cover': 50,
        'Index of total productivity by plant phenology': 200,
        'Change in average temperature compared to a recent past': 0,
        'Relative change in the potential evapotranspiration compared to a recent past': 0,
        'Cumulative change in precipitation compared to a recent past': 0,
        'Number of species potentially living in the cell': 200,
        'Presence of grassland': 1,
        'Land use and cover': 'rural_natural',
        'Change in land use and cover in the past decade': '1',
        'Change in grassland presence in the past decade': '0',
        'Change in tree cover density in the past decade': '0'
    }

def validate_delta_scenario(feature, range_info, base):
    """
    Validate a delta scenario before modifying the baseline.

    Returns:
        None if the scenario is valid.
        A descriptive error string otherwise.
    """

    import math
    from numbers import Real

    # --------------------------------------------------
    # 1. Feature must exist in the baseline
    # --------------------------------------------------

    if feature not in base:
        return (
            f"Feature '{feature}' is not available "
            "in the baseline scenario."
        )

    # --------------------------------------------------
    # 2. Identify categorical and binary features
    # --------------------------------------------------

    binary_features = {
        "Presence of grassland",
    }

    categorical_features = {
        "Land use and cover",
        "Change in land use and cover in the past decade",
        "Change in grassland presence in the past decade",
        "Change in grassland presence in the past decade",
        "Change in tree cover density in the past decade",
    }

    # --------------------------------------------------
    # 3. Validate modification mode
    # --------------------------------------------------

    mode = range_info.get("mode")

    if mode == "baseline_delta":

        delta_value = range_info.get("delta")
        delta_type = range_info.get(
            "delta_type",
            "percentage_change"
        )

        if (
            isinstance(delta_value, bool)
            or not isinstance(delta_value, Real)
            or not math.isfinite(delta_value)
        ):
            return "The requested modification must be numeric."

        # Binary variables: only explicit state targets
        # are supported. Percentage changes are invalid.
        if feature in binary_features:

            if delta_type != "absolute_target":
                return (
                    f"Feature '{feature}' is binary. "
                    "Percentage changes and numeric deltas "
                    "are not supported. Specify a target "
                    "state of 0 or 1."
                )

            if delta_value not in (0, 1):
                return (
                    f"Feature '{feature}' accepts only "
                    "the values 0 or 1."
                )

        # Categorical variables: do not apply arithmetic
        # until the valid category codes are defined.
        if feature in categorical_features:
            return (
                f"Feature '{feature}' is categorical. "
                "Numeric deltas and percentage changes "
                "are not supported until valid category "
                "transitions are defined."
            )

        # Absolute temperature changes must use degrees C.
        if (
            feature
            == "Change in average temperature compared to a recent past"
            and delta_type != "absolute_delta"
        ):
            return (
                "Temperature modifications must use an "
                "absolute change expressed in degrees Celsius."
            )

        # Validate the resulting value for bounded features.
        baseline_value = base[feature]

        if (
            isinstance(baseline_value, Real)
            and not isinstance(baseline_value, bool)
        ):

            if delta_type == "absolute_delta":
                resulting_value = baseline_value + delta_value

            elif delta_type == "absolute_target":
                resulting_value = delta_value

            elif delta_type == "percentage_change":

                additive_change_features = {
                    "Relative change in the potential evapotranspiration compared to a recent past",
                    "Cumulative change in precipitation compared to a recent past",
                }

                if feature in additive_change_features:
                    resulting_value = baseline_value + delta_value
                else:
                    resulting_value = (
                        baseline_value
                        * (1 + delta_value / 100)
                    )

            else:
                return (
                    f"Unsupported delta type '{delta_type}'."
                )

            if not math.isfinite(resulting_value):
                return "The resulting value is not finite."

            if feature in {
                "Density of tree cover",
                "Density change in land imperviousness",
            } and not 0 <= resulting_value <= 100:
                return (
                    f"The resulting value for '{feature}' "
                    "must be between 0 and 100."
                )

            if feature in {
                "Index of total productivity by plant phenology",
                "Number of species potentially living in the cell",
            } and resulting_value < 0:
                return (
                    f"The resulting value for '{feature}' "
                    "cannot be negative."
                )

        return None

    # --------------------------------------------------
    # 4. Validate explicit ranges
    # --------------------------------------------------

    if mode is None:

        if "from" not in range_info or "to" not in range_info:
            return (
                "The scenario must contain either a baseline "
                "delta or an explicit from/to range."
            )

        v_from = range_info["from"]
        v_to = range_info["to"]

        if feature in categorical_features:
            return (
                f"Feature '{feature}' is categorical. "
                "Numeric ranges are not supported until "
                "valid category transitions are defined."
            )

        if feature in binary_features:
            if v_from not in (0, 1) or v_to not in (0, 1):
                return (
                    f"Feature '{feature}' accepts only "
                    "the values 0 or 1."
                )

        for value in (v_from, v_to):
            if (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
            ):
                return (
                    "Explicit ranges must contain finite "
                    "numeric values for this feature."
                )

        if feature in {
            "Density of tree cover",
            "Density change in land imperviousness",
        }:
            if any(not 0 <= value <= 100 for value in (v_from, v_to)):
                return (
                    f"Values for '{feature}' must be "
                    "between 0 and 100."
                )

        if feature in {
            "Index of total productivity by plant phenology",
            "Number of species potentially living in the cell",
        }:
            if any(value < 0 for value in (v_from, v_to)):
                return (
                    f"Values for '{feature}' cannot be negative."
                )

        return None

    return f"Unsupported scenario mode '{mode}'."

# ======================================================
# RISK LEVEL
# ======================================================

def risk_level_from_score(score: float) -> str:

    if score < 0.33:
        return "Low Risk"
    elif score < 0.66:
        return "Medium Risk"
    else:
        return "High Risk"


# ======================================================
# 🔥 GENERIC FALLBACK (IMPLICIT DELTA)
# ======================================================


def infer_simple_range(question):

    q = question.lower()

    # Grassland cover is not a percentage-based feature
    # available in the dataset.
    if "grassland" in q and any(
        term in q
        for term in (
            "cover",
            "coverage",
            "density",
            "percentage",
            "percent",
            "copertura",
            "percentuale",
            "densità",
        )
    ):
        print(
            "[DEBUG] Grassland cover requested, "
            "but no percentage-coverage feature exists."
        )
        return None

    keywords = [
        "temperature",
        "precipitation",
        "evapotranspiration",
        "biodiversity",
        "species",
        "tree cover",
        "impervious",
        "productivity",
        "grassland",
        "land use"
    ]

    detected = None

    for k in keywords:
        if k in q:
            detected = k
            break

    if not detected:
        return None

    feature = normalize_feature_name(detected)

    if not feature:
        return None

    # Direction
    if any(w in q for w in ["decrease", "reduce", "drop"]):
        direction = -1
    elif any(w in q for w in ["increase", "rise"]):
        direction = 1
    else:
        return None

    # Magnitude (safe generic)
    magnitude = 10

    if "temperature" in detected:
        magnitude = 2

    return {
        "feature": feature,
        "from": 0,
        "to": direction * magnitude
    }



# ======================================================
# 🔥 FEATURE RECOVERY
# ======================================================


def recover_feature_from_question(question):

    q = question.lower()

    # Grassland cover is not a percentage-based feature
    # available in the dataset.
    if "grassland" in q and any(
        term in q
        for term in (
            "cover",
            "coverage",
            "density",
            "percentage",
            "percent",
            "copertura",
            "percentuale",
            "densità",
        )
    ):
        print(
            "[DEBUG] Refusing grassland feature recovery: "
            "requested coverage is not available."
        )
        return None

    if "tree cover" in q:
        return normalize_feature_name("tree_cover")

    if "biodiversity" in q or "species" in q:
        return normalize_feature_name("biodiversity")

    if "evapotranspiration" in q:
        return normalize_feature_name("evapotranspiration")

    if "temperature" in q:
        return normalize_feature_name("temperature")

    if "precipitation" in q:
        return normalize_feature_name("precipitation")

    if "grassland" in q:
        return normalize_feature_name("grassland")

    return None


# ======================================================
# MAIN
# ======================================================

def handle_delta(
    question,
    range_info,
    features,
    parsed,
    model
):

    print("\n========== DELTA TASK START ==========")

    # --------------------------------------------------
    # Build implicit delta from parsed features
    # --------------------------------------------------

    if not range_info and features:

        print(
            "[DEBUG] Building delta from parsed modifications"
        )

        mods = parsed.get(
            "modifications",
            []
        )

        if mods:

            mod = mods[0]

            feature = mod["variable"]

            value = mod["value"]

            print(
                "[DEBUG] Modification:",
                mod
            )

            print(
                "[DEBUG] Delta type:",
                mod.get("type")
            )

            range_info = {

                "feature": feature,

                "mode": "baseline_delta",

                "delta": value,

                "delta_type": mod.get("type")
            }


    # --------------------------------------------------
    # Legacy fallback
    # --------------------------------------------------

    if not range_info:

        print(
            "[DEBUG] No range detected → using implicit range"
        )

        range_info = infer_simple_range(
            question
        )

        if not range_info:

            question_lower = question.lower()

            grassland_coverage_terms = (
                "cover",
                "coverage",
                "density",
                "percentage",
                "percent",
                "copertura",
                "percentuale",
                "densità",
            )

            asks_grassland_coverage = (
                "grassland" in question_lower
                and any(
                    term in question_lower
                    for term in grassland_coverage_terms
                )
            )

            if asks_grassland_coverage:
                print(
                    "[DEBUG] Grassland percentage coverage "
                    "requested, but the feature is unsupported."
                )

                return {
                    "summary": "Unsupported environmental variable",
                    "data": {},
                    "drivers": [],
                    "interpretation": (
                        "The dataset represents grassland through "
                        "binary presence (0/1), not percentage coverage. "
                        "The requested scenario cannot be simulated "
                        "with the available variables."
                    ),
                }

            return {
                "summary": "Range not recognized",
                "data": {},
                "drivers": [],
                "interpretation": "Could not parse range"
            }


    # --------------------------------------------------
    # Feature recovery
    # --------------------------------------------------

    feature = range_info.get(
        "feature"
    )

    if feature is None:

        print(
            "[DEBUG] Recovering feature from question..."
        )

        feature = recover_feature_from_question(
            question
        )

    if feature is None:

        return {

            "summary":
                "Feature not recognized",

            "data":
                {},

            "drivers":
                [],

            "interpretation":
                "Could not identify the environmental variable."
        }
    
    # --------------------------------------------------
    # Validate grassland cover requests
    # --------------------------------------------------

    q = question.lower()

    if "grassland" in q and any(
        term in q
        for term in (
            "cover",
            "coverage",
            "density",
            "percentage",
            "percent",
            "copertura",
            "percentuale",
            "densità",
        )
    ):
        print(
            "[DEBUG] Unsupported request: grassland "
            "percentage coverage is not available."
        )

        return {
            "summary": "Unsupported environmental variable",
            "data": {},
            "drivers": [],
            "interpretation": (
                "The dataset contains binary grassland presence, "
                "not percentage grassland coverage. "
                "The requested scenario cannot be simulated."
            )
        }

    # --------------------------------------------------
    # Build scenarios
    # --------------------------------------------------

    base = get_base_scenario()
    
    # --------------------------------------------------
    # Validate scenario before building modifications
    # --------------------------------------------------

    validation_error = validate_delta_scenario(
        feature,
        range_info,
        base
    )

    if validation_error:
        print(
            "[DEBUG] Invalid scenario:",
            validation_error
        )

        return {
            "summary": "Invalid scenario",
            "data": {},
            "drivers": [],
            "interpretation": validation_error
        }

    # ----------------------------------------------
    # Case 1:
    # baseline → modified baseline
    # ----------------------------------------------

    if range_info.get(
        "mode"
    ) == "baseline_delta":

        delta_value = range_info[
            "delta"
        ]

        delta_type = range_info.get(
            "delta_type",
            "percentage_change"
        )

        baseline_value = base[
            feature
        ]

        scenario_a = base.copy()
        scenario_b = base.copy()

        # ------------------------------------------
        # Absolute variation
        # Example:
        # temperature +2°C
        # ------------------------------------------

        if delta_type == "absolute_delta":

            scenario_b[
                feature
            ] = baseline_value + delta_value

        # ------------------------------------------
        # Absolute target
        # Example:
        # tree cover increases to 70%
        # ------------------------------------------

        elif delta_type == "absolute_target":

            scenario_b[
                feature
            ] = delta_value

        # ------------------------------------------
        # Percentage variation
        # Example:
        # biodiversity -30%
        # ------------------------------------------

        else:

            change_variables = {
                "Relative change in the potential evapotranspiration compared to a recent past",
                "Cumulative change in precipitation compared to a recent past"
            }

            if feature in change_variables:

                scenario_b[
                    feature
                ] = baseline_value + delta_value

            else:

                scenario_b[
                    feature
                ] = (
                    baseline_value
                    * (
                        1
                        + delta_value / 100
                    )
                )

        v_from = baseline_value

        v_to = scenario_b[
            feature
        ]

        print(

            "[DEBUG] Baseline delta:",

            baseline_value,

            "->",

            v_to
        )

    # ----------------------------------------------
    # Case 2:
    # explicit range
    # ----------------------------------------------

    else:

        v_from = range_info[
            "from"
        ]

        v_to = range_info[
            "to"
        ]

        scenario_a = base.copy()
        scenario_b = base.copy()

        scenario_a[
            feature
        ] = v_from

        scenario_b[
            feature
        ] = v_to

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    print(
        f"[DEBUG] Feature: {feature}"
    )

    print(
        f"[DEBUG] Range: {v_from} → {v_to}"
    )

    df_a = pd.DataFrame(
        [scenario_a]
    )

    df_b = pd.DataFrame(
        [scenario_b]
    )

    print("\n[DEBUG SCENARIO A]")
    print(df_a.T)

    print("\n[DEBUG SCENARIO B]")
    print(df_b.T)

    score_a = float(
        model.predict(df_a)[0]
    )

    score_b = float(
        model.predict(df_b)[0]
    )

    delta = round(
        score_b - score_a,
        3
    )

    # --------------------------------------------------
    # Output
    # --------------------------------------------------

    drivers = [

        (
            feature,
            v_from,
            v_to
        )
    ]

    risk_from = risk_level_from_score(
        score_a
    )

    risk_to = risk_level_from_score(
        score_b
    )

    interpretation = generate_delta_explanation(
        question,
        drivers,
        delta,
        features=features
    )

    print(
        "========== DELTA TASK END ==========\n"
    )

    return {

        "summary":
            "Change in ecosystem risk (range analysis)",

        "data": {

            "score_from":
                round(score_a, 3),

            "score_to":
                round(score_b, 3),

            "delta":
                delta,

            "risk_from":
                risk_from,

            "risk_to":
                risk_to
        },

        "drivers":
            drivers,

        "interpretation":
            interpretation
    }