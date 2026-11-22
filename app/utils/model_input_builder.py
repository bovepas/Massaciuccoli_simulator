# -*- coding: utf-8 -*-
"""Model Input Builder — Single Source of Truth."""

import pandas as pd

from versions.v6_1_emulator import (
    NUM_FEATURES,
    CAT_FEATURES,
    preprocess_semantic_features
)

ADDITIVE_PERCENTAGE_FEATURES = {
    "Relative change in the potential evapotranspiration compared to a recent past",
    "Cumulative change in precipitation compared to a recent past",
}


def clean_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    df = dataset.copy()
    test_col = NUM_FEATURES[0]
    df[test_col] = pd.to_numeric(df[test_col], errors="coerce")
    return df[df[test_col].notna()]


def compute_baseline(dataset: pd.DataFrame) -> dict:
    dataset = clean_dataset(dataset)
    baseline = {}
    for col in NUM_FEATURES:
        baseline[col] = float(pd.to_numeric(dataset[col], errors="coerce").mean())
    for col in CAT_FEATURES:
        baseline[col] = dataset[col].mode().iloc[0]
    return baseline


def build_input_df(values: dict, dataset: pd.DataFrame,
                   interpret_percentages=False) -> pd.DataFrame:
    baseline = compute_baseline(dataset)
    precip = "Cumulative change in precipitation compared to a recent past"


    if not interpret_percentages:
        baseline.update(values)
    else:
        for k, v in values.items():
            if isinstance(v, dict):
                mod_type = v.get("type")
                mod_value = v.get("value")
                print("[DEBUG]", k, mod_type, mod_value)

                if mod_type == "percentage_change" and k in baseline:
                    # PET and precipitation are already relative changes:
                    # apply their percentage-point delta additively.
                    if k in ADDITIVE_PERCENTAGE_FEATURES:
                        baseline[k] += mod_value
                    else:
                        baseline[k] *= (1 + mod_value / 100)

                elif mod_type in ("numeric", "absolute_delta") and k in baseline:
                    baseline[k] += mod_value

                elif mod_type in ("absolute_target", "categorical_target"):
                    baseline[k] = mod_value

                else:
                    baseline[k] = mod_value
                continue

            # Legacy behavior retained for existing callers.
            if k in baseline and isinstance(v, (int, float)):
                if abs(v) <= 5:
                    baseline[k] += v
                else:
                    baseline[k] *= (1 + v / 100)
            else:
                baseline[k] = v

    df = pd.DataFrame([baseline])
    df = df[NUM_FEATURES + CAT_FEATURES]
    return preprocess_semantic_features(df)


def compute_feature_statistics(dataset: pd.DataFrame) -> dict:
    dataset = clean_dataset(dataset)
    stats = {}
    for col in NUM_FEATURES:
        values = pd.to_numeric(dataset[col], errors="coerce")
        stats[col] = {
            "mean": float(values.mean()),
            "std": float(values.std()),
        }
    return stats


def build_baseline_and_scenario(delta_values: dict, dataset: pd.DataFrame):
    """Legacy helper; retains its historical magnitude-based heuristic."""
    baseline = compute_baseline(dataset)
    scenario = baseline.copy()

    for k, v in delta_values.items():
        if k in baseline and isinstance(baseline[k], (int, float)):
            base_val = baseline[k]
            if abs(v) <= 5:
                scenario[k] = base_val + v
            else:
                scenario[k] = base_val * (1 + v / 100)
        else:
            scenario[k] = v

    columns = NUM_FEATURES + CAT_FEATURES
    df_base = preprocess_semantic_features(pd.DataFrame([baseline])[columns])
    df_scen = preprocess_semantic_features(pd.DataFrame([scenario])[columns])
    return df_base, df_scen


def build_scenario(modifications: dict, dataset: pd.DataFrame):
    """
    Structured scenario builder.

    Supported types: percentage_change, absolute_delta, absolute_target,
    categorical_target. PET and precipitation percentage changes are
    additive because the stored features are already changes from reference.
    """
    import math
    from numbers import Real

    baseline = compute_baseline(dataset)
    scenario = baseline.copy()

    for feature, modification in modifications.items():
        if feature not in baseline:
            raise ValueError(f"Unknown model feature: {feature}")
        if not isinstance(modification, dict):
            raise ValueError(
                f"Modification for '{feature}' must be a structured dictionary."
            )

        mod_type = modification.get("type")
        value = modification.get("value")

        if mod_type == "categorical_target":
            if feature not in CAT_FEATURES:
                raise ValueError(f"'{feature}' is not a categorical feature.")
            if value is None:
                raise ValueError(f"Missing categorical target for '{feature}'.")
            scenario[feature] = value
            continue

        if feature not in NUM_FEATURES:
            raise ValueError(f"'{feature}' is not a numeric feature.")
        if (isinstance(value, bool) or not isinstance(value, Real)
                or not math.isfinite(value)):
            raise ValueError(f"Invalid numeric value for '{feature}': {value}")

        base_value = baseline[feature]

        if mod_type == "percentage_change":
            if feature in ADDITIVE_PERCENTAGE_FEATURES:
                scenario[feature] = base_value + value
            else:
                scenario[feature] = base_value * (1 + value / 100)
        elif mod_type == "absolute_delta":
            scenario[feature] = base_value + value
        elif mod_type == "absolute_target":
            scenario[feature] = value
        else:
            raise ValueError(
                f"Unsupported modification type '{mod_type}' for '{feature}'."
            )

    columns = NUM_FEATURES + CAT_FEATURES
    df_base = preprocess_semantic_features(pd.DataFrame([baseline])[columns])
    df_scenario = preprocess_semantic_features(pd.DataFrame([scenario])[columns])
    return df_base, df_scenario
