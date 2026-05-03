"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v10 (template-guided, strict)
"""

from knowledge.rag_pipeline import generate_answer
import re


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text: str):

    text = text.strip()

    # remove unwanted phrases
    text = re.sub(r"here is.*?:", "", text, flags=re.IGNORECASE)

    # remove markdown / bullets
    text = re.sub(r"[*•\-]+", "", text)

    # remove bold
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    # normalize spaces
    text = re.sub(r"\s+", " ", text)

    # keep ONLY first sentence
    sentences = [s.strip() for s in text.split(".") if s.strip()]

    if not sentences:
        return "These variables influence ecosystem risk."

    return sentences[0] + "."


# ======================================================
# MAIN
# ======================================================

def generate_importance_explanation(drivers, mode="absolute"):

    print("\n[RAG-IMPORTANCE v10] START\n")

    if not drivers:
        return "No dominant drivers were identified in this scenario."

    drivers_text = ", ".join(drivers)

    # --------------------------------------------------
    # HARD TEMPLATE PROMPT
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

    result = generate_answer(
        question="Fill template.",
        extra_prompt=prompt
    )

    print("\n[RAG-IMPORTANCE] Raw output:")
    print(result)

    cleaned = clean_output(result)

    print("\n[RAG-IMPORTANCE] Cleaned output:")
    print(cleaned)

    print("[RAG-IMPORTANCE v10] END\n")

    return cleaned