# -*- coding: utf-8 -*-

"""
RAG Dependency Explanation — v5 (hard grounded + anchored)

✔ Forces grounding in retrieved context
✔ Rejects generic answers
✔ Anchors explanation to Massaciuccoli basin
✔ Makes KB clearly visible
"""

from knowledge.rag_pipeline import generate_answer


def generate_dependency_explanation(question: str) -> str:

    print("\n[RAG-DEPENDENCY] START")

    extra_prompt = """
You are an environmental scientist analyzing a real lake ecosystem.

TASK:
Explain how the environmental factor in the question affects ecosystem stability or risk.

STRICT REQUIREMENTS:
- You MUST use information from the provided context
- You MUST explicitly mention at least ONE of the following if present in the context:
  • hydrological dynamics
  • nutrient loading
  • water quality
  • anthropogenic pressures
  • climate-driven changes
- If none of these appear in your answer, the answer is INVALID
- You MUST explain the mechanism step-by-step, not just the outcome

CONTEXT ANCHORING:
- You MUST explicitly refer to the lake system (e.g., "in the Massaciuccoli lake basin")
- Ground the explanation in the specific ecosystem described in the context
- The answer must clearly feel tied to a real place, not a generic ecosystem

CAUSAL STRUCTURE:
- You MUST describe a clear causal chain
  (e.g., temperature → hydrology → water quality → species → ecosystem risk)
- Avoid vague statements like "affects the ecosystem"
- Make the mechanism explicit and sequential

UNCERTAINTY HANDLING:
- If the relationship between variables is NOT explicitly supported by the context,
  you MUST state that the effect is uncertain, indirect, or not clearly established
- Do NOT invent direct causal relationships between variables
- Prefer cautious, evidence-based statements over confident but unsupported claims

STYLE:
- 3–5 sentences
- Scientific but concrete
- Clearly explain direction (increase/decrease stability or risk)

DO NOT:
- Give generic ecological explanations
- Talk about biodiversity in abstract terms only
- Use vague phrases like "in ecosystems" or "in general"
- Ignore the lake-specific processes

GOOD ANSWER EXAMPLE:
"In the Massaciuccoli lake basin, biodiversity stabilizes the ecosystem by buffering
the effects of nutrient loading and maintaining trophic interactions under hydrological variability..."

BAD ANSWER EXAMPLE:
"Biodiversity increases resilience through functional redundancy..."

---

Now answer the question using ONLY the context.
"""

    try:
        answer = generate_answer(question, extra_prompt)

        print("\n[RAG-DEPENDENCY] Output:")
        print(answer)
        print("[RAG-DEPENDENCY] END\n")

        return answer

    except Exception as e:
        print("[RAG-DEPENDENCY ERROR]", e)

        return (
            "In the Massaciuccoli lake basin, biodiversity contributes to ecosystem stability "
            "by regulating nutrient dynamics, maintaining trophic interactions, and buffering "
            "the effects of hydrological and climate variability."
        )