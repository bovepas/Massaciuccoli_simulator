# -*- coding: utf-8 -*-

"""
RAG Assessment — v3 (LLM + fallback safe)

✔ Uses LLM for richer explanations
✔ Keeps deterministic fallback
✔ No breaking changes
"""

from tools.llm_client import call_llm


# ======================================================
# FALLBACK (OLD LOGIC)
# ======================================================

def fallback_explanation(features):

    if not features:
        return ""

    parts = []

    for name, value in features:

        name = name.lower()

        if "temperature" in name:
            parts.append("temperature increases ecosystem stress")

        elif "precipitation" in name:
            if value < 0:
                parts.append("reduced precipitation increases drought risk")
            else:
                parts.append("higher precipitation may support ecosystem stability")

        elif "evapotranspiration" in name:
            parts.append("evapotranspiration influences water balance")

        elif "tree cover" in name:
            parts.append("tree cover affects ecosystem resilience")

        elif "species" in name:
            parts.append("biodiversity influences ecosystem vulnerability")

        elif "phenology" in name:
            parts.append("ecosystem productivity affects nutrient dynamics")

        elif "grassland" in name:
            parts.append("grassland presence impacts habitat stability")

    return ". ".join(parts) + "."


# ======================================================
# PROMPT
# ======================================================

def build_prompt(features):

    feature_text = "\n".join([
        f"- {name}: {value}"
        for name, value in features
    ])

    return f"""
You are an environmental analyst.

INPUT FEATURES:
{feature_text}

TASK:
Provide a short ecological interpretation of the ecosystem risk.

RULES:
- Be concise (2–3 sentences)
- Focus only on provided variables
- No speculation beyond inputs
- Use scientific tone

OUTPUT:
"""


# ======================================================
# MAIN
# ======================================================

def generate_assessment_explanation(features):

    if not features:
        return ""

    try:

        prompt = build_prompt(features)

        response = call_llm(prompt)

        if response and "Interpretation not available" not in response:
            return response.strip()

        # fallback if LLM returns empty
        return fallback_explanation(features)

    except Exception as e:

        print("[RAG-ASSESSMENT ERROR]", e)

        return fallback_explanation(features)