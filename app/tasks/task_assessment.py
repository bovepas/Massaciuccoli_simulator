# task_assessment.py

import numpy as np

from knowledge.rag_assessment import generate_assessment_explanation

from utils.model_input_builder import (
    build_input_df,
    compute_baseline
)

from utils.shap_utils import (
    compute_delta_shap,
    aggregate_onehot_features,
    simplify_feature_names,
    extract_driver_names
)

from utils.feature_mapping import (
    prettify_feature_name,
    prettify_feature_dict
)

# ======================================================
# QUALITATIVE SCALE
# ======================================================

QUALITATIVE_SCALE = {
    "slightly": 0.5,
    "moderately": 1.0,
    "significantly": 1.5,
    "strongly": 2.0,
    "severely": 2.5,
    "extremely": 3.0
}


# ======================================================
# DATASET STATISTICS
# ======================================================

def compute_feature_statistics(dataset):

    stats = {}

    if dataset is None:
        return stats

    numeric_df = dataset.select_dtypes(include=["number"])

    for col in numeric_df.columns:

        try:

            stats[col] = {
                "mean": float(numeric_df[col].mean()),
                "std": float(numeric_df[col].std())
            }

        except Exception:
            pass

    return stats


# ======================================================
# QUALITATIVE GROUNDING
# ======================================================

def apply_qualitative_changes(features, qualitative_changes, dataset):

    if not qualitative_changes:
        return features

    stats = compute_feature_statistics(dataset)

    grounded = features.copy()

    print("\n[ASSESSMENT] QUALITATIVE GROUNDING")

    for change in qualitative_changes:

        feature = change["feature"]
        direction = change["direction"]
        magnitude = change["magnitude"]

        if feature not in stats:
            continue

        std = stats[feature]["std"]

        scale = QUALITATIVE_SCALE.get(magnitude, 1.0)

        delta = std * scale

        if "decrease" in direction:
            delta = -delta

        baseline = grounded.get(feature, 0)

        grounded[feature] = baseline + delta

        print(f"""
Feature: {feature}
Direction: {direction}
Magnitude: {magnitude}
STD: {round(std, 3)}
Delta Applied: {round(delta, 3)}
Final Value: {round(grounded[feature], 3)}
""")

    return grounded


# ======================================================
# FEATURE PRIORITIZATION
# ======================================================

def prioritize_modified_features(
    shap_values,
    grounded_features,
    top_k=5
):

    """
    Separates:
    - primary perturbation drivers
    - secondary ecosystem responses
    """

    primary = {}
    secondary = {}

    modified_candidates = set()

    # --------------------------------------------------
    # Detect modified features
    # --------------------------------------------------

    for feature, value in grounded_features.items():

        # baseline-like defaults
        if feature == "Presence of grassland":

            if value != 1:
                modified_candidates.add(feature)

        elif value not in [0, 50, 200]:

            modified_candidates.add(feature)

    print("\n[ASSESSMENT] MODIFIED FEATURES")
    print(modified_candidates)

    # --------------------------------------------------
    # PRIMARY DRIVERS
    # --------------------------------------------------

    for feature, impact in shap_values.items():

        for modified in modified_candidates:

            normalized_modified = prettify_feature_name(
                modified
            )

            if normalized_modified.lower() == feature.lower():

                primary[feature] = impact
    # --------------------------------------------------
    # SECONDARY RESPONSES
    # --------------------------------------------------

    ranking = sorted(
        shap_values.items(),
        key=lambda x: abs(x[1]),
        reverse=True
    )

    for feature, impact in ranking:

        if feature in primary:
            continue

        secondary[feature] = impact

        if len(secondary) >= top_k:
            break

    return {
        "primary": primary,
        "secondary": secondary,
        "modified": list(modified_candidates)

    }


# ======================================================
# MAIN
# ======================================================

