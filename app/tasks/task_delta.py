# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Delta Task — v29 (final with implicit range support)
"""

import re
import pandas as pd
import numpy as np

from knowledge.rag_delta import generate_delta_explanation
from utils.feature_mapping import normalize_feature_name
from utils.model_input_builder import build_scenario, compute_baseline
from output_formatter import format_result, dumps_llm_context


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


GRASSLAND_FEATURE = "Presence of grassland"
GRASSLAND_RANDOM_SEED = 42


def simulate_grassland_loss(model, dataset, loss_percent, seed=GRASSLAND_RANDOM_SEED):
    """
    Spatial approximation for a percentage loss of grassland presence.

    A negative percentage change is interpreted as removing that proportion
    of cells currently coded Presence of grassland = 1. All other cell
    attributes are held fixed. Predictions are evaluated over the full grid.
    """
    from versions.v6_1_emulator import (
        NUM_FEATURES,
        CAT_FEATURES,
        preprocess_semantic_features,
    )

    loss_percent = float(loss_percent)
    if not np.isfinite(loss_percent) or not 0 <= loss_percent <= 100:
        raise ValueError("Grassland loss must be between 0 and 100 percent.")

    feature_columns = NUM_FEATURES + CAT_FEATURES
    missing = [column for column in feature_columns if column not in dataset.columns]
    if missing:
        raise ValueError(
            "The dataset is missing model features required for the spatial "
            f"grassland simulation: {missing}"
        )

    raw = dataset.loc[:, feature_columns].copy()
    grassland_values = pd.to_numeric(
        raw[GRASSLAND_FEATURE], errors="coerce"
    )

    valid_values = grassland_values.isin([0, 1])
    if not bool(valid_values.all()):
        invalid_count = int((~valid_values).sum())
        raise ValueError(
            f"{invalid_count} cells have missing or non-binary "
            f"'{GRASSLAND_FEATURE}' values; spatial simulation stopped."
        )

    raw[GRASSLAND_FEATURE] = grassland_values.astype(int)
    positive_positions = np.flatnonzero(
        grassland_values.to_numpy() == 1
    )
    total_cells = len(raw)
    initial_grassland_cells = len(positive_positions)

    if total_cells == 0 or initial_grassland_cells == 0:
        raise ValueError(
            "The dataset is empty or contains no cells with grassland presence."
        )

    cells_to_remove = int(
        round(initial_grassland_cells * loss_percent / 100.0)
    )

    # One reproducible random selection of the cells to be transformed.
    rng = np.random.default_rng(seed)
    selected_positions = rng.permutation(positive_positions)[:cells_to_remove]

    baseline_features = preprocess_semantic_features(raw)
    baseline_predictions = np.asarray(
        model.predict(baseline_features), dtype=float
    )

    scenario_raw = raw.copy()
    if cells_to_remove:
        grassland_column_position = scenario_raw.columns.get_loc(GRASSLAND_FEATURE)
        scenario_raw.iloc[selected_positions, grassland_column_position] = 0

    scenario_features = preprocess_semantic_features(scenario_raw)
    scenario_predictions = np.asarray(
        model.predict(scenario_features), dtype=float
    )

    if len(baseline_predictions) != total_cells or len(scenario_predictions) != total_cells:
        raise ValueError(
            "The emulator did not return one prediction for every dataset cell."
        )
    if not np.isfinite(baseline_predictions).all() or not np.isfinite(scenario_predictions).all():
        raise ValueError("The emulator returned non-finite risk predictions.")

    # Use the same Low/Medium/High thresholds already used by Delta.
    def count_risk_classes(predictions):
        low = int(np.sum(predictions < 0.33))
        medium = int(np.sum((predictions >= 0.33) & (predictions < 0.66)))
        high = int(np.sum(predictions >= 0.66))
        return {
            "low": low,
            "medium": medium,
            "high": high,
            "at_risk": medium + high,
        }

    baseline_classes = count_risk_classes(baseline_predictions)
    scenario_classes = count_risk_classes(scenario_predictions)

    changed_predictions = (
        np.abs(scenario_predictions - baseline_predictions) > 1e-12
    )
    remaining_grassland_cells = initial_grassland_cells - cells_to_remove

    baseline_mean = float(np.mean(baseline_predictions))
    scenario_mean = float(np.mean(scenario_predictions))
    baseline_at_risk_percent = (
        100.0 * baseline_classes["at_risk"] / total_cells
    )
    scenario_at_risk_percent = (
        100.0 * scenario_classes["at_risk"] / total_cells
    )

    return {
        "score_from": baseline_mean,
        "score_to": scenario_mean,
        "delta": scenario_mean - baseline_mean,
        "total_cells": total_cells,
        "grassland_cells_before": initial_grassland_cells,
        "grassland_cells_removed": cells_to_remove,
        "grassland_cells_remaining": remaining_grassland_cells,
        "grassland_presence_percent_before": (
            100.0 * initial_grassland_cells / total_cells
        ),
        "grassland_presence_percent_after": (
            100.0 * remaining_grassland_cells / total_cells
        ),
        "cells_with_changed_prediction": int(changed_predictions.sum()),
        "percent_cells_with_changed_prediction": (
            100.0 * float(changed_predictions.mean())
        ),
        "baseline_low_risk_cells": baseline_classes["low"],
        "baseline_medium_risk_cells": baseline_classes["medium"],
        "baseline_high_risk_cells": baseline_classes["high"],
        "baseline_at_risk_cells": baseline_classes["at_risk"],
        "baseline_at_risk_percent": baseline_at_risk_percent,
        "scenario_low_risk_cells": scenario_classes["low"],
        "scenario_medium_risk_cells": scenario_classes["medium"],
        "scenario_high_risk_cells": scenario_classes["high"],
        "scenario_at_risk_cells": scenario_classes["at_risk"],
        "scenario_at_risk_percent": scenario_at_risk_percent,
        "delta_at_risk_cells": (
            scenario_classes["at_risk"] - baseline_classes["at_risk"]
        ),
        "delta_at_risk_percentage_points": (
            scenario_at_risk_percent - baseline_at_risk_percent
        ),
        "grassland_loss_percent": loss_percent,
        "random_seed": int(seed),
    }


def build_grassland_loss_result(question, feature, loss_percent, stats):
    """Create a transparent, non-causal explanation for the spatial approximation."""
    score_from = stats["score_from"]
    score_to = stats["score_to"]
    delta = stats["delta"]

    risk_from = risk_level_from_score(score_from)
    risk_to = risk_level_from_score(score_to)

    remaining_percent = stats["grassland_presence_percent_after"]
    at_risk_delta = stats["delta_at_risk_cells"]
    if at_risk_delta > 0:
        area_change_text = f"an increase of {at_risk_delta:,} cells"
    elif at_risk_delta < 0:
        area_change_text = f"a decrease of {abs(at_risk_delta):,} cells"
    else:
        area_change_text = "no change in the number of cells"

    interpretation = (
        "**Simulation setup**\n"
        f"The requested {loss_percent:g}% grassland decrease was operationalized "
        "as converting the same proportion of cells currently coded "
        f"`{GRASSLAND_FEATURE} = 1` to 0. The selection was random and "
        f"reproducible (seed {stats['random_seed']}); all other cell attributes "
        "were kept unchanged.\n\n"
        "**Spatial model estimate**\n"
        f"The simulation covers {stats['total_cells']:,} cells. Grassland "
        f"presence changes from {stats['grassland_cells_before']:,} cells "
        f"({stats['grassland_presence_percent_before']:.2f}% of the grid) to "
        f"{stats['grassland_cells_remaining']:,} cells "
        f"({remaining_percent:.2f}%). The mean predicted risk score changes "
        f"from {score_from:.3f} to {score_to:.3f} "
        f"({delta:+.3f}).\n\n"
        "**Cells classified as at risk**\n"
        "Using the task's existing score thresholds (Medium or High Risk, "
        "score >= 0.33), the number of cells classified as at risk changes "
        f"from {stats['baseline_at_risk_cells']:,} "
        f"({stats['baseline_at_risk_percent']:.2f}%) to "
        f"{stats['scenario_at_risk_cells']:,} "
        f"({stats['scenario_at_risk_percent']:.2f}%), "
        f"{area_change_text} "
        f"({stats['delta_at_risk_percentage_points']:+.2f} percentage points). "
        f"Predictions change in {stats['cells_with_changed_prediction']:,} "
        f"cells ({stats['percent_cells_with_changed_prediction']:.2f}%).\n\n"
        "**Interpretation limits**\n"
        "This is a model-based spatial approximation, not a spatially targeted "
        "land-cover forecast. The random selection does not represent where "
        "grassland loss would occur in reality. The predicted changes reflect "
        "associations learned by the surrogate model and must not be interpreted "
        "as evidence that losing grassland improves ecological conditions."
    )

    return {
        "summary": "Grassland loss scenario (spatial simulation)",
        "data": {
            **stats,
            "score_from": round(score_from, 3),
            "score_to": round(score_to, 3),
            "delta": round(delta, 3),
            "risk_from": risk_from,
            "risk_to": risk_to,
        },
        "drivers": [(feature, 1, 0)],
        "interpretation": interpretation,
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

        # Grassland presence has a dedicated spatial approximation:
        # a negative percentage change removes that proportion of cells
        # currently coded 1. Other binary modifications remain state targets.
        if feature in binary_features:

            if (
                feature == GRASSLAND_FEATURE
                and delta_type == "percentage_change"
            ):
                if not -100 <= delta_value <= 0:
                    return (
                        "Grassland percentage changes are supported only "
                        "as a loss between 0% and 100% of cells currently "
                        "coded as present."
                    )
                return None

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

    # Spatial approximation for explicit percentage changes in grassland cover.
    if "grassland" in q and any(
        term in q
        for term in ("cover", "coverage", "copertura", "percentage", "percent")
    ):
        match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", q)
        if match:
            magnitude = float(match.group(1).replace(",", "."))
            if any(w in q for w in ("decrease", "decreases", "reduce", "reduces", "drop", "loss", "decline")):
                direction = -1
            elif any(w in q for w in ("increase", "increases", "rise", "gain")):
                direction = 1
            else:
                return None

            return {
                "feature": normalize_feature_name("grassland"),
                "mode": "baseline_delta",
                "delta": direction * magnitude,
                "delta_type": "percentage_change",
            }

        # Do not fall through to the generic 10% fallback for grassland cover.
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
    model,
    dataset
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
                        "Grassland percentage coverage is not supported "
                        "by the current dataset. Grassland is represented "
                        "only as a binary presence/absence variable (0/1). "
                        "Changes in percentage coverage are not yet "
                        "implemented at this stage of development. "
                        "Therefore, the requested delta task has not been executed."
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
    # Build baseline from dataset
    # --------------------------------------------------

    base = compute_baseline(dataset)

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

    # --------------------------------------------------
    # Dedicated spatial simulation for grassland loss
    # --------------------------------------------------

    delta_type = range_info.get("delta_type", "percentage_change")
    if (
        feature == GRASSLAND_FEATURE
        and range_info.get("mode") == "baseline_delta"
        and delta_type == "percentage_change"
    ):
        loss_percent = abs(float(range_info["delta"]))
        print(
            "[DEBUG] Running spatial grassland-loss approximation: "
            f"{loss_percent:g}% (seed={GRASSLAND_RANDOM_SEED})."
        )
        try:
            stats = simulate_grassland_loss(
                model=model,
                dataset=dataset,
                loss_percent=loss_percent,
                seed=GRASSLAND_RANDOM_SEED,
            )
        except Exception as exc:
            print(f"[DEBUG] Grassland spatial simulation failed: {exc}")
            return {
                "summary": "Grassland spatial simulation failed",
                "data": {},
                "drivers": [],
                "interpretation": (
                    "The requested grassland-loss simulation could not be "
                    f"completed: {exc}"
                ),
            }

        result = build_grassland_loss_result(
            question=question,
            feature=feature,
            loss_percent=loss_percent,
            stats=stats,
        )

        # Describe the modification as a percentage of the cells that
        # initially had grassland presence, not as a single-cell 1 -> 0 change.
        rag_driver = (
            "Grassland presence among initially grassland cells (%)",
            100.0,
            100.0 - loss_percent,
        )
        rag_drivers = [rag_driver]
        result["drivers"] = rag_drivers

        scenario_context = (
            f"The scenario removes {loss_percent:g}% of the cells that "
            "were initially coded Presence of grassland = 1. This is "
            "operationalized by randomly converting that proportion of "
            "those cells from 1 to 0, using the fixed random seed "
            f"{GRASSLAND_RANDOM_SEED}. The selection is reproducible but "
            "not spatially targeted. It is not a uniform reduction of "
            "grassland cover within every cell, and it does not identify "
            "where grassland loss would occur in reality."
        )

        try:
            ecological_interpretation = generate_delta_explanation(
                question,
                rag_drivers,
                delta=stats["delta"],
                features=features,
                model_results={
                    "score_from": stats["score_from"],
                    "score_to": stats["score_to"],
                    "risk_from": risk_level_from_score(stats["score_from"]),
                    "risk_to": risk_level_from_score(stats["score_to"]),
                },
                scenario_context=scenario_context,
                ecological_only=True,
            )

            if ecological_interpretation:
                result["interpretation"] = (
                    "**Ecological interpretation**\n"
                    f"{ecological_interpretation}\n\n"
                    f"{result['interpretation']}"
                )

        except Exception as exc:
            # Keep the completed spatial result if the explanatory RAG fails.
            print(f"[DEBUG] Grassland ecological RAG failed: {exc}")

        print(
            "[DEBUG] Grassland spatial simulation completed: "
            f"mean risk {stats['score_from']:.6f} -> "
            f"{stats['score_to']:.6f}; at-risk cells "
            f"{stats['baseline_at_risk_cells']} -> "
            f"{stats['scenario_at_risk_cells']}."
        )
        print("========== DELTA TASK END (GRASSLAND SPATIAL) ==========\n")
        return result

    # ----------------------------------------------
    # Build scenarios using shared Scenario Builder
    # ----------------------------------------------

    if range_info.get("mode") == "baseline_delta":

        delta_value = range_info["delta"]

        delta_type = range_info.get(
            "delta_type",
            "percentage_change"
        )

        # Map Delta modification types to Scenario Builder types.
        modification_types = {
            "absolute_delta": "absolute_delta",
            "absolute_target": "absolute_target",
            "percentage_change": "percentage_change"
        }

        builder_type = modification_types.get(delta_type)

        if builder_type is None:
            return {
                "summary": "Invalid scenario",
                "data": {},
                "drivers": [],
                "interpretation": (
                    f"Unsupported modification type: '{delta_type}'."
                )
            }

        modifications = {
            feature: {
                "type": builder_type,
                "value": delta_value
            }
        }

        df_a, df_b = build_scenario(
            modifications,
            dataset
        )

        v_from = float(df_a.iloc[0][feature])
        v_to = float(df_b.iloc[0][feature])

    else:

        v_from = range_info["from"]
        v_to = range_info["to"]

        # Build the first scenario using the explicit starting value.
        modifications_a = {
            feature: {
                "type": "absolute_target",
                "value": v_from
            }
        }

        df_a_baseline, df_a = build_scenario(
            modifications_a,
            dataset
        )

        # Build the second scenario using the explicit ending value.
        modifications_b = {
            feature: {
                "type": "absolute_target",
                "value": v_to
            }
        }

        df_b_baseline, df_b = build_scenario(
            modifications_b,
            dataset
        )

        # Both scenarios must share exactly the same baseline.
        if not df_a_baseline.equals(df_b_baseline):
            raise ValueError(
                "Inconsistent baseline detected between Delta scenarios."
            )

    # --------------------------------------------------
    # Scenario information
    # --------------------------------------------------

    print("\n[DEBUG] Shared Scenario Builder applied.")

    print(
        f"[DEBUG] Feature: {feature}"
    )

    print(
        f"[DEBUG] Range: {v_from} → {v_to}"
    )

    print("\n[DEBUG SCENARIO A]")
    print(df_a.T)

    print("\n[DEBUG SCENARIO B]")
    print(df_b.T)

    # --------------------------------------------------
    # Prediction
    # --------------------------------------------------

    score_a = float(
        model.predict(df_a)[0]
    )

    score_b = float(
        model.predict(df_b)[0]
    )

    print("\n[DEBUG] Predictions completed.")

    print(
        f"[DEBUG] Baseline risk: {score_a}"
    )

    print(
        f"[DEBUG] Scenario risk: {score_b}"
    )

    delta_raw = score_b - score_a
    delta = round(delta_raw, 3)

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
    summary = "Change in ecosystem risk (range analysis)"

    formatter_input = {
        "summary": summary,
        "data": {
            "score_from": score_a,
            "score_to": score_b,
            "delta": delta_raw,
            "risk_from": risk_from,
            "risk_to": risk_to,
        },
        "drivers": drivers,
    }

    formatted_llm_context = ""

    try:
        from output_formatter import format_result, dumps_llm_context

        formatted_result = format_result("delta", formatter_input)
        formatted_llm_context = dumps_llm_context(formatted_result)

        print(
            "[DELTA FORMATTER] Applied before explanation generation "
            f"(version={formatted_result.get('formatter_version')})."
        )
        print(
            "[DELTA FORMATTER] Canonical values:",
            formatted_result.get("display_values_by_path", {}),
        )

    except Exception as exc:
        print(
            "[DELTA FORMATTER] WARNING: formatter bypassed; "
            "legacy explanation path will be used. "
            f"Reason: {exc}"
        )

    question_for_llm = question

    if formatted_llm_context:
        question_for_llm = (
            f"{question}\n\n"
            "============================================================\n"
            "DIGITAL TWIN FORMATTED RESULTS — SYSTEM CONTEXT\n"
            "The JSON below is generated by output_formatter, not part "
            "of the user's original question. Use canonical_formatted_values "
            "when reporting numeric values; preserve the sign of the delta "
            "and distinguish the absolute scores from their difference.\n"
            "============================================================\n"
            f"{formatted_llm_context}\n"
            "============================================================"
        )
    interpretation = generate_delta_explanation(
            question_for_llm,
            drivers,
            delta_raw,
            features=features,
            model_results={
                "score_from": score_a,
                "score_to": score_b,
                "risk_from": risk_from,
                "risk_to": risk_to,
            },
        )

    print(
        "========== DELTA TASK END ==========\n"
    )

    return {

        "summary":
            summary,

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