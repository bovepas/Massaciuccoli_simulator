# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Task: Comparison v8 (DUAL ASSESSMENT LITE)

✔ Real model predictions
✔ Dual local explainability
✔ Semantic driver prioritization
✔ Transition-ready architecture
✔ KB-grounded comparison
✔ Backward compatible
"""

import pandas as pd

from utils.feature_mapping import (
    normalize_feature_name,
    prettify_feature_dict,
    prettify_feature_name
)

from utils.scenario_parser import (
    parse_comparison_scenarios
)

from utils.model_input_builder import (
    build_input_df,
    compute_baseline
)

from utils.shap_utils import (
    compute_delta_shap,
    aggregate_onehot_features,
    simplify_feature_names
)

from knowledge.rag_comparison import (
    generate_comparison_explanation
)

from utils.model_input_builder import (
    compute_feature_statistics
)



DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


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
        'Change in grassland presence  in the past decade': '0',
        'Change in tree cover density in the past decade': '0'
    }


# ======================================================
# PRIMARY / SECONDARY SPLIT
# ======================================================

def split_primary_secondary(
    shap_values,
    modified_features
):

    primary = {}
    secondary = {}

    for feature, impact in shap_values.items():

        matched = False

        for modified in modified_features:

            pretty_modified = prettify_feature_name(
                modified
            )

            if pretty_modified.lower() == feature.lower():

                primary[feature] = impact
                matched = True
                break

        if not matched:
            secondary[feature] = impact

    return primary, secondary


# ======================================================
# SCENARIO ANALYSIS
# ======================================================

def analyze_scenario(
    scenario_features,
    model,
    dataset,
    top_k=5
):

    baseline_values = compute_baseline(dataset)

    # --------------------------------------------------
    # INPUTS
    # --------------------------------------------------

    df_base = build_input_df(
        baseline_values,
        dataset
    )
    print("\n[DEBUG] Scenario features:")
    print(scenario_features)

    print("\n[DEBUG] Baseline:")
    print(compute_baseline(dataset))

    df_scenario = build_input_df(
        scenario_features,
        dataset,
        interpret_percentages=True
    )

    print("\n[DEBUG] Scenario DF:")
    print(df_scenario.T)

    # --------------------------------------------------
    # PREDICTIONS
    # --------------------------------------------------

    base_pred = float(
        model.predict(df_base)[0]
    )

    scenario_pred = float(
        model.predict(df_scenario)[0]
    )

    delta = scenario_pred - base_pred

    # --------------------------------------------------
    # SHAP
    # --------------------------------------------------

    shap_values = compute_delta_shap(
         model=model,
        df_baseline=df_base,
        df_scenario=df_scenario,
        top_k=top_k
    )

    shap_values = aggregate_onehot_features(
        shap_values
    )

    shap_values = simplify_feature_names(
        shap_values
    )

    shap_values = prettify_feature_dict(
        shap_values
    )

    # --------------------------------------------------
    # FILTER SMALL RESPONSES
    # --------------------------------------------------

    shap_values = {
        k: v
        for k, v in shap_values.items()
        if abs(v) > 0.01
    }

    # --------------------------------------------------
    # MODIFIED FEATURES
    # --------------------------------------------------

    modified_candidates = list(
        scenario_features.keys()
    )

    modified_candidates = [
        prettify_feature_name(x)
        for x in modified_candidates
    ]

    primary, secondary = split_primary_secondary(
        shap_values,
        modified_candidates
    )

    return {

        "risk": round(scenario_pred, 4),

        "delta": round(delta, 4),

        "primary_drivers": primary,

        "secondary_drivers": secondary,

        "shap_values": shap_values
    }


# ======================================================
# DRIVER FORMATTER
# ======================================================

def format_scenario_drivers(
    title,
    primary,
    secondary
):

    output = []

    output.append(title)
    output.append("PRIMARY DRIVERS")

    for k, v in primary.items():

        output.append(
            f"{k} (impact={round(v, 3)})"
        )

    output.append("SECONDARY RESPONSES")

    if secondary:

        for k, v in secondary.items():

            output.append(
                f"{k} (impact={round(v, 3)})"
            )

    else:

        output.append(
            "No major secondary ecosystem responses detected."
        )

    return output


# ======================================================
# SUMMARY
# ======================================================

def build_summary(score_a, score_b):

    delta = abs(score_a - score_b)

    # --------------------------------------------------
    # SIMILAR RISK
    # --------------------------------------------------

    if delta < 0.01:

        return (
            "The two scenarios produce "
            "similar ecosystem risk"
        )

    # --------------------------------------------------
    # SCENARIO A WORSE
    # --------------------------------------------------

    if score_a > score_b:

        return (
            "The first scenario produces "
            "higher ecosystem risk"
        )

    # --------------------------------------------------
    # SCENARIO B WORSE
    # --------------------------------------------------

    return (
        "The second scenario produces "
        "higher ecosystem risk"
    )


# ======================================================
# MAIN
# ======================================================



def handle_comparison(
    question,
    model,
    dataset=None
):

    print("\n========== COMPARISON TASK START ==========")

    feature_stats = compute_feature_statistics(
    dataset
)

    # ==================================================
    # SAFETY
    # ==================================================

    if model is None or dataset is None:

        return {
            "summary": "Comparison unavailable",
            "data": {},
            "drivers": [],
            "interpretation": (
                "Model or dataset missing."
            )
        }

    # ==================================================
    # PARSING
    # ==================================================

    scenario_A, scenario_B = (
        parse_comparison_scenarios(
            question,
            feature_stats
        )
    )

    debug_print(
        "[DEBUG] Parsed Scenario A:",
        scenario_A
    )

    debug_print(
        "[DEBUG] Parsed Scenario B:",
        scenario_B
    )

    if not scenario_A or not scenario_B:

        return {
            "summary": "Comparison not recognized",
            "data": {},
            "drivers": [],
            "interpretation": (
                "Could not parse scenarios"
            )
        }

    # ==================================================
    # NORMALIZATION
    # ==================================================

    normalized_A = {}
    normalized_B = {}

    for k, v in scenario_A.items():

        feature = normalize_feature_name(k)

        if feature:
            normalized_A[feature] = v

    for k, v in scenario_B.items():

        feature = normalize_feature_name(k)

        if feature:
            normalized_B[feature] = v

    # ==================================================
    # ANALYSIS
    # ==================================================

    analysis_A = analyze_scenario(
        normalized_A,
        model,
        dataset
    )

    analysis_B = analyze_scenario(
        normalized_B,
        model,
        dataset
    )

    score_A = analysis_A["risk"]
    score_B = analysis_B["risk"]

    delta = round(score_B - score_A, 4)

    debug_print(
        f"[DEBUG] Scores: "
        f"A={score_A} | "
        f"B={score_B} | "
        f"Δ={delta}"
    )

    # ==================================================
    # RAG DRIVER STRUCTURE
    # ==================================================

    structured_drivers = []

    # --------------------------------------------------
    # SCENARIO A
    # --------------------------------------------------

    for feature, impact in analysis_A["primary_drivers"].items():

        structured_drivers.append(
            (feature, impact, None)
        )

    # --------------------------------------------------
    # SCENARIO B
    # --------------------------------------------------

    for feature, impact in analysis_B["primary_drivers"].items():

        structured_drivers.append(
            (feature, None, impact)
        )

    # ==================================================
    # SEMANTIC FEATURES
    # ==================================================

    semantic_features = list(
        set(
            list(normalized_A.keys()) +
            list(normalized_B.keys())
        )
    )

    debug_print(
        "[DEBUG] Semantic features:",
        semantic_features
    )

    # ==================================================
    # RAG
    # ==================================================

    rag_text = generate_comparison_explanation(
        drivers=structured_drivers,
        delta=delta,
        features=semantic_features

    )

    interpretation = rag_text

    # ==================================================
    # SUMMARY
    # ==================================================

    summary = build_summary(
        score_A,
        score_B
    )

    # ==================================================
    # DRIVER OUTPUT
    # ==================================================

    drivers = []

    drivers.extend(
        format_scenario_drivers(
            "SCENARIO A",
            analysis_A["primary_drivers"],
            analysis_A["secondary_drivers"]
        )
    )

    drivers.extend(
        format_scenario_drivers(
            "SCENARIO B",
            analysis_B["primary_drivers"],
            analysis_B["secondary_drivers"]
        )
    )

    print("========== COMPARISON TASK END ==========\n")

    # ==================================================
    # OUTPUT
    # ==================================================

    return {

        "summary": summary,

        "data": {

            "scenario_a": {

                "risk": score_A,

                "delta_from_baseline":
                    analysis_A["delta"]
            },

            "scenario_b": {

                "risk": score_B,

                "delta_from_baseline":
                    analysis_B["delta"]
            },

            "risk_difference": delta
        },

        "drivers": drivers,

        "interpretation": interpretation
    }