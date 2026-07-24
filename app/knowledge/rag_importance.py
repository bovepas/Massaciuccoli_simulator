# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v22

✔ Compact prompt architecture
✔ Reduced verbosity
✔ Cleaner ecosystem grounding
✔ Faster generation
✔ Better alignment with structured outputs
✔ Preserved uncertainty handling
"""

import re

from knowledge.rag_pipeline import generate_answer
# from utils.feature_semantics import (
#     build_semantic_context
# )

from config.llm_profiles import (
    LLM_PROFILE,
    LLM_STYLE
)


from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)

DEBUG = True
# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text: str):

    if not text:
        return None

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    sentences = re.split(
        r'(?<=[.!?])\s+',
        text
    )

    if not sentences:
        return None

    return " ".join(
        sentences[:4]
    ).strip()


# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(
    drivers,
    mode,
    group_scores=None
):

    if not drivers:

        return (
            "No dominant drivers "
            "were identified."
        )

    variables = ", ".join([

        d["name"]

        for d in drivers[:5]
    ])

    if group_scores:

        dominant_groups = list(
            group_scores.keys()
        )[:2]

        group_text = ", ".join(
            dominant_groups
        )

        return (
            f"In the Massaciuccoli lake basin, "
            f"{group_text}-related variables "
            f"appear associated with ecosystem "
            f"risk through interactions involving "
            f"biodiversity, land-use dynamics, "
            f"hydrology, and ecosystem resilience."
        )

    return (
        f"In the Massaciuccoli lake basin, "
        f"{variables} are associated with "
        f"ecosystem risk through interacting "
        f"ecological and environmental processes."
    )


# ======================================================
# BUILD DRIVER BLOCK
# ======================================================

def build_driver_block(drivers):

    rows = []

    for d in drivers:

        delta = d.get(
            "perturbation_delta",
            "n/a"
        )

        if isinstance(delta, (int, float)):

            delta = round(
                abs(delta),
                2
            )

        rows.append(

            f"- {d['name']} | "
            f"group={d.get('group', 'other')} | "
            f"impact={round(d['impact'], 4)} | "
            f"strength={d.get('strength', 'unknown')} | "
            f"delta={delta}"
        )

    return "\n".join(rows)


# ======================================================
# BUILD GROUP BLOCK
# ======================================================

def build_group_block(group_scores):

    if not group_scores:
        return "- None"

    rows = []

    for group, score in group_scores.items():

        rows.append(
            f"- {group} | score={round(score, 4)}"
        )

    return "\n".join(rows)


# ======================================================
# IMPORTANCE REPORT
# ======================================================

def build_importance_report(
    question,
    increase_block,
    decrease_block,
    group_block
):

    return f"""
============================================================
DIGITAL TWIN IMPORTANCE REPORT
============================================================

QUESTION
------------------------------------------------------------

{question}

============================================================
DOMINANT ENVIRONMENTAL DOMAINS
------------------------------------------------------------

{group_block}

============================================================
RISK-INCREASING VARIABLES
------------------------------------------------------------

{increase_block}

============================================================
RISK-REDUCING VARIABLES
------------------------------------------------------------

{decrease_block}
"""

# ======================================================
# ECOLOGICAL NOTES
# ======================================================

def build_importance_notes():

    return """
============================================================
ECOLOGICAL INTERPRETATION NOTES
============================================================

The reported variables represent the strongest
statistical associations identified by the
Digital Twin.

Variables reported as risk-increasing are
statistically associated with higher predicted
ecosystem risk.

Variables reported as risk-reducing are
statistically associated with lower predicted
ecosystem risk.

These associations do not represent observed
environmental changes and should not be interpreted
as direct ecological causality.

Use the retrieved scientific evidence only to
explain the ecological relevance of the reported
variables.
"""

# ======================================================
# LEGACY PROMPT 
# ======================================================
def build_legacy_prompt(
    impact_text
):

    return f"""
You are an environmental scientist.

QUESTION:
What are the main factors influencing ecosystem risk?

MODEL RESULTS:

{impact_text}

TASK

Provide a concise scientific interpretation
of the dominant ecosystem drivers.

Use the scientific knowledge base to
describe possible ecological mechanisms
associated with the identified domains
and variables.

Interpret associations rather than
assuming direct causality.

Focus on:
- biodiversity
- land-use dynamics
- ecosystem resilience
- hydrology

Write a compact paragraph
of approximately 4–5 sentences.

