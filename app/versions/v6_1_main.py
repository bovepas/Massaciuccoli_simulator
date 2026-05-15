# -*- coding: utf-8 -*-

import re
from utils.logger import log_section, log_question, log_route


def normalize(q: str) -> str:
    return q.lower().strip()


VARIABLE_KEYWORDS = [
    "temperature",
    "precipitation",
    "biodiversity",
    "tree cover",
    "grassland",
    "evapotranspiration",
    "productivity"
]


# ======================================================
# 🆕 DATA DETECTION (NUOVO)
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


def is_data_query(q: str) -> bool:
    return any(k in q for k in DATA_KEYWORDS)


# ======================================================
# SEMANTICS
# ======================================================

def detect_target(q: str):
    if "risk" in q or "ecosystem" in q:
        return "risk"
    if any(v in q for v in VARIABLE_KEYWORDS):
        return "variable"
    return "unknown"


def count_variables(q: str):
    return sum(1 for v in VARIABLE_KEYWORDS if v in q)


def parse_semantics(q: str):
    return {
        "target": detect_target(q),
        "num_variables": count_variables(q),
        "has_range": bool(re.search(r"\bfrom\b.*\bto\b", q)),
        "has_delta_change": bool(
            re.search(r"\b(increase|decrease)\b", q) or
            re.search(r"[\+\-]\s*\d", q)
        ),
        "has_comparison": (
            any(k in q for k in [" vs ", " versus ", "compare"]) or
            re.search(r"\bor\b.*\d", q)
        ),
        "has_condition": any(k in q for k in ["if", "given", "when"]),
        "asks_influence": any(k in q for k in ["affect", "influence", "effect", "impact"]),
        "asks_importance": any(k in q for k in ["most", "top", "important", "influential"]),
        "asks_drivers": any(k in q for k in ["drivers", "drive"]),
        "mentions_habitat": any(k in q for k in ["habitat", "suitability"]),
        "asks_what_happens": "what happens" in q,
        "mentions_multiple": " and " in q or "interact" in q or "combined" in q or "together" in q or "also" in q
    }


# ======================================================
# ROUTER
# ======================================================

def route_question(question: str):

    q = normalize(question)

    log_section("ROUTER V28 FINAL (DATA SAFE)")
    log_question(question)

    # ==================================================
    # 🆕 HARD RULE: DATA FIRST
    # ==================================================

    if is_data_query(q):
        log_route("DATA (hard rule)")
        return {"type": "data"}

    p = parse_semantics(q)

    scores = {
        "assessment": 0,
        "dependency": 0,
        "delta": 0,
        "comparison": 0,
        "importance": 0,
        "drivers": 0,
        "enm": 0
    }

    # =============================
    # HARD RULES
    # =============================

    if p["mentions_habitat"]:
        return {"type": "enm"}

    if p["has_comparison"]:
        return {"type": "comparison"}

    # =============================
    # DELTA
    # =============================

    if p["has_range"]:
        scores["delta"] += 100

    if p["asks_what_happens"]:
        scores["delta"] += 80

    if p["has_delta_change"] and p["num_variables"] == 1:
        scores["delta"] += 40

    if p["target"] == "risk" and p["has_condition"]:
        scores["delta"] += 40

    # =============================
    # INTERACTION → ASSESSMENT
    # =============================

    if p["asks_influence"] and p["mentions_multiple"] and p["target"] == "risk":
        scores["assessment"] += 100

    # =============================
    # DEPENDENCY
    # =============================

    if p["asks_influence"]:
        scores["dependency"] += 50

    if p["target"] == "variable" and p["has_condition"]:
        scores["dependency"] += 30

    # =============================
    # IMPORTANCE
    # =============================

    if "which factors" in q or "which variables" in q or "main factors" in q:
        scores["importance"] += 80

    if p["asks_importance"]:
        scores["importance"] += 60

    if p["asks_drivers"] and p["has_condition"]:
        scores["importance"] += 90

    if q.startswith("what drives"):
        if p["target"] == "risk":
            scores["importance"] += 80
        else:
            scores["drivers"] += 80

    # =============================
    # DRIVERS
    # =============================

    if re.search(r"top\s*\d*\s*drivers", q):
        scores["drivers"] += 100

    elif re.search(r"which .* drive", q):
        scores["drivers"] += 90

    elif "drivers of" in q:
        scores["drivers"] += 80

    elif p["asks_drivers"]:
        scores["drivers"] += 40

    # =============================
    # ASSESSMENT
    # =============================

    if p["target"] == "risk":
        scores["assessment"] += 40

    # =============================
    # DEBUG
    # =============================

    print("---- SCORE BREAKDOWN ----")
    for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True):
        print(f"{k}: {v}")
    print("-------------------------")

    # =============================
    # PICK BEST
    # =============================

    best = max(scores, key=scores.get)

    log_route(f"{best.upper()} (score={scores[best]})")

    return {"type": best}


def explain_with_shap(*args, **kwargs):
    return None