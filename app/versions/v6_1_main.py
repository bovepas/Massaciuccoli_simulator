# -*- coding: utf-8 -*-

import re

from utils.logger import (
    log_section,
    log_question,
    log_route
)

from utils.feature_parser import parse_features


# ======================================================
# NORMALIZATION
# ======================================================

def normalize(q: str) -> str:
    return q.lower().strip()


# ======================================================
# DATA DETECTION
# ======================================================

DATA_KEYWORDS = [
    "data",
    "dataset",
    "value",
    "values",
    "numbers",
    "measurements",
    "records",
    "time series",
    "latest",
    "current value",
    "retrieve",
    "get data",
    "show data"
]


def is_data_query(q: str):

    return any(k in q for k in DATA_KEYWORDS)


# ======================================================
# TARGET DETECTION
# ======================================================

def detect_target(q: str):

    risk_patterns = [
        "ecosystem risk",
        "risk level",
        "risk score",

        # 🔥 NEW
        "risk"
    ]

    if any(p in q for p in risk_patterns):
        return "risk"

    if "ecosystem" in q:
        return "ecosystem"

    variable_patterns = [
        "temperature",
        "precipitation",
        "biodiversity",
        "species richness",
        "tree cover",
        "grassland",
        "evapotranspiration",
        "productivity"
    ]

    for v in variable_patterns:

        if v in q:
            return "variable"

    return "unknown"


# ======================================================
# DRIVER ANALYSIS
# ======================================================

def asks_driver_analysis(q: str):

    patterns = [
        "drivers",
        "drive",
        "driving",
        "important",
        "importance",
        "influential",
        "main factors",
        "top factors",
        "top variables",
        "which factors",
        "which variables",
        "what drives"
    ]

    return any(p in q for p in patterns)


# ======================================================
# RISK ESTIMATION
# ======================================================

def asks_risk_estimation(q: str):

    patterns = [
        "risk level",
        "ecosystem risk",
        "estimate risk",
        "estimate the ecosystem risk",
        "assess ecosystem risk",
        "predict ecosystem risk",
        "what is the risk",
        "risk score",
        "environmental conditions",
        "state of the ecosystem",
        "current ecosystem state"
    ]

    return any(p in q for p in patterns)


# ======================================================
# COMPARISON DETECTION
# ======================================================

def has_comparison(q: str):

    patterns = [
        " vs ",
        " versus ",
        "compare",
        "comparison"
    ]

    if any(p in q for p in patterns):
        return True

    if re.search(r"\bor\b.*[\+\-]?\d", q):
        return True

    return False


# ======================================================
# DEPENDENCY DETECTION
# ======================================================

def asks_dependency(q: str):

    dependency_patterns = [
        "affect",
        "influence",
        "impact",
        "effect"
    ]

    if any(p in q for p in dependency_patterns):
        return True

    if re.search(r"how does .* change", q):
        return True

    return False


# ======================================================
# DELTA DETECTION
# ======================================================

def asks_delta_reasoning(q: str):

    patterns = [
        "change from",
        "goes from",
        "from",
        "to"
    ]

    return any(p in q for p in patterns)


# ======================================================
# BASELINE REFERENCES
# ======================================================

def references_baseline(q: str):

    baseline_patterns = [
        "baseline",
        "current",
        "present",
        "today"
    ]

    return any(p in q for p in baseline_patterns)


# ======================================================
# ENM DETECTION
# ======================================================

def asks_enm(q: str):

    patterns = [
        "habitat",
        "suitability",
        "species distribution",
        "ecological niche"
    ]

    return any(p in q for p in patterns)


# ======================================================
# ROUTER
# ======================================================

