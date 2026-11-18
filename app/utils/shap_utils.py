# -*- coding: utf-8 -*-

"""
SHAP Utilities — v2 (DELTA SHAP)

Massaciuccoli Digital Twin

✔ RandomForest-compatible
✔ sklearn Pipeline-compatible
✔ Local SHAP explanations
✔ Delta-SHAP support
✔ One-hot aggregation
✔ Stable feature names
✔ Noise filtering
✔ Safe fallbacks
"""

import shap
import pandas as pd
import numpy as np
from collections import defaultdict


# ======================================================
# CONFIG
# ======================================================

DEBUG = True


# ======================================================
# DEBUG
# ======================================================

def debug_print(*args):

    if DEBUG:
        print("[SHAP UTILS]", *args)


# ======================================================
# EXTRACT PIPELINE COMPONENTS
# ======================================================

def extract_pipeline_components(model):

    try:

        preprocessor = model.named_steps["preprocessor"]

        rf_model = model.named_steps["rf"]

        return preprocessor, rf_model

    except Exception as e:

        print("[SHAP] Pipeline extraction failed:", e)

        return None, None


# ======================================================
# GET FEATURE NAMES
# ======================================================

def get_feature_names(preprocessor):

    try:

        feature_names = preprocessor.get_feature_names_out()

        return list(feature_names)

    except Exception as e:

        print("[SHAP] Feature name extraction failed:", e)

        return []


# ======================================================
# PREPROCESS INPUT
# ======================================================

def preprocess_input(model, df_input):

    preprocessor, _ = extract_pipeline_components(model)

    if preprocessor is None:
        return None

    try:

        transformed = preprocessor.transform(df_input)

        return transformed

    except Exception as e:

        print("[SHAP] Preprocessing failed:", e)

        return None


# ======================================================
# INTERNAL SHAP
# ======================================================

def _compute_raw_shap(model, df_input):

    preprocessor, rf_model = extract_pipeline_components(model)

    if rf_model is None:
        return {}, []

    X_processed = preprocess_input(model, df_input)

    if X_processed is None:
        return {}, []

    feature_names = get_feature_names(preprocessor)

    explainer = shap.TreeExplainer(rf_model)

    shap_values = explainer.shap_values(X_processed)

    if isinstance(shap_values, list):
        shap_row = shap_values[0][0]
    else:
        shap_row = shap_values[0]

    shap_dict = {}

    for feature, value in zip(feature_names, shap_row):

        try:
            shap_dict[feature] = float(value)
        except Exception:
            continue

    return shap_dict, feature_names


# ======================================================
# DELTA SHAP
# ======================================================

def compute_delta_shap(
    model, df_baseline, df_scenario, top_k=5, min_impact=0.001
):
    baseline_shap, _ = _compute_raw_shap(model, df_baseline)
    scenario_shap, _ = _compute_raw_shap(model, df_scenario)

    delta_shap = {}
    raw_delta_shap = {}

    all_features = set(
        list(baseline_shap.keys()) + list(scenario_shap.keys())
    )

    for feature in all_features:
        base_val = baseline_shap.get(feature, 0.0)
        scen_val = scenario_shap.get(feature, 0.0)
        delta = scen_val - base_val

        # Conserva tutti i contributi, senza filtro né arrotondamento
        raw_delta_shap[feature] = float(delta)

        # Mantiene invariato il comportamento originale
        if abs(delta) < min_impact:
            continue

        delta_shap[feature] = round(delta, 5)

    # Diagnostica: contributi completi e loro somma
    print("\n[SHAP DIAGNOSTIC] All raw Delta-SHAP:")
    for feature, value in sorted(
        raw_delta_shap.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    ):
        print(f"  {feature}: {value:+.10f}")

    print(
        f"[SHAP DIAGNOSTIC] Sum of all raw Delta-SHAP: "
        f"{sum(raw_delta_shap.values()):+.10f}"
    )

    print(
        f"[SHAP DIAGNOSTIC] Sum after min_impact filter: "
        f"{sum(delta_shap.values()):+.10f}"
    )

    ranking = sorted(
        delta_shap.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )
    top = ranking[:top_k]
    result = dict(top)

    debug_print("Delta SHAP:", result)
    return result


# ======================================================
# ONE-HOT AGGREGATION
# ======================================================

def aggregate_onehot_features(shap_dict):
    """
    Aggregate one-hot Delta-SHAP contributions by their original
    categorical feature, summing signed contributions before labels
    are simplified or prettified.
    """
    from collections import defaultdict

    categorical_prefixes = [
        "Change in land use and cover in the past decade",
        "Change in grassland presence in the past decade",
        "Land use and cover",
        "Presence of grassland",
    ]

    # Match the longest categorical feature name first.
    categorical_prefixes.sort(key=len, reverse=True)

    aggregated = defaultdict(float)

    for feature, value in shap_dict.items():
        clean = feature.replace("num__", "").replace("cat__", "")
        matched_prefix = None

        for prefix in categorical_prefixes:
            if clean.startswith(prefix + "_"):
                matched_prefix = prefix
                break

        if matched_prefix is not None:
            # Sum category-level contributions under the original feature.
            aggregated[matched_prefix] += float(value)

        else:
            # Preserve the previous handling of binary one-hot features.
            if clean.endswith("_0") or clean.endswith("_1"):
                clean = clean.rsplit("_", 1)[0]

            aggregated[clean] += float(value)

    return dict(aggregated)


# ======================================================
# FILTER HUMAN-READABLE FEATURES
# ======================================================

def simplify_feature_names(shap_dict):

    simplified = {}

    for k, v in shap_dict.items():

        clean = k

        clean = clean.replace("_", " ")

        simplified[clean] = round(v, 5)

    return simplified


# ======================================================
# SPLIT POSITIVE / NEGATIVE
# ======================================================

def split_shap_by_sign(shap_dict):

    positive = {
        k: v for k, v in shap_dict.items()
        if v > 0
    }

    negative = {
        k: v for k, v in shap_dict.items()
        if v < 0
    }

    return positive, negative


# ======================================================
# DRIVER EXTRACTION
# ======================================================

def extract_driver_names(shap_dict):

    return list(shap_dict.keys())