# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG ENM — Species Explanation Layer v2 (robust + demo-ready)

✔ Uses centralized RAG pipeline
✔ Strong fallback (scientific)
✔ Cleaner output
"""

from knowledge.rag_pipeline import generate_answer


# ======================================================
# FALLBACK (🔥 IMPORTANT FOR DEMO)
# ======================================================

def fallback_explanation(species, drivers):

    if not drivers:
        return f"Habitat suitability for {species} depends on environmental conditions represented in the model."

    driver_text = ", ".join(drivers[:3])

    return (
        f"Habitat suitability for {species} is influenced by environmental variables such as {driver_text}, "
        f"which define the ecological conditions supporting species presence."
    )


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
    # PROMPT (IMPROVED)
    # --------------------------------------------------

    extra_prompt = f"""
You are an ecological modeler.

SPECIES:
{species}

ENVIRONMENTAL DRIVERS:
{driver_text}

TASK:
Explain how these variables influence habitat suitability for the species.

RULES:
- Use ecological reasoning (habitat preference, environmental constraints)
- Link variables to species presence
- Be realistic and scientifically plausible
- Use 2–3 sentences maximum
- No lists, no formatting
- Do NOT introduce variables not listed
"""

    # --------------------------------------------------
    # CALL RAG
    # --------------------------------------------------

    try:

        answer = generate_answer(
            question=question,
            extra_prompt=extra_prompt
        )

        print("\n[RAG-ENM] OUTPUT:")
        print(answer)

        # 🔥 fallback if weak output
        if not answer or "unavailable" in answer.lower():
            return fallback_explanation(species, drivers)

        print("[RAG-ENM] END\n")
        return answer

    except Exception as e:

        print("\n🔥 RAG-ENM ERROR:")
        print(e)

        return fallback_explanation(species, drivers)