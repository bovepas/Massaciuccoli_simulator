# -*- coding: utf-8 -*-

"""
RAG Dependency Explanation — v14

✔ Reduced prompt verbosity
✔ Smaller retrieval context
✔ Cleaner dependency grounding
✔ Faster generation
✔ Preserved uncertainty handling
✔ More compact scientific explanations
"""

from knowledge.rag_pipeline import generate_answer


# ======================================================
# CONFIG
# ======================================================

MAX_CONTEXT_CHARS = 1000


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

- Strength:
  {dependency_info.get('strength')}

- Score:
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
    dependency_info=None,
    features=None
) -> str:

    print("\n[RAG-DEPENDENCY v14] START")

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
You are an environmental scientist.

QUESTION:
How does {source} influence {target}?

MODEL RESULTS:
{dependency_block}

TASK

Provide a concise scientific explanation
of the observed ecological association.

Use the scientific knowledge base to
describe possible ecological mechanisms.

Interpret the relationship as an association,
not as direct causality.

Use cautious scientific language such as:
- "is associated with"
- "may contribute to"
- "appears related to"

Focus on:
- biodiversity
- hydrology
- climate interactions
- ecosystem stress

Write 3–4 concise sentences.

Answer:
"""

    # ======================================================
    # CASE 2: FEATURE → RISK
    # ======================================================

    else:

        extra_prompt = f"""
You are an environmental scientist.

QUESTION:
How does {source} affect ecosystem risk?

MODEL RESULTS:
{dependency_block}

TASK

Provide a concise scientific explanation
of the observed ecological association.

Use the scientific knowledge base to
describe possible ecological mechanisms.

Interpret the relationship as an association,
not as direct causality.

Focus on:
- ecosystem stress
- biodiversity
- hydrology
- environmental pressures

Write 3–4 concise sentences.

Answer:
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
        biodiversity interaction
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

            question=rag_query,

            features=features,

            extra_prompt=extra_prompt
        )

        print("\n[RAG-DEPENDENCY] Output:")
        print(answer)

        print("[RAG-DEPENDENCY v14] END\n")

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