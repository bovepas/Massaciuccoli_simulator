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

        prompt = (
            build_prompt("assessment")
            + f"""

    QUESTION:
    {question}

    MODEL RESULTS
    The reported association scores indicate the relative importance of variables
    within the model. They are not measurements and do not indicate that a variable
    has increased or decreased.
    Risk increase:
    {risk_text}

    Primary drivers:
    {primary_text}

    Secondary ecosystem responses:
    {secondary_text}

    SCIENTIFIC KNOWLEDGE BASE:
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