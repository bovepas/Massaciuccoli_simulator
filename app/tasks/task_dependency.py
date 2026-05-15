# -*- coding: utf-8 -*-

"""
Dependency Task — v9 (STRUCTURED + RAG ALIGNED)

# Passes structured source/target to RAG
# Cleaner reasoning
# Still fully decoupled
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

    return name


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

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Delta:", delta)

    # ======================================================
    # RAG (STRUCTURED)
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