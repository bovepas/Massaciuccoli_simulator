# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v21
(group-aware ecosystem risk attribution)

✔ Group-aware ecosystem interpretation
✔ Semantic ecosystem domains
✔ Improved scientific readability
✔ Better ecosystem-level summaries
✔ Preserves epistemic discipline
✔ Keeps perturbation-aware attribution
"""

import re

from knowledge.rag_pipeline import generate_answer


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
            f"appear to dominate ecosystem risk "
            f"attribution. Variables such as "
            f"{variables} are associated with "
            f"hydrological dynamics, ecosystem "
            f"stress, biodiversity conditions, "
            f"and land-system pressures."
        )

    return (
        f"In the Massaciuccoli lake basin, "
        f"{variables} are associated with "
        f"ecosystem risk through interactions "
        f"affecting hydrological dynamics, "
        f"climate pressures, biodiversity, "
        f"and ecosystem resilience."
    )


# ======================================================
# BUILD DRIVER BLOCK
# ======================================================

def build_driver_block(drivers):

    rows = []

    for d in drivers:

        rows.append(

            f"- {d['name']} | "
            f"group={d.get('group', 'other')} | "
            f"impact={round(d['impact'], 4)} | "
            f"strength={d.get('strength', 'unknown')} | "
            f"delta={d.get('perturbation_delta', 'n/a')}"
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
# MAIN
# ======================================================

def generate_importance_explanation(
    drivers,
    question,
    mode="absolute",
    group_scores=None
):

    print("\n[RAG-IMPORTANCE v21] START\n")

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

    print(f"[DEBUG] Detected focus: {focus}")

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
        )[:3]

    retrieval_terms = driver_names + group_names

    driver_text = ", ".join(
        retrieval_terms
    )

    rag_query = f"""
    {driver_text}

    ecosystem risk
    Massaciuccoli lake basin
    hydrology
    biodiversity
    nutrient loading
    water quality
    climate stress
    ecosystem resilience
    land use dynamics
    vegetation dynamics
    """

    print("[DEBUG] RAG query:")
    print(rag_query)

    # ======================================================
    # PROMPT
    # ======================================================

    prompt = f"""
You are analyzing ecosystem risk
in a real lake ecosystem.

TASK:
Explain how the following environmental
domains and variables are associated
with ecosystem risk.

{impact_text}

STRICT REQUIREMENTS:

- You MUST respect the direction
  of influence

- You MUST distinguish between:
  • modeled importance estimates
  • ecological mechanisms
  • ecosystem domains

- The listed impacts represent:
  perturbation-based sensitivity estimates

- Importance scores DO NOT prove
  direct ecological causality

- Ecological mechanisms MUST come ONLY
  from the retrieved context

- You MUST explicitly mention
  dominant ecosystem domains
  when supported by the data

- You MUST NOT introduce drivers
  not listed above

- Avoid deterministic causal language:
  "drives"
  "determines"
  "directly causes"

- Prefer cautious language:
  "is associated with"
  "may contribute to"
  "appears related to"

DOMAIN REQUIREMENTS:

You MUST explicitly mention at least ONE:
• hydrological dynamics
• nutrient loading
• water quality
• anthropogenic pressures
• climate-driven changes

CONTEXT ANCHORING:
- Refer explicitly to the
  Massaciuccoli lake basin

STYLE:
- Scientific but readable
- Natural language
- No bullet points
- No introductions like:
  "As an environmental scientist..."
- 3–5 sentences

DO NOT:
- Treat all drivers equally
- Ignore dominant ecosystem domains
- Invent unsupported mechanisms
- Turn statistical importance
  into proven causality

---

Now explain the system.
"""

    # ======================================================
    # CALL
    # ======================================================

    try:

        result = generate_answer(

            question=rag_query,

            extra_prompt=prompt
        )

        cleaned = clean_output(
            result
        )

        if cleaned:

            print("\n[RAG-IMPORTANCE] Output:")
            print(cleaned)

            print("[RAG-IMPORTANCE v21] END\n")

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