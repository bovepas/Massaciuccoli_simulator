# -*- coding: utf-8 -*-

"""
RAG Assessment — v3

✔ Strong KB grounding
✔ Driver-guided retrieval
✔ Scientific ecological explanations
✔ Uses primary drivers explicitly
✔ Uses secondary ecosystem responses
✔ Better alignment with assessment outputs
✔ Reduced generic climate narratives
✔ Safe fallback
"""

from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm
import re
from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)



# ======================================================
# CONFIG
# ======================================================

MAX_CONTEXT_CHARS = 1500
DEBUG = True

# ======================================================
# DEBUG FLAGS
# ======================================================

DEBUG = True

DEBUG_DISABLE_RAG = False

MAX_CONTEXT_CHARS = 1500

# ======================================================
# UTILS
# ======================================================

def clean_text(text: str):

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_context(retrieved):

    if not retrieved:
        return ""

    chunks = [r["text"] for r in retrieved]

    context = "\n\n".join(chunks)

    if len(context) > MAX_CONTEXT_CHARS:

        context = context[:MAX_CONTEXT_CHARS]

    return context


def is_valid_output(text: str):

    if not text:
        return False

    if len(text.strip()) < 30:
        return False

    return True


def fallback():

    return (
        "Environmental drivers influence ecosystem risk through "
        "interacting effects on hydrology, habitat structure, "
        "ecological resilience, and biodiversity."
    )
# ======================================================
# REPORT
# ======================================================

def build_assessment_report(
    question,
    risk_delta,
    primary_drivers,
    secondary_responses
):

    if risk_delta is None:
        risk_text = "Unknown"
    else:
        risk_text = f"{risk_delta:.2f}"

    if risk_delta is None:
        trend = "cannot be determined"
    elif risk_delta > 0:
        trend = "higher than"
    elif risk_delta < 0:
        trend = "lower than"
    else:
        trend = "comparable to"

    primary = ""

    if primary_drivers:
        primary = "\n".join(
            f"• {k} (association score: {abs(v):.2f})"
            for k, v in primary_drivers.items()
        )
    else:
        primary = "None"

    secondary = ""

    if secondary_responses:
        secondary = "\n".join(
            f"• {k} (association score: {abs(v):.2f})"
            for k, v in secondary_responses.items()
        )
    else:
        secondary = "None"

    report = f"""
============================================================
DIGITAL TWIN ASSESSMENT REPORT
============================================================

BASELINE ECOSYSTEM
------------------------------------------------------------

The current ecosystem conditions are used as the
baseline reference for the assessment.

============================================================
SIMULATED ENVIRONMENTAL SCENARIO
------------------------------------------------------------

{question}

============================================================
PREDICTED ECOSYSTEM RESPONSE
------------------------------------------------------------

Predicted ecosystem risk: {risk_text}

============================================================
PRIMARY MODEL DRIVERS
------------------------------------------------------------

{primary}

============================================================
SECONDARY ECOSYSTEM ASSOCIATIONS
------------------------------------------------------------

{secondary}
"""

    return report

# ======================================================
# ECOLOGICAL NOTES
# ======================================================

def build_ecological_notes(
    primary_drivers,
    secondary_responses
):

    notes = []

    notes.append(
        "The primary model drivers identify the environmental "
        "variables most strongly associated with the predicted "
        "ecosystem risk."
    )

    notes.append(
        "Secondary ecosystem associations identify ecosystem "
        "components statistically associated with the simulated "
        "scenario. They do not necessarily indicate variables "
        "that increased or decreased during the simulation."
    )

    if primary_drivers:

        notes.append("")

        notes.append(
            "Primary drivers reported by the Digital Twin:"
        )

        for feature in primary_drivers.keys():

            notes.append(
                f"• {feature} is identified by the Digital Twin "
                "as one of the primary model drivers associated "
                "with the predicted ecosystem response."
            )

    if secondary_responses:

        notes.append("")

        notes.append(
            "Secondary ecosystem associations:"
        )

        for feature in secondary_responses.keys():

            notes.append(
                f"• {feature} is identified by the Digital Twin "
                "as a secondary ecosystem association describing "
                "the simulated environmental scenario."
            )

    return (
        "============================================================\n"
        "ECOLOGICAL INTERPRETATION NOTES\n"
        "============================================================\n\n"
        + "\n".join(notes)
        + "\n"
    )

