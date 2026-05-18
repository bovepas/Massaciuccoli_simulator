# -*- coding: utf-8 -*-

"""
RAG Dependency Explanation — v11 (STRONG KB GROUNDING)

✔ Keeps existing structure
✔ Strengthens KB usage
✔ Forces concrete, context-based reasoning
✔ Minimal changes, safe drop-in
"""

from knowledge.rag_pipeline import generate_answer


# ======================================================
# 🔥 TARGET NORMALIZATION FOR RETRIEVAL
# ======================================================

TARGET_QUERY_MAP = {
    "hydrological dynamics": "water balance lake level hydrology",
    "ecosystem stability": "ecosystem stability lake dynamics",
    "ecosystem productivity": "primary productivity lake ecosystem",
    "biodiversity": "species richness biodiversity ecosystem",
    "ecosystem risk": "ecosystem risk environmental stress lake"
}


def normalize_target_for_query(target: str):

    if not target:
        return ""

    return TARGET_QUERY_MAP.get(target, target)


# ======================================================
# MAIN
# ======================================================

def generate_dependency_explanation(question: str, source=None, target=None) -> str:

    print("\n[RAG-DEPENDENCY v11] START")

    target_for_query = normalize_target_for_query(target)

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
- You MUST base your explanation on specific mechanisms described in the context
- You MUST NOT rely on generic ecological knowledge alone
- You MUST ground your explanation in concrete processes (e.g., hydrology, nutrient dynamics)

CAUSAL REASONING:

- The relationship may be:
  • direct
  • indirect (via hydrological dynamics, climate processes, etc.)
  • uncertain or context-dependent

- If indirect:
  • explain intermediate mechanisms grounded in the context

- If unsupported:
  • explicitly state uncertainty
  • do NOT invent links

CONTEXT USAGE (CRITICAL):
- Refer to specific processes or dynamics mentioned in the context
- Avoid generic textbook explanations
- Anchor reasoning to lake ecosystem conditions when possible

OUTPUT FORMAT:
- Single paragraph
- 3–4 sentences
"""

    # ======================================================
    # CASE 2: FEATURE → RISK
    # ======================================================

    else:

        extra_prompt = f"""
You are an environmental scientist analyzing a real lake ecosystem.

TASK:
Explain how {source} affects ecosystem risk.

STRICT REQUIREMENTS:
- You MUST use information from the provided context
- You MUST explicitly refer to {source}
- You MUST base your reasoning on specific mechanisms from the context
- You MUST NOT rely on generic knowledge alone

DOMAIN REQUIREMENTS:
- You MUST explicitly mention at least ONE of:
  • hydrological dynamics
  • nutrient loading
  • water quality
  • climate-driven changes

CONTEXT USAGE (CRITICAL):
- Anchor the explanation to processes described in the context
- Avoid generic ecosystem explanations
- Prefer concrete mechanisms over general statements

OUTPUT FORMAT:
- Single paragraph
- 3–5 sentences
"""

    # ======================================================
    # 🔥 STRONGER QUERY (driver-guided)
    # ======================================================

    rag_query = question

    if source:
        rag_query = f"""
        lake ecosystem {source} {target_for_query} interactions
        hydrology nutrient dynamics water quality climate processes
        """

    print("[RAG] Final query:", rag_query)

    # ======================================================
    # CALL RAG
    # ======================================================

    try:
        answer = generate_answer(rag_query, extra_prompt)

        print("\n[RAG-DEPENDENCY] Output:")
        print(answer)
        print("[RAG-DEPENDENCY v11] END\n")

        return answer

    except Exception as e:
        print("[RAG-DEPENDENCY ERROR]", e)

        return (
            "In lake ecosystems, environmental drivers influence ecological dynamics "
            "through hydrological and biogeochemical processes, although specific "
            "relationships may depend on local conditions and available evidence."
        )