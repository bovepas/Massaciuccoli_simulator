# -*- coding: utf-8 -*-

"""
RAG Dependency Explanation — v13 (epistemically grounded dependency reasoning)

✔ Uses dependency evidence
✔ Separates statistical interaction from ecological mechanisms
✔ KB-grounded ecological interpretation
✔ Strong uncertainty handling
✔ Preserves existing architecture
"""

from knowledge.rag_pipeline import generate_answer


# ======================================================
# TARGET NORMALIZATION FOR RETRIEVAL
# ======================================================

TARGET_QUERY_MAP = {

    "hydrological dynamics":
        "water balance lake level hydrology",

    "ecosystem stability":
        "ecosystem stability lake dynamics",

    "ecosystem productivity":
        "primary productivity lake ecosystem",

    "biodiversity":
        "species richness biodiversity ecosystem",

    "ecosystem risk":
        "ecosystem risk environmental stress lake"
}


def normalize_target_for_query(target: str):

    if not target:
        return ""

    return TARGET_QUERY_MAP.get(
        target,
        target
    )


# ======================================================
# DEPENDENCY EVIDENCE BLOCK
# ======================================================

def build_dependency_block(dependency_info):

    if not dependency_info:

        return """
DEPENDENCY EVIDENCE:
No quantitative dependency evidence available.
"""

    return f"""
DEPENDENCY EVIDENCE:

- Dependency strength:
  {dependency_info.get('strength')}

- Dependency score:
  {dependency_info.get('score')}

- Interaction type:
  {dependency_info.get('interaction_type')}

- Confidence:
  {dependency_info.get('confidence')}

- Direction:
  {dependency_info.get('direction')}
"""


# ======================================================
# MAIN
# ======================================================

def generate_dependency_explanation(
    question: str,
    source=None,
    target=None,
    dependency_info=None
) -> str:

    print("\n[RAG-DEPENDENCY v13] START")

    target_for_query = normalize_target_for_query(
        target
    )

    dependency_block = build_dependency_block(
        dependency_info
    )

    # ======================================================
    # CASE 1: FEATURE → FEATURE / ABSTRACT TARGET
    # ======================================================

    if target and target != "risk_score":

        extra_prompt = f"""
You are analyzing interactions within a lake ecosystem.

TASK:
Explain how {source} influences {target}.

{dependency_block}

STRICT REQUIREMENTS:
- You MUST use information from the provided context
- You MUST explicitly refer to BOTH {source} and {target}
- You MUST ground ecological mechanisms ONLY in the retrieved context
- You MUST use the dependency evidence as a quantitative constraint
- You MUST NOT contradict the dependency evidence
- You MUST avoid unsupported causal claims

DEPENDENCY INTERPRETATION:

- The dependency evidence ONLY measures
  statistical interaction strength between variables.

- The dependency score does NOT prove
  direct causality.

- Ecological mechanisms MUST come ONLY
  from the retrieved context.

- Statistical interaction strength
  MUST NOT be described as proven causality.

- Avoid verbs implying causal certainty such as:
  "drives"
  "determines"
  "directly causes"
  "controls"

- Prefer cautious language such as:
  "is associated with"
  "may contribute to"
  "is linked to"
  "appears related to"

- Clearly distinguish between:
  • modeled statistical interaction
  • ecological mechanisms discussed in the literature

- Strong dependencies:
  • indicate stronger modeled interactions
  • but do NOT automatically imply direct causation

- Moderate dependencies:
  • may reflect indirect or context-dependent interactions

- Weak dependencies:
  • should be interpreted cautiously
  • may reflect limited influence or noisy interactions

- Unsupported dependencies:
  • explicitly state that quantitative support is limited
  • avoid forcing explanations

CONTEXT USAGE:
- Prefer mechanisms grounded in retrieved documents
- Refer to hydrology, biodiversity, vegetation, climate, or nutrient dynamics when relevant
- Avoid generic textbook ecology

STYLE:
- Scientific but readable
- Natural language
- No introductory phrases like:
  "As an environmental scientist..."
- 3–5 sentences
- Suitable for both academic and non-technical users
"""

    # ======================================================
    # CASE 2: FEATURE → RISK
    # ======================================================

    else:

        extra_prompt = f"""
You are analyzing interactions within a lake ecosystem.

TASK:
Explain how {source} affects ecosystem risk.

{dependency_block}

STRICT REQUIREMENTS:
- You MUST use information from the provided context
- You MUST explicitly refer to {source}
- You MUST use the dependency evidence as a quantitative constraint
- You MUST avoid unsupported causal claims

DEPENDENCY INTERPRETATION:

- The dependency evidence ONLY measures
  modeled interaction strength.

- The dependency score does NOT prove
  direct causality.

- Ecological mechanisms MUST come ONLY
  from the retrieved context.

- Strong interaction scores:
  • indicate stronger modeled relationships
  • but NOT guaranteed direct ecological causation

- Weak or unsupported interactions:
  • should be interpreted cautiously
  • may indicate limited evidence

DOMAIN REQUIREMENTS:
- Explicitly discuss ecosystem stressors when relevant
- Prefer concrete mechanisms from the retrieved context
- Refer to hydrological dynamics, biodiversity, vegetation, or climate pressures when relevant

STYLE:
- Scientific but readable
- Natural language
- No introductory phrases like:
  "As an environmental scientist..."
- 3–5 sentences
"""

    # ======================================================
    # QUERY
    # ======================================================

    rag_query = question

    if source:

        rag_query = f"""
        lake ecosystem
        {source}
        {target_for_query}

        interaction dynamics
        hydrology
        biodiversity
        nutrient loading
        climate processes
        ecosystem stress
        """

    print("[RAG] Final query:")
    print(rag_query)

    print("[RAG] Dependency evidence:")
    print(dependency_info)

    # ======================================================
    # CALL RAG
    # ======================================================

    try:

        answer = generate_answer(
            rag_query,
            extra_prompt
        )

        print("\n[RAG-DEPENDENCY] Output:")
        print(answer)

        print("[RAG-DEPENDENCY v13] END\n")

        return answer

    except Exception as e:

        print("[RAG-DEPENDENCY ERROR]")
        print(e)

        return (
            "Environmental interactions in lake ecosystems "
            "often emerge through coupled hydrological, "
            "climatic, and ecological processes, although "
            "the strength of specific dependencies may vary "
            "depending on available evidence and ecosystem conditions."
        )