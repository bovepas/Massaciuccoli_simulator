# -*- coding: utf-8 -*-

"""
RAG Dependency Explanation — v9 (robust + structured reasoning)

# Distinguishes feature→feature vs feature→risk
# Aligns retrieval with structured features
# No forced causal chains
# Handles uncertainty correctly
# Produces natural scientific explanations
# Fully grounded in retrieved context
"""

from knowledge.rag_pipeline import generate_answer


def generate_dependency_explanation(question: str, source=None, target=None) -> str:

    print("\n[RAG-DEPENDENCY v9] START")

    # ======================================================
    # CASE 1: FEATURE → FEATURE
    # ======================================================

    if target and target != "risk_score":

        extra_prompt = f"""
You are an environmental scientist analyzing a lake ecosystem.

TASK:
Explain how {source} influences {target}.

STRICT REQUIREMENTS:
- You MUST use information from the provided context
- You MUST explicitly use BOTH {source} and {target}
- You MUST NOT replace them with other variables
- Focus ONLY on the relationship between these two variables
- Do NOT shift the explanation to ecosystem risk unless clearly relevant

CAUSAL REASONING:

- The relationship may be:
  • direct
  • indirect (via hydrological dynamics, climate processes, etc.)
  • uncertain or context-dependent

- If the relationship is indirect:
  • explain intermediate mechanisms

- If the relationship is NOT clearly supported:
  • explicitly say it is uncertain
  • do NOT invent a direct link

DOMAIN REQUIREMENTS:
- You SHOULD mention, if relevant:
  • hydrological dynamics
  • water balance
  • climate-driven processes

CONTEXT ANCHORING:
- Refer to the Massaciuccoli lake basin if supported by context

STYLE:
- Avoid generic ecosystem explanations
- Avoid drifting to biodiversity or risk unless necessary
- If the context mentions other variables, ignore them unless strictly needed

OUTPUT FORMAT:
- Single paragraph
- 3–4 sentences
- Scientific but focused

DO NOT:
- Invent causal relationships
- Drift away from the two variables
"""

    # ======================================================
    # CASE 2: FEATURE → RISK
    # ======================================================

    else:

        extra_prompt = f"""
You are an environmental scientist analyzing a real lake ecosystem.

TASK:
Explain how {source} affects ecosystem stability or risk.

STRICT REQUIREMENTS:
- You MUST use information from the provided context
- You MUST explicitly refer to {source}
- You MUST NOT replace it with other variables

CAUSAL REASONING:

- You SHOULD describe a causal relationship if supported by the context

- The relationship may be:
  • direct
  • indirect (via hydrological dynamics, nutrient loading, water quality)
  • uncertain

- If NOT clearly supported:
  • explicitly state uncertainty
  • do NOT invent relationships

DOMAIN REQUIREMENTS:
- You MUST explicitly mention at least ONE of:
  • hydrological dynamics
  • nutrient loading
  • water quality
  • anthropogenic pressures
  • climate-driven changes

CONTEXT ANCHORING:
- You MUST refer to the Massaciuccoli lake basin

STYLE:
- Avoid generic ecological statements
- Do NOT assume direction (increase/decrease) unless supported
- Do NOT extend beyond what is supported

OUTPUT FORMAT:
- Single paragraph
- 3–5 sentences

DO NOT:
- Invent causal relationships
- Force cause-effect links
- Ignore uncertainty

---

Now answer the question using ONLY the context.
"""

    # ======================================================
    # BUILD QUERY (ALIGN WITH FEATURES)
    # ======================================================

    rag_query = question

    if source and target:
        rag_query = f"{source} affects {target} hydrology climate relationship lake ecosystem"

    # ======================================================
    # CALL RAG
    # ======================================================

    try:
        answer = generate_answer(rag_query, extra_prompt)

        print("\n[RAG-DEPENDENCY] Output:")
        print(answer)
        print("[RAG-DEPENDENCY v9] END\n")

        return answer

    except Exception as e:
        print("[RAG-DEPENDENCY ERROR]", e)

        return (
            "In the Massaciuccoli lake basin, environmental drivers influence ecosystem "
            "dynamics through hydrological and climate processes, although some relationships "
            "may be indirect or not clearly established in the available data."
        )