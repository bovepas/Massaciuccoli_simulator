# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v19 (QUERY-AWARE + FIX OVERFITTING)

# FIX:
# - Now uses user question
# - Handles increase / decrease / stability
# - Prevents semantic overfitting
# - Keeps clean RAG structure
"""

import re
from knowledge.rag_pipeline import generate_answer


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text: str):

    if not text:
        return None

    text = text.strip()
    text = re.sub(r"\s+", " ", text)

    sentences = re.split(r'(?<=[.!?])\s+', text)

    if not sentences:
        return None

    return " ".join(sentences[:4]).strip()


# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(drivers, mode):

    if not drivers:
        return "No dominant drivers were identified."

    variables = ", ".join([d["name"] for d in drivers[:5]])

    return (
        f"In the Massaciuccoli lake basin, {variables} influence ecosystem risk "
        f"through interactions affecting hydrological dynamics, nutrient cycles, "
        f"and ecosystem resilience."
    )


# ======================================================
# MAIN FUNCTION (🔥 FIXED)
# ======================================================

def generate_importance_explanation(drivers, question, mode="absolute"):

    print("\n[RAG-IMPORTANCE v19] START\n")

    if not drivers:
        return "No dominant drivers were identified in this scenario."

    # ======================================================
    # 🔥 UNDERSTAND USER INTENT (CORE FIX)
    # ======================================================

    q = question.lower()

    focus = "all"

    if any(k in q for k in ["increase", "higher", "raise", "drives risk"]):
        focus = "increase"

    elif any(k in q for k in ["decrease", "reduce", "mitigate", "lower"]):
        focus = "decrease"

    elif "stability" in q:
        focus = "stability"

    print(f"[DEBUG] Detected focus: {focus}")

    # ======================================================
    # DRIVER NAMES (for retrieval)
    # ======================================================

    driver_names = [d["name"] for d in drivers[:5]]
    driver_text = ", ".join(driver_names)

    print("[DEBUG] Driver names:", driver_names)

    # ======================================================
    # 🔥 FILTER DRIVERS BASED ON QUESTION
    # ======================================================

    if focus == "increase":
        increase = [d for d in drivers if d["impact"] > 0][:5]
        decrease = []

    elif focus == "decrease":
        increase = []
        decrease = [d for d in drivers if d["impact"] < 0][:5]

    elif focus == "stability":
        # stability = inverse of risk
        increase = [d for d in drivers if d["impact"] < 0][:5]
        decrease = [d for d in drivers if d["impact"] > 0][:5]

    else:
        increase = [d for d in drivers if d["impact"] > 0][:5]
        decrease = [d for d in drivers if d["impact"] < 0][:5]

    # ======================================================
    # BUILD TEXT BLOCKS
    # ======================================================

    increase_text = "\n".join([
        f"- An increase in {d['name']} leads to higher ecosystem risk"
        for d in increase
    ]) or "- None"

    decrease_text = "\n".join([
        f"- An increase in {d['name']} leads to lower ecosystem risk"
        for d in decrease
    ]) or "- None"

    # ======================================================
    # 🔥 ADAPT PROMPT BASED ON FOCUS
    # ======================================================

    if focus == "increase":

        impact_text = f"""
DRIVERS THAT INCREASE RISK:
{increase_text}
"""

    elif focus == "decrease":

        impact_text = f"""
DRIVERS THAT REDUCE RISK:
{decrease_text}
"""

    else:

        impact_text = f"""
DRIVERS THAT INCREASE RISK:
{increase_text}

DRIVERS THAT REDUCE RISK:
{decrease_text}
"""

    print("[DEBUG] Impact structure:\n", impact_text)

    # ======================================================
    # RAG QUERY
    # ======================================================

    rag_query = (
        f"{driver_text} ecosystem risk lake basin hydrology nutrient loading "
        f"climate biodiversity Massaciuccoli ecosystem dynamics"
    )

    print("[DEBUG] RAG query:", rag_query)

    # ======================================================
    # PROMPT
    # ======================================================

    prompt = f"""
You are an environmental scientist analyzing a real lake ecosystem.

TASK:
Explain how the following environmental drivers influence ecosystem risk.

{impact_text}

STRICT REQUIREMENTS:
- You MUST respect the direction of influence
- You MUST NOT introduce drivers not listed above
- You MUST explain WHY these drivers matter
- You MUST use information from the provided context

You MUST explicitly mention at least ONE of:
• hydrological dynamics
• nutrient loading
• water quality
• anthropogenic pressures
• climate-driven changes

CONTEXT ANCHORING:
- You MUST refer to the Massaciuccoli lake basin

OUTPUT:
- Single paragraph
- 3–5 sentences
- No bullet points

DO NOT:
- Treat all drivers equally
- Ignore the requested focus
- Invent relationships not supported by context

---

Now explain the system.
"""

    # ======================================================
    # CALL
    # ======================================================

    try:

        result = generate_answer(
            question=rag_query,
            extra_prompt=prompt
        )

        cleaned = clean_output(result)

        if cleaned:
            print("\n[RAG-IMPORTANCE] Output:")
            print(cleaned)
            print("[RAG-IMPORTANCE v19] END\n")
            return cleaned

        return fallback_explanation(drivers, mode)

    except Exception as e:

        print("\n# RAG-IMPORTANCE ERROR:")
        print(e)

        return fallback_explanation(drivers, mode)