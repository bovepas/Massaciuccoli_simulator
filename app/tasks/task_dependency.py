# -*- coding: utf-8 -*-

"""
Dependency Task — v13 (UX CLEAN + TEXT FIX)

✔ Fix double "on"
✔ Remove LLM-style intro
✔ Clean feature names in text
✔ No logic changes
"""

from utils.dependency_parser import parse_dependency
from knowledge.rag_dependency import generate_dependency_explanation


# ======================================================
# HUMAN READABLE FEATURE
# ======================================================

def humanize_feature(name: str):

    if not name:
        return ""

    name = name.lower()

    if "species" in name:
        return "Biodiversity"

    if "temperature" in name:
        return "Temperature"

    if "precipitation" in name:
        return "Precipitation"

    if "tree cover" in name:
        return "Vegetation (tree cover)"

    if "evapotranspiration" in name:
        return "Evapotranspiration"

    return name


# ======================================================
# ABSTRACT TARGET DETECTION
# ======================================================

ABSTRACT_KEYWORDS = {
    "water availability": "hydrological dynamics",
    "water": "hydrological dynamics",
    "water level": "hydrological dynamics",
    "nutrients": "nutrient loading",
    "productivity": "ecosystem productivity",
    "ecosystem": "ecosystem stability",
    "biodiversity": "biodiversity",
    "risk": "ecosystem risk"
}


def extract_abstract_target(question: str):

    q = question.lower()

    for k, v in ABSTRACT_KEYWORDS.items():
        if k in q:
            return v

    return "ecosystem stability"


# ======================================================
# SOURCE FALLBACK
# ======================================================

def extract_source_from_question(question: str):

    q = question.lower()

    if "evapotranspiration" in q:
        return "Relative change in the potential evapotranspiration compared to a recent past"

    if "temperature" in q:
        return "Change in average temperature compared to a recent past"

    if "precipitation" in q:
        return "Cumulative change in precipitation compared to a recent past"

    if "biodiversity" in q or "species" in q:
        return "Number of species potentially living in the cell"

    if "tree cover" in q:
        return "Density of tree cover"

    return None


# ======================================================
# CLEAN HELPERS
# ======================================================

def simplify(name: str):
    if not name:
        return ""
    name = name.lower()
    if "temperature" in name:
        return "temperature"
    if "precipitation" in name:
        return "precipitation"
    if "evapotranspiration" in name:
        return "evapotranspiration"
    return name


def simplify_text(text: str):

    if not text:
        return text

    replacements = {
        "Change in average temperature compared to a recent past": "temperature",
        "Cumulative change in precipitation compared to a recent past": "precipitation",
        "Relative change in the potential evapotranspiration compared to a recent past": "evapotranspiration",
        "Number of species potentially living in the cell": "biodiversity",
        "Density of tree cover": "tree cover"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


# ======================================================
# MAIN
# ======================================================

def handle_dependency(question, route):

    print("\n========== DEPENDENCY TASK START ==========")
    print("# USING STRUCTURED DEPENDENCY TASK")

    parsed = parse_dependency(question)

    source = parsed.get("source")
    target = parsed.get("target")
    target_raw = parsed.get("target_raw")
    delta = parsed.get("delta")

    if target is None:
        target = extract_abstract_target(question)

    if source is None:
        source = extract_source_from_question(question)

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Target raw:", target_raw)
    print("[DEBUG] Delta:", delta)

    explanation = generate_dependency_explanation(
        question=question,
        source=source,
        target=target
    )

    # 🔥 CLEAN TEXT
    explanation = simplify_text(explanation)

    # 🔥 REMOVE LLM INTRO
    if explanation.startswith("Here is"):
        explanation = explanation.split(":", 1)[-1].strip()

    # 🔥 CAPITALIZE
    if explanation:
        explanation = explanation[0].upper() + explanation[1:]

    variables = [humanize_feature(source)] if source else []

    human_target = target_raw if target_raw else simplify(target)

    # 🔥 FIX DOUBLE "on"
    if source:
        summary = f"Effect of {simplify(source).capitalize()} on {human_target}"
        summary = summary.replace("on on", "on")
    else:
        summary = "Conceptual dependency analysis"

    return {
        "summary": summary,
        "data": {},
        "drivers": variables,
        "interpretation": explanation
    }