Answer:
"""


# ======================================================
# MAIN
# ======================================================

def generate_importance_explanation(
    drivers,
    question,
    mode="absolute",
    group_scores=None,
    features=None

):

    print("\n[RAG-IMPORTANCE v22] START\n")
    print(
    f"[RAG-IMPORTANCE] "
    f"profile={LLM_PROFILE} "
    f"style={LLM_STYLE}"
)

    if not drivers:

        return (
            "No dominant drivers were "
            "identified in this scenario."
        )

    # ======================================================
    # USER INTENT
    # ======================================================

    q = question.lower()

    focus = "all"

    if any(k in q for k in [

        "increase",
        "higher",
        "raise",
        "drives risk"

    ]):

        focus = "increase"

    elif any(k in q for k in [

        "decrease",
        "reduce",
        "mitigate",
        "lower"

    ]):

        focus = "decrease"

    elif "stability" in q:

        focus = "stability"

    print(
        f"[DEBUG] Detected focus: {focus}"
    )

    # ======================================================
    # FILTER DRIVERS
    # ======================================================

    if focus == "increase":

        increase = [

            d for d in drivers

            if d["impact"] > 0
        ][:5]

        decrease = []

    elif focus == "decrease":

        increase = []

        decrease = [

            d for d in drivers

            if d["impact"] < 0
        ][:5]

    elif focus == "stability":

        increase = [

            d for d in drivers

            if d["impact"] < 0
        ][:5]

        decrease = [

            d for d in drivers

            if d["impact"] > 0
        ][:5]

    else:

        increase = [

            d for d in drivers

            if d["impact"] > 0
        ][:5]

        decrease = [

            d for d in drivers

            if d["impact"] < 0
        ][:5]

    # ======================================================
    # DRIVER BLOCKS
    # ======================================================

    increase_block = build_driver_block(
        increase
    ) or "- None"

    decrease_block = build_driver_block(
        decrease
    ) or "- None"

    # ======================================================
    # GROUP BLOCK
    # ======================================================

    group_block = build_group_block(
        group_scores
    )

    # ======================================================
    # IMPACT STRUCTURE
    # ======================================================

    if focus == "increase":

        impact_text = f"""
DOMINANT ECOSYSTEM DOMAINS:
{group_block}

RISK-INCREASING DRIVERS:
{increase_block}
"""

    elif focus == "decrease":

        impact_text = f"""
DOMINANT ECOSYSTEM DOMAINS:
{group_block}

RISK-REDUCING DRIVERS:
{decrease_block}
"""

    else:

        impact_text = f"""
DOMINANT ECOSYSTEM DOMAINS:
{group_block}

RISK-INCREASING DRIVERS:
{increase_block}

RISK-REDUCING DRIVERS:
{decrease_block}
"""

    print("[DEBUG] Impact structure:")
    print(impact_text)

    # ======================================================
    # RETRIEVAL QUERY
    # ======================================================

    driver_names = [

        d["name"]

        for d in drivers[:5]
    ]

    group_names = []

    if group_scores:

        group_names = list(
            group_scores.keys()
        )[:2]

    retrieval_terms = (
        driver_names +
        group_names
    )

    driver_text = ", ".join(
        retrieval_terms
    )

    rag_query = f"""
    {driver_text}

    ecosystem risk
    lake ecosystem
    
    """

    print("[DEBUG] RAG query:")
    print(rag_query)


    # ======================================================
    # PROMPT
    # ======================================================

    if USE_LEGACY_PROMPTS:

        prompt = build_legacy_prompt(
            impact_text
        )

    else:

        importance_report = build_importance_report(
            question,
            increase_block,
            decrease_block,
            group_block
        )

        importance_notes = build_importance_notes()

        prompt = (
            build_prompt("importance")
            + f"""

QUESTION:
{question}

{importance_report}

{importance_notes}

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

"""
        )

    # ======================================================
    # CALL
    # ======================================================

    try:
        if DEBUG:

            print("\n========== EXTRA PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        result = generate_answer(

            question=rag_query,

            features=features,

            extra_prompt=prompt
        )

        cleaned = clean_output(
            result
        )

        if cleaned:

            print("\n[RAG-IMPORTANCE] Output:")
            print(cleaned)

            print("[RAG-IMPORTANCE v22] END\n")

            return cleaned

        return fallback_explanation(
            drivers,
            mode,
            group_scores
        )

    except Exception as e:

        print("\n# RAG-IMPORTANCE ERROR:")
        print(e)

        return fallback_explanation(
            drivers,
            mode,
            group_scores
        )