# ======================================================
# PROMPT
# ======================================================
def build_legacy_prompt(
    question,
    risk_text,
    primary_text,
    secondary_text,
    context
):
    return f"""
You are an environmental scientist.

QUESTION:
{question}

MODEL RESULTS

Risk increase:
{risk_text}

Primary drivers:
{primary_text}

Secondary ecosystem responses:
{secondary_text}

SCIENTIFIC KNOWLEDGE BASE:
{context}

TASK

Provide a short scientific interpretation
of the scenario.

The primary drivers identify the factors
most strongly associated with the increase
in ecosystem risk.

The secondary ecosystem responses identify
ecosystem components most strongly associated
with the scenario.

Use the scientific knowledge base to explain
the ecological mechanisms that may connect
the primary drivers and the secondary
responses.

Interpret associations rather than assuming
that variables necessarily increase or
decrease.

Focus on ecological processes, ecosystem
functioning, resilience and biodiversity
when supported by the scientific context.

Write a single coherent paragraph.

Use approximately 4–6 sentences.

Answer:
"""



# ======================================================
# MAIN
# ======================================================

def generate_assessment_explanation(
    question: str,
    drivers: list,
    primary_drivers: dict = None,
    secondary_responses: dict = None,
    risk_delta: float = None,
    features: list = None

):

    print("\n[RAG-ASSESSMENT v3] START")

    # --------------------------------------------------
    # DRIVER-GUIDED QUERY
    # --------------------------------------------------

    driver_text = ", ".join(
        drivers[:3]
    )

    query = f"""
    lake ecosystem risk interactions
    {driver_text}
    hydrology biodiversity resilience
    ecological stability nutrient dynamics
    """

    print(
        "[DEBUG] RAG query:",
        query
    )

    if DEBUG_DISABLE_RAG:

        print(
            "[RAG] DEBUG: Retrieval context disabled."
        )

        retrieved = []

        context = ""

    else:

        retrieved, _ = retrieve_documents(
            query
        )

        context = build_context(
            retrieved
        )

        print(
            "[RAG] Retrieved documents:",
            len(retrieved)
        )

        print(
            "[RAG] Context length:",
            len(context)
        )

    # --------------------------------------------------
    # MODEL RESULTS
    # --------------------------------------------------

    primary_text = ""
    secondary_text = ""

    if primary_drivers:

        primary_text = "\n".join(
            f"- {k}\n"
            f"  association score: {abs(v):.2f}"
            for k, v in primary_drivers.items()
        )

    if secondary_responses:

        secondary_text = "\n".join(
            f"- {k}\n"
            f"  association score: {abs(v):.2f}"
            for k, v in secondary_responses.items()
        )

    risk_text = "unknown"

    if risk_delta is not None:

        risk_text = f"{risk_delta:.2f}"

    # --------------------------------------------------
    # DEBUG
    # --------------------------------------------------

    print("\n[RAG] PRIMARY DRIVERS")
    print(primary_drivers)

    print("\n[RAG] SECONDARY RESPONSES")
    print(secondary_responses)

    print("\n[RAG] RISK DELTA")
    print(risk_delta)


    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if USE_LEGACY_PROMPTS:

        prompt = build_legacy_prompt(
            question,
            risk_text,
            primary_text,
            secondary_text,
            context
        )

    else:

        report = build_assessment_report(
            question,
            risk_delta,
            primary_drivers,
            secondary_responses
        )

        ecological_notes = build_ecological_notes(
            primary_drivers,
            secondary_responses
        )

        prompt = (
            build_prompt(
                "assessment",
                question=question
            )
            + report
            + ecological_notes
            + f"""

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

        {context}

        """
        )

    # --------------------------------------------------
    # LLM
    # --------------------------------------------------

    try:
        if DEBUG:

            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")
        raw = call_llm(
            prompt
        )

        print(
            "[RAG] RAW:",
            raw
        )

        if not is_valid_output(raw):

            return fallback()

        cleaned = clean_text(
            raw
        )

        print(
            "[RAG-ASSESSMENT v3] END\n"
        )

        return cleaned

    except Exception as e:

        print(
            "[RAG-ASSESSMENT ERROR]",
            e
        )

        return fallback()