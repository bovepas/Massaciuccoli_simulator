# -*- coding: utf-8 -*-

"""
RAG Assessment — v4 (validated + structured + demo-ready)

✔ Uses centralized LLM client
✔ Strong output control
✔ Scientific + readable tone
✔ Robust fallback
✔ Consistent demo quality
"""

from tools.llm_client import call_llm


# ======================================================
# FALLBACK (🔥 IMPROVED)
# ======================================================

def fallback_explanation(features):

    if not features:
        return "No environmental factors were provided."

    parts = []

    for name, value in features:

        name_low = name.lower()

        if "temperature" in name_low:
            parts.append("temperature contributes to ecosystem stress")

        elif "precipitation" in name_low:
            if value < 0:
                parts.append("reduced precipitation is associated with water scarcity")
            else:
                parts.append("higher precipitation is associated with improved water availability")

        elif "evapotranspiration" in name_low:
            parts.append("evapotranspiration influences water balance")

        elif "tree cover" in name_low:
            parts.append("tree cover contributes to ecosystem stability")

        elif "species" in name_low:
            parts.append("biodiversity affects ecosystem resilience")

        elif "phenology" in name_low:
            parts.append("ecosystem productivity influences system functioning")

        elif "grassland" in name_low:
            parts.append("grassland presence affects habitat conditions")

    if not parts:
        return "The system shows environmental conditions influencing ecosystem risk."

    return ". ".join(parts[:3]) + "."


# ======================================================
# PROMPT (🔥 MUCH STRONGER)
# ======================================================

def build_prompt(features):

    feature_text = "\n".join([
        f"- {name}: {value}"
        for name, value in features
    ])

    return f"""
You are an environmental scientist.

INPUT VARIABLES:
{feature_text}

TASK:
Provide a short ecological interpretation of ecosystem risk.

RULES:
- Use ONLY the variables listed above
- Do NOT introduce new variables or concepts
- Do NOT speculate beyond the data
- Keep explanation realistic and grounded
- Maximum 2 sentences
- Clear and scientific tone

STYLE:
- Explain how the variables relate to ecosystem stress, stability, or vulnerability
- Avoid repetition
- Avoid generic phrases

OUTPUT:
"""


# ======================================================
# VALIDATION (🔥 NEW)
# ======================================================

def is_valid(text):

    if not text:
        return False

    if len(text) < 30:
        return False

    if "Interpretation not available" in text:
        return False

    return True


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text):

    text = text.strip()

    text = text.replace("\n", " ")
    text = " ".join(text.split())

    return text


# ======================================================
# MAIN
# ======================================================

def generate_assessment_explanation(features):

    print("\n[RAG-ASSESSMENT v4] START")

    if not features:
        return "No environmental factors were provided."

    try:

        prompt = build_prompt(features)

        response = call_llm(prompt)

        print("[RAG-ASSESSMENT RAW]:", response)

        if not is_valid(response):
            return fallback_explanation(features)

        cleaned = clean_output(response)

        print("[RAG-ASSESSMENT FINAL]:", cleaned)
        print("[RAG-ASSESSMENT v4] END\n")

        return cleaned

    except Exception as e:

        print("\n🔥 RAG-ASSESSMENT ERROR:")
        print(e)

        return fallback_explanation(features)