# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE EXPLANATION v24

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
Never interpret a domain score as the impact, sign, or
ranking of an individual variable.

Never present a domain such as "biodiversity" or "land_use"
as if it were an individual environmental variable.

VARIABLE DIRECTIONS
-------------------

A positive impact is associated with higher predicted
ecosystem risk. A negative impact is associated with lower
predicted ecosystem risk.

Preserve the direction reported for each variable.
Do not infer a variable's direction from its domain score
or from another variable in the same domain.

For questions about the variables contributing most to
risk, cover the leading individual variables and their
reported directions. Include both directions when present.

Exact impact magnitudes need not be repeated unless the
question asks for numerical values. Never alter or invent
a magnitude.

ECOLOGICAL INTERPRETATION
-------------------------

The reported associations describe the Digital Twin's
predictions. They do not establish direct ecological
causality or prove that changing a variable will change
risk in the reported direction.

Do not describe an association as statistically significant
unless a statistical significance test is explicitly reported.

Do not equate plant productivity with biodiversity.
Explain what each variable represents and why that
environmental dimension matters in wetland ecosystems.

Distinguish general ecological knowledge about wetland
systems from evidence specifically concerning the
Massaciuccoli basin. Do not present general knowledge as
a finding demonstrated by the retrieved documents or
by the Digital Twin.

Do not invent mechanisms explaining the sign of an impact,
site-specific trends, or management recommendations.
If the retrieved evidence does not support a specific
mechanism, explain the ecological relevance at a general
level and retain the uncertainty.

OUTPUT
------

Produce one integrated, coherent answer, not separate
"model results" and "ecological context" sections.

Use clear, readable prose. Identify the leading variables,
explain their complementary ecological dimensions, and
connect them cautiously to wetland ecosystem functioning.

Keep the answer concise (approximately 4-5 sentences).
Use the canonical variable names or clear, faithful
descriptions of them. Do not omit leading variables.
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

    print("\n[RAG-IMPORTANCE v24] START\n")
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

    driver_names = [d["name"] for d in drivers[:5]]
    driver_list = "; ".join(driver_names)

    rag_query = f"""
target=ecosystem risk in the Massaciuccoli wetland ecosystem;
drivers={driver_list}.

Relevant context: ecological significance, environmental roles,
and documented relationships with wetland ecosystem condition,
habitat functioning, and resilience.

Do not assume that the retrieved documents establish causality.
Prioritize evidence specific to the Massaciuccoli basin where available.
"""

    print("[DEBUG] Importance RAG query:")
    print(rag_query)

    # ======================================================
    # AUTHORITATIVE RESULTS + INTEGRATED SYNTHESIS PROMPT
    # ======================================================

    importance_report = build_importance_report(
        question,
        increase_block,
        decrease_block,
        group_block
    )

    importance_notes = build_importance_notes()

    if USE_LEGACY_PROMPTS:
        base_prompt = build_legacy_prompt(impact_text)
    else:
        base_prompt = build_prompt("importance")

    synthesis_instructions = """
============================================================
INTEGRATED ANSWER TASK
============================================================

Answer the user's question by integrating:
1. the authoritative Digital Twin importance results;
2. the ecological meaning of the identified variables;
3. the retrieved scientific context.

Write one coherent paragraph of approximately 4-5 sentences.
Do not produce a list followed by a separate ecological note.

Explain how the selected variables describe complementary
dimensions of ecosystem condition. Where appropriate, connect
those dimensions to general wetland ecosystem functioning,
but distinguish general ecological knowledge from
Massaciuccoli-specific evidence.

Preserve the risk direction reported for each variable.
Do not imply that all variables have the same association.
Do not claim that retrieved documents explain an impact sign
unless they explicitly provide that evidence.

Do not infer causality, intervention effects, or management
priorities from model associations. In particular, do not
suggest that increasing or decreasing a variable will
necessarily reduce ecosystem risk.

If the retrieved evidence is general or limited, use cautious
wording; do not invent site-specific mechanisms or findings.

Return only the final answer, with no headings, preamble,
or separate "Ecological context" section.
"""

    full_prompt = (
        base_prompt
        + "\n\n"
        + importance_report
        + "\n\n"
        + importance_notes
        + "\n\n"
        + synthesis_instructions
    )

    # Deterministic fallback: preserve the model results if generation fails.
    def format_driver(driver):
        return (
            f"{driver['name']} "
            f"(impact={float(driver['impact']):+.4f}, "
            f"strength={driver.get('strength', 'unknown')})"
        )

    sections = []

    if increase:
        sections.append(
            "Variables associated with higher predicted ecosystem risk: "
            + "; ".join(format_driver(d) for d in increase)
            + "."
        )

    if decrease:
        sections.append(
            "Variables associated with lower predicted ecosystem risk: "
            + "; ".join(format_driver(d) for d in decrease)
            + "."
        )

    if not sections:
        sections.append(
            "No variables matching the requested risk direction "
            "were identified in the importance report."
        )

    fallback_interpretation = " ".join(sections)
    fallback_interpretation += (
        " These are associations in the Digital Twin's predictions, "
        "not proof of direct ecological causality or evidence that "
        "changing a variable will cause risk to change in the same direction."
    )

    # ======================================================
    # RETRIEVAL + INTEGRATED GENERATION
    # ======================================================

    try:
        print("\n[RAG-IMPORTANCE] Generating integrated interpretation...")

        rag_output = generate_answer(
            rag_query,
            extra_prompt=full_prompt,
            # The original question is already included in importance_report.
            # Empty displayed_question avoids duplicating it in the RAG prompt.
            prompt_question="",
            modular_prompt=True
        )

        generated_answer = clean_output(rag_output)

        # Do not return the generic RAG fallback as if it were an answer.
        if generated_answer and any(
            marker in generated_answer.lower()
            for marker in (
                "the system could not retrieve",
                "the system could not provide",
                "not enough information to provide",
            )
        ):
            generated_answer = None

        if generated_answer:
            interpretation = generated_answer
            print("[RAG-IMPORTANCE] Integrated LLM answer accepted.")
        else:
            interpretation = fallback_interpretation
            print("[RAG-IMPORTANCE] Empty/fallback LLM output; using deterministic result.")

    except Exception as exc:
        print(
            "[RAG-IMPORTANCE] Retrieval/generation failed: "
            f"{exc}"
        )
        interpretation = fallback_interpretation

    print("\n[RAG-IMPORTANCE] Final output:")
    print(interpretation)
    print("[RAG-IMPORTANCE v24] END\n")

    return interpretation
