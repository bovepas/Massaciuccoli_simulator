# -*- coding: utf-8 -*-

"""
Dependency Task — v7 (clean conceptual mode)

✔ Fully isolated from other tasks
✔ Pure RAG-based reasoning
✔ No SHAP
✔ No importance reuse
✔ Clean output (no fake drivers)
"""

from utils.dependency_parser import parse_dependency
from knowledge.rag_dependency import generate_dependency_explanation


# ======================================================
# 🔥 HUMAN READABLE FEATURE
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
    print("🔥 USING NEW DEPENDENCY TASK")

    parsed = parse_dependency(question)

    source = parsed.get("source")
    target = parsed.get("target")
    delta = parsed.get("delta")

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Delta:", delta)

    # ======================================================
    # 🔥 PURE RAG EXPLANATION
    # ======================================================

    explanation = generate_dependency_explanation(question)

    # ======================================================
    # OUTPUT LOGIC (clean)
    # ======================================================

    # 👉 human-readable variable (non tecnico)
    variables = [humanize_feature(source)] if source else []

    return {
        "summary": "Conceptual dependency analysis",
        "data": {},
        "drivers": variables,   # solo per riferimento, non “drivers reali”
        "interpretation": explanation
    }