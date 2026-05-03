"""
Massaciuccoli Digital Twin
RAG ENM — Species Explanation Layer
"""

from knowledge.rag_pipeline import generate_answer


# ======================================================
# MAIN
# ======================================================

def generate_enm_explanation(question, drivers, species):

    print("\n[RAG-ENM] START")

    # --------------------------------------------------
    # FORMAT DRIVERS
    # --------------------------------------------------

    driver_text = "\n".join([f"- {d}" for d in drivers])

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    extra_prompt = f"""
IMPORTANT:
You must explain habitat suitability using ecological reasoning grounded in the provided variables.

SPECIES:
{species}

DRIVERS:
{driver_text}

TASK:
Explain how these environmental variables influence habitat suitability for the species.

STRICT RULES:
- Focus on ecological interpretation (habitat preferences, environmental constraints)
- Use cause → effect logic
- You MAY use ecological concepts (unlike assessment/comparison)
- Do NOT invent variables not listed above
- Be concise (2–3 sentences)
- No lists, no formatting
"""

    # --------------------------------------------------
    # CALL RAG
    # --------------------------------------------------

    answer = generate_answer(
        question=question,
        extra_prompt=extra_prompt
    )

    print("\n[RAG-ENM] OUTPUT:")
    print(answer)
    print("[RAG-ENM] END\n")

    return answer