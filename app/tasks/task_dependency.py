# -*- coding: utf-8 -*-

"""
Dependency Task — v11 (STRUCTURED + RAG ALIGNED + FULL FALLBACK)

✔ Fix target None
✔ Fix source None
✔ No change to parser
✔ Safe + robust
"""

from utils.dependency_parser import parse_dependency
from knowledge.rag_dependency import generate_dependency_explanation


# ======================================================
# HUMAN READABLE FEATURE
# ======================================================

def humanize_feature(name: str) -> str:

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
# 🔥 SOURCE FALLBACK (NEW)
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
# MAIN
# ======================================================

def handle_dependency(question, route):

    print("\n========== DEPENDENCY TASK START ==========")
    print("# USING STRUCTURED DEPENDENCY TASK")

    parsed = parse_dependency(question)

    source = parsed.get("source")
    target = parsed.get("target")
    delta = parsed.get("delta")

    # ======================================================
    # 🔥 FIX TARGET
    # ======================================================

    if target is None:
        target = extract_abstract_target(question)

    # ======================================================
    # 🔥 FIX SOURCE
    # ======================================================

    if source is None:
        source = extract_source_from_question(question)

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Delta:", delta)

    # ======================================================
    # RAG
    # ======================================================

    explanation = generate_dependency_explanation(
        question=question,
        source=source,
        target=target
    )

    # ======================================================
    # OUTPUT
    # ======================================================

    variables = [humanize_feature(source)] if source else []

    return {
        "summary": "Conceptual dependency analysis",
        "data": {},
        "drivers": variables,
        "interpretation": explanation
    }