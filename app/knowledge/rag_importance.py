# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v11 (robust + fallback)
"""

from knowledge.rag_pipeline import generate_answer
import re


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text: str):

    if not text:
        return None

    text = text.strip()

    text = re.sub(r"here is.*?:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[*•\-]+", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\s+", " ", text)

    sentences = [s.strip() for s in text.split(".") if s.strip()]

    if not sentences:
        return None

    return sentences[0] + "."


# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(drivers, mode):

    if not drivers:
        return "No dominant drivers were identified."

    variables = ", ".join(drivers)

    if mode == "delta":
        return f"{variables} drive changes in ecosystem risk by increasing or decreasing stress, instability, and vulnerability."
    else:
        return f"{variables} drive ecosystem risk through stress, instability, and vulnerability."


# ======================================================
# MAIN
# ======================================================

def generate_importance_explanation(drivers, mode="absolute"):

    print("\n[RAG-IMPORTANCE v11] START\n")

    if not drivers:
        return "No dominant drivers were identified in this scenario."

    drivers_text = ", ".join(drivers)

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if mode == "delta":

        prompt = f"""
Fill this template EXACTLY.

TEMPLATE:
"<variables> drive changes in ecosystem risk by increasing or decreasing stress, instability, and vulnerability."

VARIABLES:
{drivers_text}

RULES:
- Replace <variables> with the list
- One sentence only
- Use ONLY: stress, instability, vulnerability
- Do NOT add explanations
- Do NOT add causes
- Do NOT add extra sentences
"""

    else:

        prompt = f"""
Fill this template EXACTLY.

TEMPLATE:
"<variables> drive ecosystem risk through stress, instability, and vulnerability."

VARIABLES:
{drivers_text}

RULES:
- Replace <variables> with the list
- One sentence only
- Use ONLY: stress, instability, vulnerability
- Do NOT add explanations
- Do NOT add causes
- Do NOT add extra sentences
"""

    # --------------------------------------------------
    # CALL MODEL
    # --------------------------------------------------

    try:

        result = generate_answer(
            question="Fill template.",
            extra_prompt=prompt
        )

        print("\n[RAG-IMPORTANCE] Raw output:")
        print(result)

        cleaned = clean_output(result)

        if cleaned:
            print("\n[RAG-IMPORTANCE] Cleaned output:")
            print(cleaned)
            print("[RAG-IMPORTANCE v11] END\n")
            return cleaned

        # 🔥 fallback if cleaning failed
        return fallback_explanation(drivers, mode)

    except Exception as e:

        print("\n🔥 RAG-IMPORTANCE ERROR:")
        print(e)

        return fallback_explanation(drivers, mode)