def handle_assessment(
    question,
    features=None,
    qualitative_changes=None,
    dataset=None,
    model=None,
    top_k=5
):

    print("\n========== ASSESSMENT TASK ==========")

    # ==================================================
    # SAFETY
    # ==================================================

    if features is None:
        features = {}

    if qualitative_changes is None:
        qualitative_changes = []

    if model is None or dataset is None:

        return {
            "summary": "Assessment unavailable",
            "data": {},
            "drivers": [],
            "interpretation": "Model or dataset missing."
        }

    # ==================================================
    # QUALITATIVE GROUNDING
    # ==================================================

    grounded_features = apply_qualitative_changes(
        features,
        qualitative_changes,
        dataset
    )

    print("\n[ASSESSMENT] FINAL FEATURES:")
    print(grounded_features)

    # ==================================================
    # BASELINE INPUT
    # ==================================================

    baseline_values = compute_baseline(dataset)

    df_baseline = build_input_df(
        baseline_values,
        dataset
    )

    baseline_risk = float(
        model.predict(df_baseline)[0]
    )

    # ==================================================
    # SCENARIO INPUT
    # ==================================================

    scenario_values = baseline_values.copy()

    for k, v in grounded_features.items():
        scenario_values[k] = v

    df_scenario = build_input_df(
        scenario_values,
        dataset
    )

    scenario_risk = float(
        model.predict(df_scenario)[0]
    )

    # ==================================================
    # DELTA
    # ==================================================

    risk_delta = scenario_risk - baseline_risk

    print("\n[ASSESSMENT]")
    print("Baseline risk:", round(baseline_risk, 4))
    print("Scenario risk:", round(scenario_risk, 4))
    print("Risk delta:", round(risk_delta, 4))

    # ==================================================
    # DELTA SHAP
    # ==================================================

    shap_values = compute_delta_shap(
        model=model,
        df_baseline=df_baseline,
        df_scenario=df_scenario,
        top_k=20
    )

    # ==================================================
    # AGGREGATE ONE-HOT FEATURES
    # ==================================================

    shap_values = aggregate_onehot_features(
        shap_values
    )

    # ==================================================
    # CLEAN FEATURE NAMES
    # ==================================================

    shap_values = simplify_feature_names(
        shap_values
    )

    # ==================================================
    # SEMANTIC PRESENTATION
    # ==================================================

    shap_values = prettify_feature_dict(
        shap_values
    )

    # ==================================================
    # PRIORITIZATION
    # ==================================================

    driver_groups = prioritize_modified_features(
        shap_values,
        grounded_features,
        top_k=top_k
    )

    primary_drivers = driver_groups["primary"]

    secondary_drivers = driver_groups["secondary"]

    modified_features = driver_groups["modified"]

    # --------------------------------------------------
    # Backward-compatible flat list
    # --------------------------------------------------

    combined_drivers = {
        **primary_drivers,
        **secondary_drivers
    }

    drivers = extract_driver_names(
        combined_drivers
    )

    print("\n[ASSESSMENT] PRIMARY DRIVERS")
    print(primary_drivers)

    print("\n[ASSESSMENT] SECONDARY RESPONSES")
    print(secondary_drivers)

    # ==================================================
    # RAG DRIVER PRIORITIZATION
    # ==================================================

    rag_drivers = (
        list(primary_drivers.keys()) +
        list(secondary_drivers.keys())[:2]
    )

    # ==================================================
    # RAG
    # ==================================================

    try:

        explanation = generate_assessment_explanation(
            question=question,
            drivers=rag_drivers,
            primary_drivers=primary_drivers,
            secondary_responses=secondary_drivers,
            risk_delta=risk_delta,
            features=modified_features        )

    except Exception as e:

        print("[ASSESSMENT][RAG ERROR]", e)

        explanation = (
            "The scenario alters ecosystem dynamics through "
            "changes in environmental stressors and ecological resilience."
        )

    # ==================================================
    # OUTPUT
    # ==================================================

    return {

        "summary": "Scenario-based ecosystem risk assessment",

        "baseline_risk": round(baseline_risk, 4),

        "scenario_risk": round(scenario_risk, 4),

        "risk_delta": round(risk_delta, 4),

        # backward-compatible
        "data": combined_drivers,

        "drivers": drivers,

        # new UX structure
        "primary_drivers": primary_drivers,

        "secondary_drivers": secondary_drivers,

        "grounded_features": grounded_features,

        "qualitative_changes": qualitative_changes,

        "interpretation": explanation
    }