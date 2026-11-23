# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Compare Task

Confronta gli effetti sul rischio delle variazioni indicate
per due variabili o gruppi di variabili numeriche.

Le entita' composte vengono valutate perturbando simultaneamente
le rispettive feature numeriche.
Le variabili categoriche non sono ancora supportate.
"""

import math
from versions.v6_1_emulator import NUM_FEATURES, CAT_FEATURES

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

def classify_impact_strength(impact):
    """Classifica l'intensita' assoluta della variazione di rischio."""

    magnitude = abs(float(impact))

    if magnitude < 0.01:
        return "weak"

    if magnitude < 0.05:
        return "moderate"

    return "strong"


# ======================================================
# DIRECTION
# ======================================================

def get_direction_sign(direction):
    """Converte la direzione estratta nel segno della perturbazione."""

    direction = (direction or "unspecified").strip().lower()

    if direction == "decrease":
        return -1.0

    if direction in ("increase", "unspecified"):
        return 1.0

    raise ValueError(
        f"Unsupported direction '{direction}'. "
        "Expected increase, decrease or unspecified."
    )


# ======================================================
# ENTITY FEATURES VALIDATION
# ======================================================

def get_numeric_entity_features(entity_features):
    """
    Restituisce le feature numeriche di un'entita'.

    Le feature categoriche sono riconosciute ma non supportate:
    senza una transizione esplicita, la perturbazione sarebbe ambigua.
    """

    if isinstance(entity_features, str):
        features = [entity_features]
    elif isinstance(entity_features, list) and entity_features:
        features = entity_features
    else:
        raise ValueError("Entity is empty or has an unsupported format.")

    categorical = [
        feature for feature in features
        if feature in CAT_FEATURES
    ]

    unknown = [
        feature for feature in features
        if feature not in NUM_FEATURES and feature not in CAT_FEATURES
    ]

    if categorical:
        raise ValueError(
            "The comparison includes categorical variable(s): "
            f"{categorical}. "
            "Categorical variables cannot be perturbed using numerical "
            "increases or decreases. Without an explicitly specified "
            "categorical transition, the requested modification is "
            "ambiguous and its impact cannot be evaluated."
        )

    if unknown:
        raise ValueError(
            f"Unrecognized model feature(s): {unknown}"
        )

    return features


# ======================================================
# ENTITY IMPACT
# ======================================================

def compute_entity_impact(
    entity_features,
    direction,
    baseline_values,
    dataset,
    model,
    baseline_prediction
):
    """
    Calcola l'effetto di una variazione specifica sul rischio.

    Per i gruppi, tutte le feature numeriche vengono perturbate
    simultaneamente nella direzione richiesta. L'impatto del gruppo
    e' la differenza tra la predizione dello scenario combinato e
    la predizione baseline: gli effetti non vengono sommati.
    """

    features = get_numeric_entity_features(entity_features)
    direction_sign = get_direction_sign(direction)

    scenario_values = baseline_values.copy()
    perturbations = {}

    for feature in features:
        baseline_value = baseline_values.get(feature)

        if baseline_value is None or not isinstance(
            baseline_value, (int, float)
        ) or not math.isfinite(float(baseline_value)):
            raise ValueError(
                f"Baseline value for '{feature}' is not a valid number."
            )

        try:
            feature_std = float(dataset[feature].std())
        except Exception as exc:
            raise ValueError(
                f"Could not calculate standard deviation for '{feature}'."
            ) from exc

        if not math.isfinite(feature_std) or feature_std <= 0:
            raise ValueError(
                f"Feature '{feature}' has no usable standard deviation; "
                "a directional perturbation cannot be calculated."
            )

        delta = direction_sign * 0.5 * feature_std
        scenario_value = float(baseline_value) + delta
        scenario_values[feature] = scenario_value

        perturbations[feature] = {
            "baseline_value": round(float(baseline_value), 6),
            "delta": round(float(delta), 6),
            "scenario_value": round(float(scenario_value), 6)
        }

    scenario_df = build_input_df(
        scenario_values,
        dataset
    )

    scenario_prediction = float(
        model.predict(scenario_df)[0]
    )

    raw_impact = scenario_prediction - baseline_prediction
    impact = round(raw_impact, 4)

    return {
        "impact": impact,
        "strength": classify_impact_strength(impact),
        "baseline_prediction": round(float(baseline_prediction), 4),
        "scenario_prediction": round(scenario_prediction, 4),
        "perturbations": perturbations,
        "features": features
    }


# ======================================================
# MAIN
# ======================================================

def handle_importance_compare(
    question,
    model=None,
    dataset=None,
    importance_compare_inputs=None
):

    print(
        "\n========== IMPORTANCE COMPARE TASK START =========="
    )

    # --------------------------------------------------
    # SAFETY
    # --------------------------------------------------

    if model is None or dataset is None:
        return {
            "summary": "Model not available",
            "data": {},
            "drivers": [],
            "interpretation": "The model or dataset is missing."
        }

    # --------------------------------------------------
    # EXTRACTION / LEGACY PARSER
    # --------------------------------------------------

    if importance_compare_inputs is not None:
        parsed = importance_compare_inputs

        # Original semantic entities
        entity_a = parsed.get("entity_a")
        entity_b = parsed.get("entity_b")

        # Normalized numerical features
        feature_a = parsed.get("feature_a") or normalize_feature_name(entity_a)
        feature_b = parsed.get("feature_b") or normalize_feature_name(entity_b)

        direction_a = parsed.get("direction_a", "unspecified")
        direction_b = parsed.get("direction_b", "unspecified")

    else:
        parsed = parse_importance_compare(question)

        print("\n[DEBUG] Parsed:")
        print(parsed)

        if not parsed:
            return {
                "summary": "Comparison not recognized",
                "data": {},
                "drivers": [],
                "interpretation": (
                    "Could not identify the variables to compare."
                )
            }

        feature_a = normalize_feature_name(parsed.get("entity_a"))
        feature_b = normalize_feature_name(parsed.get("entity_b"))
        direction_a = parsed.get("direction_a", "unspecified")
        direction_b = parsed.get("direction_b", "unspecified")

    print("\n[DEBUG] Normalized entities:")
    print("entity_a =", parsed.get("entity_a"))
    print("feature_a =", feature_a)
    print("direction_a =", direction_a)
    print("entity_b =", parsed.get("entity_b"))
    print("feature_b =", feature_b)
    print("direction_b =", direction_b)

    # --------------------------------------------------
    # BASELINE
    # --------------------------------------------------

    baseline_values = compute_baseline(dataset)

    baseline_df = build_input_df(
        {},
        dataset
    )

    baseline_prediction = float(
        model.predict(baseline_df)[0]
    )

    print(
        f"[DEBUG] Baseline prediction: {baseline_prediction}"
    )

    # --------------------------------------------------
    # DIRECTIONAL ENTITY IMPACTS
    # --------------------------------------------------

    try:
        result_a = compute_entity_impact(
            entity_features=feature_a,
            direction=direction_a,
            baseline_values=baseline_values,
            dataset=dataset,
            model=model,
            baseline_prediction=baseline_prediction
        )

        result_b = compute_entity_impact(
            entity_features=feature_b,
            direction=direction_b,
            baseline_values=baseline_values,
            dataset=dataset,
            model=model,
            baseline_prediction=baseline_prediction
        )

    except ValueError as exc:
        message = str(exc)
        print("[IMPORTANCE COMPARE VALIDATION ERROR]", message)

        return {
            "summary": "Unsupported comparison",
            "data": {},
            "drivers": [],
            "interpretation": message
        }

    print("\n[DEBUG] Directional impacts:")
    print("impact_a =", result_a)
    print("impact_b =", result_b)

    # --------------------------------------------------
    # RAG
    # --------------------------------------------------

    interpretation = generate_importance_compare_explanation(
        question=question,
        entity_a=parsed.get("entity_a"),
        entity_b=parsed.get("entity_b"),
        feature_a=feature_a,
        feature_b=feature_b,
        direction_a=direction_a,
        direction_b=direction_b,
        impact_a=result_a["impact"],
        impact_b=result_b["impact"],
        perturbations_a=result_a["perturbations"],
        perturbations_b=result_b["perturbations"]
    )

    print(
        "\n[DEBUG] interpretation:"
    )
    print(interpretation)

    return {
        "summary": "Directional impact comparison",
        "data": {
            "feature_a": feature_a,
            "feature_b": feature_b,
            "direction_a": direction_a,
            "direction_b": direction_b,
            "baseline_risk": round(baseline_prediction, 4),
            # Backward-compatible magnitude fields; signed effects are
            # exposed separately as impact_a and impact_b.
            "score_a": abs(result_a["impact"]),
            "score_b": abs(result_b["impact"]),
            "impact_a": result_a["impact"],
            "impact_b": result_b["impact"],
            "strength_a": result_a["strength"],
            "strength_b": result_b["strength"],
            "scenario_risk_a": result_a["scenario_prediction"],
            "scenario_risk_b": result_b["scenario_prediction"],
            "perturbations_a": result_a["perturbations"],
            "perturbations_b": result_b["perturbations"]
        },
        "drivers": [],
        "interpretation": interpretation
    }
