# -*- coding: utf-8 -*-

import os

# ======================================================
# FAKE MODEL (COHERENT + DEBUGGABLE)
# ======================================================

FEATURE_WEIGHTS = {
    "Change in average temperature compared to a recent past": 0.3,
    "Cumulative change in precipitation compared to a recent past": -0.25,
    "Relative change in the potential evapotranspiration compared to a recent past": 0.2,
    "Density of tree cover": -0.15,
    "Number of species potentially living in the cell": -0.2,
    "Presence of grassland": -0.1,
}


def _normalize_value(v):
    try:
        return float(v)
    except:
        return 0.0


def explain_with_shap(features: dict) -> dict:

    # -------------------------------
    # SCORE COMPUTATION
    # -------------------------------

    score = 0.5  # baseline

    contributions = []

    for fname, weight in FEATURE_WEIGHTS.items():
        value = _normalize_value(features.get(fname, 0))

        impact = value * weight

        score += impact

        contributions.append({
            "feature": fname,
            "impact": round(impact, 4)
        })

    # clamp score
    score = max(0, min(1, score))

    # -------------------------------
    # SORT FEATURES (SHAP-like)
    # -------------------------------

    contributions_sorted = sorted(
        contributions,
        key=lambda x: abs(x["impact"]),
        reverse=True
    )

    # -------------------------------
    # RISK LEVEL
    # -------------------------------

    if score < 0.33:
        level = "Low Risk"
    elif score < 0.66:
        level = "Medium Risk"
    else:
        level = "High Risk"

    return {
        "risk_score": round(score, 3),
        "risk_level": level,
        "top_features": contributions_sorted[:5]
    }


# ======================================================
# SPECIES
# ======================================================

def load_species_names():
    base_path = "/app/enm/presence"
    species = set()

    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.startswith("Presence_") and f.endswith(".csv"):
                name = f.replace("Presence_", "").replace(".csv", "")
                name = name.replace("_", " ").lower()
                species.add(name)

    return species


SPECIES_NAMES = load_species_names()


# ======================================================
# NORMALIZATION
# ======================================================

def normalize(q: str) -> str:
    return q.lower().strip()


# ======================================================
# CHAT
# ======================================================

def is_chat(q: str):
    patterns = [
        "what are you", "who are you",
        "are you", "can you",
        "what can you do",
        "help me", "tell me",
        "explain this system",
        "what is going on"
    ]
    return any(p in q for p in patterns)


def is_greeting(q: str):
    return q in ["hi", "hello", "hey"]


def is_gibberish(q: str):
    words = q.split()

    if len(words) <= 2:
        return True

    scientific_words = [
        "temperature", "precipitation", "biodiversity",
        "ecosystem", "risk", "habitat", "species"
    ]

    if any(w in q for w in scientific_words):
        return False

    if not any(w in ["what", "how", "why", "which", "is", "are"] for w in words):
        return True

    return False


# ======================================================
# TASK DETECTORS
# ======================================================

def is_enm(q: str):
    return (
        "habitat" in q or
        "suitability" in q or
        any(s in q for s in SPECIES_NAMES)
    )


def is_comparison(q: str):
    return (
        "compare" in q or
        "vs" in q or
        "versus" in q or
        ("which" in q and "riskier" in q) or
        "higher" in q or
        "lower" in q
    )


def is_delta(q: str):
    return (
        ("from" in q and "to" in q) or
        ("goes from" in q)
    )


def is_importance(q: str):
    return (
        "most" in q or
        "top" in q or
        "influential" in q or
        "important" in q
    )


def is_drivers(q: str):
    return (
        "drivers of" in q or
        "what drives" in q or
        "factors driving" in q or
        "drive" in q
    )


def is_dependency(q: str):
    return (
        "how does" in q or
        "effect of" in q or
        "affect" in q or
        "influence" in q
    )


# ======================================================
# ROUTER (NON TOCCATO)
# ======================================================

from utils.logger import log_section, log_question, log_route


def route_question(question: str):

    q = normalize(question)

    log_section("ROUTER v6_5")
    log_question(question)

    # 1. CHAT
    if is_chat(q) or is_greeting(q) or is_gibberish(q):
        log_route("CHAT")
        return {"type": "chat"}

    # 2. ENM
    if is_enm(q):
        log_route("ENM")
        return {"type": "enm"}

    # 3. COMPARISON
    if is_comparison(q):
        log_route("COMPARISON")
        return {"type": "comparison"}

    # 4. DELTA
    if is_delta(q):
        log_route("DELTA")
        return {"type": "delta"}

    # 🔥 5. RISK OVERRIDE
    if "risk" in q:
        if is_importance(q) or "driving" in q:
            log_route("IMPORTANCE (risk override)")
            return {"type": "importance"}

        log_route("ASSESSMENT (risk override)")
        return {"type": "assessment"}

    # 🔥 6. DRIVERS PRIORITY FIX
    if "drivers of" in q:
        log_route("DRIVERS (explicit)")
        return {"type": "drivers"}

    # 🔥 7. CONDITIONAL DRIVERS → IMPORTANCE
    if "drivers" in q and ("if" in q or "when" in q):
        log_route("IMPORTANCE (conditional drivers)")
        return {"type": "importance"}

    # 8. IMPORTANCE
    if is_importance(q):
        log_route("IMPORTANCE")
        return {"type": "importance"}

    # 9. DRIVERS
    if is_drivers(q):
        log_route("DRIVERS")
        return {"type": "drivers"}

    # 10. DEPENDENCY
    if is_dependency(q):
        log_route("DEPENDENCY")
        return {"type": "dependency"}

    # DEFAULT
    log_route("DEFAULT: ASSESSMENT")
    return {"type": "assessment"}