def route_question(question: str):

    q = normalize(question)

    log_section("ROUTER V35 (RISK TARGET FIX)")
    log_question(question)

    # ==================================================
    # HARD RULES
    # ==================================================

    if is_data_query(q):

        log_route("DATA (hard rule)")

        return {"type": "data"}

    # ==================================================
    # PARSER
    # ==================================================

    parsed = parse_features(
        question,
        return_metadata=True
    )

    scenario_detected = parsed["scenario_detected"]

    num_modified = parsed["num_modified_features"]

    range_detected = parsed["range_detected"]

    # ==================================================
    # SEMANTICS
    # ==================================================

    target = detect_target(q)

    comparison_detected = has_comparison(q)

    dependency_detected = asks_dependency(q)

    driver_analysis = asks_driver_analysis(q)

    delta_reasoning = asks_delta_reasoning(q)

    risk_estimation = asks_risk_estimation(q)

    baseline_reference = references_baseline(q)

    enm_detected = asks_enm(q)

    # ==================================================
    # SCORES
    # ==================================================

    scores = {
        "assessment": 0,
        "dependency": 0,
        "delta": 0,
        "comparison": 0,
        "importance": 0,
        "drivers": 0,
        "enm": 0
    }

    # ==================================================
    # LEVEL 1 — DOMINANT STRUCTURES
    # ==================================================

    # --------------------------------------------------
    # COMPARISON
    # --------------------------------------------------

    if comparison_detected:

        scores["comparison"] += 400

    # --------------------------------------------------
    # DELTA
    # --------------------------------------------------

    if (
        range_detected
        and not baseline_reference
        and target == "risk"
    ):

        scores["delta"] += 350

    # --------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------

    if (
        scenario_detected
        and risk_estimation
    ):

        scores["assessment"] += 300

    # --------------------------------------------------
    # ENM
    # --------------------------------------------------

    if enm_detected:

        scores["enm"] += 300

    # ==================================================
    # LEVEL 2 — CONTEXTUAL SEMANTICS
    # ==================================================

    # --------------------------------------------------
    # DEPENDENCY
    # --------------------------------------------------

    if (
        dependency_detected
        and target != "risk"
    ):

        scores["dependency"] += 180

    # --------------------------------------------------
    # DRIVER FAMILY
    # --------------------------------------------------

    if driver_analysis:

        if target == "risk":

            scores["importance"] += 240

        elif target in ["variable", "ecosystem"]:

            scores["drivers"] += 240

    # --------------------------------------------------
    # ASSESSMENT CONTEXT
    # --------------------------------------------------

    if target == "risk":

        scores["assessment"] += 60

    if scenario_detected and num_modified > 1:

        scores["assessment"] += 40

    # ==================================================
    # LEVEL 3 — DELTA TRAJECTORY
    # ==================================================

    if (
        delta_reasoning
        and range_detected
        and not baseline_reference
        and target == "risk"
    ):

        scores["delta"] += 120

    # ==================================================
    # LEVEL 4 — CONFLICT RESOLUTION
    # ==================================================

    # --------------------------------------------------
    # COMPARISON DOMINATES
    # --------------------------------------------------

    if comparison_detected:

        scores["comparison"] += 100

    # --------------------------------------------------
    # DRIVER ANALYSIS REDUCES ASSESSMENT
    # --------------------------------------------------

    if driver_analysis:

        scores["assessment"] -= 60

    # --------------------------------------------------
    # TRUE DELTA SHOULD REDUCE ASSESSMENT
    # --------------------------------------------------

    if (
        range_detected
        and not baseline_reference
        and target == "risk"
    ):

        scores["assessment"] -= 120

    # ==================================================
    # DEBUG
    # ==================================================

    print("---- ROUTER SEMANTICS ----")

    print("scenario_detected:", scenario_detected)
    print("num_modified:", num_modified)
    print("range_detected:", range_detected)
    print("baseline_reference:", baseline_reference)
    print("target:", target)
    print("comparison_detected:", comparison_detected)
    print("dependency_detected:", dependency_detected)
    print("driver_analysis:", driver_analysis)
    print("risk_estimation:", risk_estimation)

    print("--------------------------")

    print("---- SCORE BREAKDOWN ----")

    for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True):

        print(f"{k}: {v}")

    print("-------------------------")

    # ==================================================
    # FINAL SELECTION
    # ==================================================

    best = max(scores, key=scores.get)

    log_route(f"{best.upper()} (score={scores[best]})")

    return {"type": best}


# ======================================================
# LEGACY
# ======================================================

def explain_with_shap(*args, **kwargs):
    return None