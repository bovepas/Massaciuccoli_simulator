# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Compare Task

Confronta l'influenza relativa di due driver
utilizzando lo stesso algoritmo di importance.

NOTA:
Il calcolo degli impact è volutamente duplicato
da task_importance.py per evitare regressioni.
"""

from utils.model_input_builder import (
    build_input_df,
    compute_baseline
)

from utils.importance_compare_parser import (
    parse_importance_compare
)

from utils.feature_mapping import (
    normalize_feature_name
)

from knowledge.rag_importance_compare import (
    generate_importance_compare_explanation
)


# ======================================================
# IMPACT STRENGTH
# ======================================================

def classify_impact_strength(score):

    score = abs(score)

    if score < 0.01:
        return "weak"

    if score < 0.05:
        return "moderate"

    return "strong"

# ======================================================
# ENTITY SCORE
# ======================================================

def compute_entity_score(
    entity_features,
    impacts
):

    print(
        "\n[DEBUG] compute_entity_score:"
    )

    print(
        "entity_features =",
        entity_features
    )

    # --------------------------------------------------
    # SINGLE FEATURE
    # --------------------------------------------------

    if isinstance(
        entity_features,
        str
    ):

        print(
            "[DEBUG] SINGLE FEATURE"
        )

        if entity_features not in impacts:

            print(
                "[DEBUG] NOT FOUND:",
                entity_features
            )

            return 0.0

        score = abs(

            impacts[
                entity_features
            ]["impact"]
        )

        print(
            "[DEBUG] FOUND:",
            entity_features,
            "->",
            score
        )

        return score

    # --------------------------------------------------
    # FEATURE GROUP
    # --------------------------------------------------

    if isinstance(
        entity_features,
        list
    ):

        print(
            "[DEBUG] FEATURE GROUP"
        )

        score = 0.0

        for feature in entity_features:

            if feature not in impacts:

                print(
                    "[DEBUG] NOT FOUND:",
                    feature
                )

                continue

            impact_value = abs(

                impacts[
                    feature
                ]["impact"]
            )

            print(
                "[DEBUG] FOUND:",
                feature,
                "->",
                impact_value
            )

            score += impact_value

        print(
            "[DEBUG] GROUP SCORE =",
            score
        )

        return score

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------

    print(
        "[DEBUG] UNKNOWN ENTITY TYPE"
    )

    return 0.0

# ======================================================
# MAIN
# ======================================================

def handle_importance_compare(
    question,
    model=None,
    dataset=None
):

    print(
        "\n========== IMPORTANCE COMPARE TASK START =========="
    )

    # --------------------------------------------------
    # SAFETY
    # --------------------------------------------------

    if model is None or dataset is None:

        return {

            "summary":
                "Model not available",

            "data":
                {},

            "drivers":
                [],

            "interpretation":
                "The model or dataset is missing."
        }

    # --------------------------------------------------
    # PARSER
    # --------------------------------------------------

    parsed = parse_importance_compare(
        question
    )

    print("\n[DEBUG] Parsed:")
    print(parsed)

    if not parsed:

        return {

            "summary":
                "Comparison not recognized",

            "data":
                {},

            "drivers":
                [],

            "interpretation":
                "Could not identify the variables to compare."
        }

    feature_a = normalize_feature_name(
        parsed["entity_a"]
    )

    feature_b = normalize_feature_name(
        parsed["entity_b"]
    )

    print("\n[DEBUG] Normalized features:")
    print("entity_a =", parsed["entity_a"])
    print("feature_a =", feature_a)

    print("entity_b =", parsed["entity_b"])
    print("feature_b =", feature_b)

    print("\n[DEBUG] Feature types:")

    print(
        "feature_a_is_list =",
        isinstance(feature_a, list)
    )

    print(
        "feature_b_is_list =",
        isinstance(feature_b, list)
    )

    # ======================================================
    # BASELINE
    # ======================================================

    baseline_values = compute_baseline(
        dataset
    )

    df_base = build_input_df(
        {},
        dataset
    )

    base_pred = float(
        model.predict(df_base)[0]
    )

    print(
        f"[DEBUG] Baseline prediction: {base_pred}"
    )

    # ======================================================
    # IMPORTANCE CALCULATION
    # (copiato da task_importance)
    # ======================================================

    impacts = {}

    for feature in baseline_values.keys():

        val = baseline_values[feature]
        print(
            "[FEATURE LOOP]",
            repr(feature)
        )

        if not isinstance(
            val,
            (int, float)
        ):
            continue

        try:

            feature_std = dataset[
                feature
            ].std()

        except Exception:

            continue

        if feature_std is None:
            continue

        if feature_std == 0:
            continue

        delta = 0.5 * feature_std

        test_values = baseline_values.copy()

        test_values[feature] = (
            val + delta
        )

        df_test = build_input_df(
            test_values,
            dataset
        )

        pred = float(
            model.predict(df_test)[0]
        )

        raw_impact = (
            pred - base_pred
        )

        impact = round(
            raw_impact,
            4
        )

        if feature in [

            "Density of tree cover",

            "Cumulative change in precipitation compared to a recent past",

            "Relative change in the potential evapotranspiration compared to a recent past"
        ]:

            print(
                "\n[DEBUG FEATURE]"
            )

            print(
                "feature =",
                feature
            )

            print(
                "delta =",
                delta
            )

            print(
                "base_pred =",
                base_pred
            )

            print(
                "pred =",
                pred
            )

            print(
                "raw_impact =",
                raw_impact
            )

            print(
                "rounded_impact =",
                impact
            )

        impacts[feature] = {

            "impact":
                impact,

            "strength":
                classify_impact_strength(
                    impact
                ),

            "perturbation_delta":
                round(
                    float(delta),
                    4
                )
        }

    print(
        "[DEBUG] impacts:"
    )

    print(
        impacts
    )
    # ======================================================
    # ENTITY SCORES
    # ======================================================

    score_a = compute_entity_score(

        feature_a,

        impacts
    )

    score_b = compute_entity_score(

        feature_b,

        impacts
    )

    print("\n[DEBUG] Entity scores:")

    print(
        "score_a =",
        score_a
    )

    print(
        "score_b =",
        score_b
    )

    # ======================================================
    # RAG
    # ======================================================

    interpretation = (

        generate_importance_compare_explanation(

            question=question,

            entity_a=parsed["entity_a"],
            entity_b=parsed["entity_b"],

            feature_a=feature_a,
            feature_b=feature_b,

            score_a=score_a,
            score_b=score_b
        )
    )

    print(
        "\n[DEBUG] interpretation:"
    )

    print(
        interpretation
    )

    return {

        "summary":
            "Importance comparison",

        "data": {

            "feature_a":
                feature_a,

            "feature_b":
                feature_b,

            "score_a":
                score_a,

            "score_b":
                score_b
        },

        "drivers":
            [],

        "interpretation":
            interpretation
    }