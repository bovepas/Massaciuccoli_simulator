# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Importance Task — v9 (focus-aware ranking)

✔ Distribution-aware perturbation scaling
✔ Semantic ecosystem grouping
✔ Focus-aware ranking
✔ Correct top-k semantic filtering
✔ Group-level ecosystem attribution
✔ Improved ecosystem interpretability
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
# FOCUS DETECTION
# ======================================================

def detect_focus(question):

    q = question.lower()

    increase_patterns = [

        "increase ecosystem risk",
        "increasing ecosystem risk",
        "higher ecosystem risk",
        "raise ecosystem risk",
        "drivers of ecosystem risk",
        "risk increasing",
        "increase risk"
    ]

    decrease_patterns = [

        "reduce ecosystem risk",
        "decreasing ecosystem risk",
        "lower ecosystem risk",
        "mitigate ecosystem risk",
        "reduce risk"
    ]

    if any(p in q for p in increase_patterns):
        return "increase"

    if any(p in q for p in decrease_patterns):
        return "decrease"

    return "all"


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
    mode="increase"
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
    # DETECT FOCUS
    # ======================================================

    focus = detect_focus(
        question
    )

    print(f"[DEBUG] detected focus: {focus}")

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

    shap_values = {}

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

        shap_values[feature] = impact

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

    print("[DEBUG] shap_values:")
    print(shap_values)

    # ======================================================
    # FILTER NOISE
    # ======================================================

    structured_impacts = [

        d for d in structured_impacts

        if abs(d["impact"]) > 0.01
    ]

    # ======================================================
    # 🔥 FOCUS-AWARE FILTERING
    # ======================================================

    if focus == "increase":

        structured_impacts = [

            d for d in structured_impacts

            if d["impact"] > 0
        ]

    elif focus == "decrease":

        structured_impacts = [

            d for d in structured_impacts

            if d["impact"] < 0
        ]

    # ======================================================
    # SHAP VALUES
    # ======================================================

    shap_values = {

        d["name"]: d["impact"]

        for d in structured_impacts
    }

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
    # RAG
    # ======================================================

    try:

        explanation = generate_importance_explanation(
            top,
            question,
            group_scores=group_scores
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
            shap_values,

        "drivers":
            drivers,

        "group_scores":
            group_scores,

        "interpretation":
            explanation
    }