# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Task — v10 (category + direction aware)

- focus selects the feature category (all/climate/biodiversity/land_use)
- direction selects the risk-response sign (all/increase/decrease)
- category and direction filters are independent
- top-k is applied only after both filters
"""

from collections import defaultdict

from knowledge.rag_importance import generate_importance_explanation
from utils.model_input_builder import build_input_df, compute_baseline


# ======================================================
# FEATURE GROUPS
# ======================================================

FEATURE_GROUPS = {

    "climate": [
        "temperature",
        "precipitation",
        "evapotranspiration"
    ],

    "biodiversity": [
        "species",
        "biodiversity",
        "productivity"
    ],

    "land_use": [
        "land use",
        "imperviousness"
    ],

    "vegetation": [
        "tree cover",
        "grassland",
        "vegetation"
    ]
}


# ======================================================
# FEATURE → GROUP
# ======================================================

def assign_feature_group(feature_name):

    f = feature_name.lower()

    for group, keywords in FEATURE_GROUPS.items():

        if any(k in f for k in keywords):
            return group

    return "other"


# ======================================================
# INPUT NORMALIZATION
# ======================================================

VALID_FOCUSES = {"all", "climate", "biodiversity", "land_use"}
VALID_DIRECTIONS = {"all", "increase", "decrease"}


def _normalize_importance_inputs(focus="all", direction="all", mode=None):
    """
    Normalize the new independent inputs while preserving compatibility
    with the previous orchestrator, which passed the parser's focus through
    the legacy `mode` argument.

    Legacy mode values increase/decrease are interpreted as direction.
    New category values passed through mode are interpreted as focus.
    """
    normalized_focus = str(focus or "all").strip().lower()
    normalized_direction = str(direction or "all").strip().lower()

    if mode is not None:
        legacy_mode = str(mode).strip().lower()

        if legacy_mode in VALID_FOCUSES:
            if normalized_focus == "all":
                normalized_focus = legacy_mode
        elif legacy_mode in {"increase", "decrease"}:
            if normalized_direction == "all":
                normalized_direction = legacy_mode

    if normalized_focus not in VALID_FOCUSES:
        raise ValueError(
            f"Invalid importance focus '{normalized_focus}'. "
            f"Expected one of {sorted(VALID_FOCUSES)}."
        )

    if normalized_direction not in VALID_DIRECTIONS:
        raise ValueError(
            f"Invalid importance direction '{normalized_direction}'. "
            f"Expected one of {sorted(VALID_DIRECTIONS)}."
        )

    return normalized_focus, normalized_direction


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
# MAIN
# ======================================================

def handle_importance(
    question,
    features=None,
    model=None,
    dataset=None,
    top_k=5,
    focus="all",
    direction="all",
    mode=None
):

    print("\n========== IMPORTANCE TASK START ==========")

    print(f"[DEBUG] question: {question}")
    print(f"[DEBUG] requested top_k: {top_k}")

    if model is None or dataset is None:

        return {
            "summary": "Model not available",
            "data": {},
            "drivers": [],
            "interpretation":
                "The model or dataset is missing."
        }

    # ======================================================
    # NORMALIZE PARSED SEMANTIC CONSTRAINTS
    # ======================================================

    try:
        focus, direction = _normalize_importance_inputs(
            focus=focus,
            direction=direction,
            mode=mode
        )
    except ValueError as exc:
        return {
            "summary": "Invalid importance query constraints",
            "data": {},
            "drivers": [],
            "interpretation": str(exc)
        }

    try:
        top_k = max(1, int(top_k))
    except (TypeError, ValueError):
        top_k = 5

    print(f"[DEBUG] feature-category focus: {focus}")
    print(f"[DEBUG] risk direction: {direction}")
    print(f"[DEBUG] effective top_k: {top_k}")

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

    print(f"[DEBUG] Baseline prediction: {base_pred}")

    # ======================================================
    # DISTRIBUTION-AWARE IMPORTANCE
    # ======================================================

    all_feature_impacts = {}

    structured_impacts = []

    for feature in baseline_values.keys():

        val = baseline_values[feature]

        # --------------------------------------------------
        # ONLY NUMERIC FEATURES
        # --------------------------------------------------

        if not isinstance(val, (int, float)):
            continue

        # --------------------------------------------------
        # COMPUTE FEATURE DISTRIBUTION
        # --------------------------------------------------

        try:

            feature_std = dataset[feature].std()

        except Exception:
            continue

        if feature_std is None:
            continue

        if feature_std == 0:
            continue

        # --------------------------------------------------
        # CALIBRATED PERTURBATION
        # --------------------------------------------------

        delta = 0.5 * feature_std

        test_values = baseline_values.copy()

        test_values[feature] = val + delta

        # --------------------------------------------------
        # PREDICT
        # --------------------------------------------------

        df_test = build_input_df(
            test_values,
            dataset
        )

        pred = float(
            model.predict(df_test)[0]
        )

        impact = pred - base_pred

        impact = round(
            float(impact),
            4
        )

        all_feature_impacts[feature] = impact

        # --------------------------------------------------
        # SEMANTIC GROUP
        # --------------------------------------------------

        group = assign_feature_group(
            feature
        )

        # --------------------------------------------------
        # STRUCTURED IMPACTS
        # --------------------------------------------------

        structured_impacts.append({

            "name": feature,

            "impact": impact,

            "strength":
                classify_impact_strength(
                    impact
                ),

            "group":
                group,

            "perturbation_delta":
                round(float(delta), 4)
        })

    print("[DEBUG] raw perturbation impacts:")
    print(all_feature_impacts)

    # ======================================================
    # FILTER NUMERICALLY ZERO IMPACTS
    # ======================================================

    structured_impacts = [
        d for d in structured_impacts
        if abs(d["impact"]) > 0.0
    ]

    # ======================================================
    # CATEGORY FILTER
    # ======================================================

    if focus != "all":
        structured_impacts = [
            d for d in structured_impacts
            if d["group"] == focus
        ]

    # ======================================================
    # RISK-DIRECTION FILTER
    # ======================================================

    if direction == "increase":
        structured_impacts = [
            d for d in structured_impacts
            if d["impact"] > 0
        ]
    elif direction == "decrease":
        structured_impacts = [
            d for d in structured_impacts
            if d["impact"] < 0
        ]

    print(
        "[DEBUG] candidates after category/direction filters: "
        f"{len(structured_impacts)}"
    )

    # ======================================================
    # RANKING
    # ======================================================

    ranking = sorted(

        structured_impacts,

        key=lambda x: abs(x["impact"]),

        reverse=True
    )

    # ======================================================
    # 🔥 APPLY TOP-K AFTER SEMANTIC FILTERING
    # ======================================================

    top = ranking[:top_k]

    # The returned data must respect top_k as well as the semantic filters.
    impact_scores = {
        d["name"]: d["impact"]
        for d in top
    }

    # ======================================================
    # GROUP ATTRIBUTION
    # ======================================================

    group_scores = defaultdict(float)

    for d in top:

        group_scores[d["group"]] += abs(
            d["impact"]
        )

    group_scores = dict(sorted(

        group_scores.items(),

        key=lambda x: x[1],

        reverse=True
    ))

    print("[DEBUG] group_scores:")
    print(group_scores)

    # ======================================================
    # SPLIT POSITIVE / NEGATIVE
    # ======================================================

    positive = [
        d for d in top
        if d["impact"] > 0
    ]

    negative = [
        d for d in top
        if d["impact"] < 0
    ]

    # ======================================================
    # DEBUG
    # ======================================================

    print("[DEBUG] structured_impacts:")
    print(top)

    # ======================================================
    # UI DRIVERS
    # ======================================================

    drivers = []

    # --------------------------------------------------
    # GROUP SUMMARY
    # --------------------------------------------------

    if group_scores:

        dominant_groups = list(
            group_scores.keys()
        )[:2]

        drivers.append(
            "🌍 Dominant ecosystem domains:"
        )

        drivers.extend([
            f"{g} (score={round(group_scores[g], 3)})"
            for g in dominant_groups
        ])

    # --------------------------------------------------
    # POSITIVE
    # --------------------------------------------------

    if positive:

        drivers.append(
            "📈 Increasing risk:"
        )

        drivers.extend([

            f"{d['name']} "
            f"[{d['group']}] "
            f"(impact={round(d['impact'], 3)}, "
            f"{d['strength']})"

            for d in positive
        ])

    # --------------------------------------------------
    # NEGATIVE
    # --------------------------------------------------

    if negative:

        drivers.append(
            "📉 Reducing risk:"
        )

        drivers.extend([

            f"{d['name']} "
            f"[{d['group']}] "
            f"(impact={round(d['impact'], 3)}, "
            f"{d['strength']})"

            for d in negative
        ])
    # ======================================================
    # SEMANTIC FEATURES
    # ======================================================

    semantic_features = [

        d["name"]

        for d in top
    ]

    print(
        "[DEBUG] semantic_features:"
    )

    print(
        semantic_features
    )
    
    # ======================================================
    # RAG
    # ======================================================

    if not top:
        explanation = (
            "No variables met the requested importance constraints "
            f"(category: {focus}; risk direction: {direction}) "
            "after the task's impact-noise filter. This does not mean "
            "that no relationship exists; it means that this analysis "
            "did not identify qualifying variables under the current "
            "perturbation and filtering settings."
        )
    else:
        try:
            explanation = generate_importance_explanation(
                top,
                question,
                group_scores=group_scores,
                features=semantic_features
            )

        except Exception as e:

            print("[IMPORTANCE][RAG ERROR]")
            print(e)

            explanation = (
                "The identified variables influence "
                "ecosystem risk through environmental "
                "stress and ecosystem imbalance."
            )

    # ======================================================
    # OUTPUT
    # ======================================================

    return {

        "summary":
            "Top factors influencing ecosystem risk",

        "data":
            impact_scores,

        "drivers":
            drivers,

        "group_scores":
            group_scores,

        "query_constraints": {
            "top_k": top_k,
            "focus": focus,
            "direction": direction
        },

        "interpretation":
            explanation
    }