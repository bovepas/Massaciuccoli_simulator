# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v16 (driver-aligned + grounded)

✔ Uses SHAP drivers explicitly
✔ Forces grounding in KB context
✔ Aligns explanation with model outputs
✔ Clean and stable for demo
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

    # non distruggere punteggiatura
    text = re.sub(r"\s+", " ", text)

    text = text.replace("Climatedriven", "Climate-driven")

    sentences = re.split(r'(?<=[.!?])\s+', text)

    if not sentences:
        return None

    # max 4 frasi (leggermente più permissivo)
    cleaned = " ".join(sentences[:4]).strip()

    return cleaned


# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(drivers, mode):

    if not drivers:
        return "No dominant drivers were identified."

    variables = ", ".join(drivers)

    return (
        f"In the Massaciuccoli lake basin, {variables} influence ecosystem risk "
        f"through interactions affecting hydrological dynamics, nutrient cycles, "
        f"and ecosystem resilience."
    )


# ======================================================
# MAIN FUNCTION
# ======================================================

def generate_importance_explanation(drivers, mode="absolute"):

    print("\n[RAG-IMPORTANCE v16] START\n")

    if not drivers:
        return "No dominant drivers were identified in this scenario."

    # ======================================================
    # 🔥 DRIVER STRING (SHAP → RAG)
    # ======================================================

    driver_text = ", ".join(drivers[:5])  # top 5 max

    print("[DEBUG] Drivers passed to RAG:", driver_text)

    # ======================================================
    # 🔥 QUERY DINAMICA (driver-aware)
    # ======================================================

    rag_query = (
        f"{driver_text} ecosystem risk lake basin hydrology nutrient loading "
        f"climate biodiversity Massaciuccoli ecosystem dynamics"
    )

    print("[DEBUG] RAG query:", rag_query)

    # ======================================================
    # 🔥 PROMPT (FIXED: NO LIST OUTPUT)
    # ======================================================

    prompt = f"""
You are an environmental scientist analyzing a real lake ecosystem.

TASK:
Explain how the following environmental drivers jointly influence ecosystem risk:
{driver_text}

STRICT REQUIREMENTS:
- You MUST explicitly refer to the listed drivers
- You MUST use information from the provided context
- You MUST explain WHY these drivers are important (not just describe the system)
- You MUST explicitly mention at least ONE of:
  • hydrological dynamics
  • nutrient loading
  • water quality
  • anthropogenic pressures
  • climate-driven changes

CONTEXT ANCHORING:
- You MUST explicitly refer to the Massaciuccoli lake basin
- The explanation must feel grounded in a real ecosystem

CAUSAL STRUCTURE:
- You MUST describe a causal chain
  (e.g., temperature → hydrology → water quality → species → ecosystem risk)
- Connect the drivers within a single mechanism
- Do NOT invent causal relationships between drivers unless supported by the context

OUTPUT FORMAT:
- Write a single coherent paragraph
- Do NOT list drivers one by one
- Integrate the drivers into a unified explanation

STYLE:
- 3–5 sentences
- Scientific but concrete
- Avoid generic explanations

DO NOT:
- Ignore the listed drivers
- Give abstract ecological theory
- Mention models or SHAP

---

Now explain how these drivers increase ecosystem risk using ONLY the context.
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
            print("[RAG-IMPORTANCE v16] END\n")
            return cleaned

        return fallback_explanation(drivers, mode)

    except Exception as e:

        print("\n🔥 RAG-IMPORTANCE ERROR:")
        print(e)

        return fallback_explanation(drivers, mode)