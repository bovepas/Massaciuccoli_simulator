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

    text = re.sub(
        r"\s+",
        " ",
        text.strip()
    )

    return text or None


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

AUTHORITATIVE RESULTS
---------------------

The DIGITAL TWIN IMPORTANCE REPORT is the authoritative
source for variable names, impact values, impact signs,
strength labels, and risk direction.

DOMAIN SCORES and VARIABLE IMPACTS are different quantities.
A domain score must never be interpreted as the impact,
sign, or ranking of an individual variable.

Never present a domain such as "biodiversity" or "land_use"
as if it were an individual environmental variable.

VARIABLE DIRECTIONS
-------------------

A variable with a positive impact is associated with
higher predicted ecosystem risk.

A variable with a negative impact is associated with
lower predicted ecosystem risk.

Preserve the exact sign and value reported for every
variable. Never infer a variable's direction from its
domain score or from the direction of another variable
in the same domain.

For questions about the variables contributing most to
risk, report the leading individual variables and their
reported directions. Include both risk-increasing and
risk-reducing variables when both are present in the report.

For questions specifically about lower risk, focus on
variables whose reported impact is negative.

ECOLOGICAL INTERPRETATION
-------------------------

The reported associations describe the Digital Twin's
predictions. They do not establish direct ecological
causality or prove that changing a variable will change
risk in the reported direction.

Do not describe an association as statistically significant
unless a statistical significance test is explicitly reported.

Do not equate plant productivity with biodiversity.
Use retrieved scientific evidence only to explain the
ecological relevance of the reported variables. If the
evidence does not establish a mechanism, state the
association without inventing one.

OUTPUT
------

Use the exact variable names from the report.
Distinguish variables from environmental domains.
Be concise, scientifically cautious, and useful to a
manager of the Massaciuccoli basin.
Do not omit leading variables merely to shorten the answer.
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
    # DETERMINISTIC FACTUAL INTERPRETATION + RAG CONTEXT
    # ======================================================

    def format_driver(driver):
        name = driver["name"]
        impact = float(driver["impact"])
        strength = driver.get("strength", "unknown")

        return (
            f"{name} (impact={impact:+.4f}, "
            f"strength={strength})"
        )

    # ------------------------------------------------------
    # 1. Build the authoritative numerical interpretation
    # ------------------------------------------------------

    sections = []

    if increase:
        increasing_text = "; ".join(
            format_driver(d) for d in increase
        )

        sections.append(
            "Variables associated with higher predicted "
            f"ecosystem risk: {increasing_text}."
        )

    if decrease:
        decreasing_text = "; ".join(
            format_driver(d) for d in decrease
        )

        sections.append(
            "Variables associated with lower predicted "
            f"ecosystem risk: {decreasing_text}."
        )

    if not sections:
        sections.append(
            "No variables matching the requested risk "
            "direction were identified in the importance report."
        )

    interpretation = " ".join(sections)

    interpretation += (
        " These are associations in the Digital Twin's "
        "predictions, not proof of direct ecological causality. "
        "The reported impacts do not establish that changing "
        "a variable will cause risk to change in the same direction."
    )

    # ------------------------------------------------------
    # 2. Retrieve scientific context through the existing RAG
    # ------------------------------------------------------

    ecological_prompt = """
You are providing a short ecological-context note for the
Massaciuccoli Digital Twin.

TASK:
Describe only the ecological meaning of the environmental
variables listed below, using the retrieved scientific evidence.

VARIABLES:
""" + "\n".join(
        f"- {d['name']}" for d in drivers[:5]
    ) + """

RULES:
- Do not report, repeat, rank or reinterpret model impacts.
- Do not infer causal mechanisms from statistical associations.
- Do not claim that the retrieved evidence explains the signs
  of the model impacts unless the evidence explicitly supports it.
- Do not invent ecological facts or recommendations.
- Distinguish general wetland ecology from evidence specific
  to the Massaciuccoli basin.
- If the retrieved documents do not provide relevant evidence,
  state that they do not support a more specific explanation.
- Use at most three concise sentences.
- Return only the ecological-context note.
"""

    ecological_context = None

    try:
        print("\n[RAG-IMPORTANCE] Retrieving ecological context...")

        rag_output = generate_answer(
            rag_query,
            extra_prompt=ecological_prompt,
            prompt_question=(
                "Provide ecological context for these "
                "Massaciuccoli Digital Twin variables: "
                + ", ".join(d["name"] for d in drivers[:5])
            ),
            modular_prompt=True
        )

        ecological_context = clean_output(rag_output)

    except Exception as exc:
        print(
            "[RAG-IMPORTANCE] Context retrieval/generation failed: "
            f"{exc}"
        )

    # ------------------------------------------------------
    # 3. Basic validation of the generated context
    # ------------------------------------------------------

    if ecological_context:
        lower_context = ecological_context.lower()

        # Reject output that repeats model-result claims.
        forbidden_phrases = [
            "variables associated with higher predicted",
            "variables associated with lower predicted",
            "impact=",
            "strength=",
            "statistically significant",
        ]

        if any(
            phrase in lower_context
            for phrase in forbidden_phrases
        ):
            print(
                "[RAG-IMPORTANCE] Context rejected: "
                "it repeats or introduces model-result claims."
            )
            ecological_context = None

    # ------------------------------------------------------
    # 4. Combine without allowing RAG to alter model results
    # ------------------------------------------------------

    if ecological_context:
        interpretation += (
            "\n\nEcological context: "
            + ecological_context
        )
    else:
        interpretation += (
            "\n\nEcological context: the retrieved evidence "
            "did not provide a sufficiently specific explanation "
            "that could be added safely to this answer."
        )

    print("\n[RAG-IMPORTANCE] Deterministic output:")
    print(interpretation)
    print("[RAG-IMPORTANCE v23] END\n")

    return interpretation
