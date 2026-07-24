# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE COMPARE

Interpreta il confronto tra due driver
utilizzando gli score prodotti da
task_importance_compare.
"""

import re

from knowledge.rag_pipeline import (
    generate_answer
)

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

    return text


# ======================================================
# FEATURE TO TEXT
# ======================================================

def feature_to_text(feature):

    if isinstance(
        feature,
        list
    ):

        return "\n".join(
            feature
        )

    return str(feature)

# ======================================================
# LEGACY PROMPT
# ======================================================

def build_legacy_prompt(
    question,
    comparison_statement
):

    return f"""
You are an environmental scientist.

QUESTION

{question}

COMPUTED RESULT

{comparison_statement}

IMPORTANT

The comparison has already been computed.

Accept the computed result exactly as provided.

Do NOT determine which driver is stronger.

Do NOT compare the scores.

Do NOT reverse the ranking.

Do NOT restate the computed result.

TASK

Explain the ecological meaning of the computed result.

Focus primarily on plausible ecological mechanisms
associated with the higher-ranked driver.

You may briefly mention the lower-ranked driver,
but do NOT describe it as unimportant,
ineffective, negligible, or irrelevant.

A lower score only indicates lower sensitivity
within the current predictive model.

Interpret associations rather than direct causality.

Avoid generic conclusions.

Do not finish with statements such as:

- overall...
- these findings highlight...
- both drivers are important...

Start directly with the ecological interpretation.

Write approximately 3–4 concise sentences.

Answer:
"""

# ======================================================
# FALLBACK
# ======================================================

def fallback_compare_explanation(

    entity_a,
    entity_b,

    score_a,
    score_b
):

    if score_a > score_b:

        return (

            f"{entity_a} appears more strongly "
            f"associated with ecosystem risk "
            f"than {entity_b} in the current model."
        )

    elif score_b > score_a:

        return (

            f"{entity_b} appears more strongly "
            f"associated with ecosystem risk "
            f"than {entity_a} in the current model."
        )

    return (

        f"{entity_a} and {entity_b} "
        f"show similar influence on "
        f"ecosystem risk."
    )



# ======================================================
# IMPORTANCE COMPARISON REPORT
# ======================================================

def build_importance_compare_report(
    question,
    entity_a,
    entity_b,
    score_a,
    score_b,
    comparison_statement
):

    return f"""
============================================================
DIGITAL TWIN IMPORTANCE COMPARISON REPORT
============================================================

QUESTION
------------------------------------------------------------

{question}

============================================================
COMPARED VARIABLES
------------------------------------------------------------

Variable A:
{entity_a}

Variable B:
{entity_b}

============================================================
MODEL RESULTS
------------------------------------------------------------

Variable A importance score:
{score_a:.4f}

Variable B importance score:
{score_b:.4f}

============================================================
DIGITAL TWIN RESULT
------------------------------------------------------------

{comparison_statement}
"""


def build_importance_compare_notes():

    return """
============================================================
ECOLOGICAL INTERPRETATION NOTES
============================================================

The reported comparison was computed by the
Digital Twin.

The reported ranking reflects the relative
statistical association of the compared variables
with predicted ecosystem risk.

A higher importance score indicates greater
model sensitivity within the current prediction.

The reported scores do not represent direct
ecological causality or observed environmental
change.

Use the retrieved scientific evidence only to
explain the ecological relevance of the reported
variables.
"""

# ======================================================
# MAIN
# ======================================================

def generate_importance_compare_explanation(

    question,

    entity_a,
    entity_b,

    feature_a,
    feature_b,

    score_a,
    score_b,

    features=None
):

    print(
        "\n[RAG-IMPORTANCE-COMPARE] START\n"
    )

    print(
        f"[RAG] profile={LLM_PROFILE} "
        f"style={LLM_STYLE}"
    )

    # --------------------------------------------------
    # WINNER
    # --------------------------------------------------

    if score_a > score_b:

        winner = entity_a
        winner_score = score_a

        loser = entity_b
        loser_score = score_b

        comparison_statement = (

            f"In the current model, "
            f"{winner} shows a stronger influence "
            f"on ecosystem risk than {loser} "
            f"({winner_score:.4f} vs "
            f"{loser_score:.4f})."
        )

    elif score_b > score_a:

        winner = entity_b
        winner_score = score_b

        loser = entity_a
        loser_score = score_a

        comparison_statement = (

            f"In the current model, "
            f"{winner} shows a stronger influence "
            f"on ecosystem risk than {loser} "
            f"({winner_score:.4f} vs "
            f"{loser_score:.4f})."
        )

    else:

        winner = None
        loser = None

        comparison_statement = (

            f"In the current model, "
            f"{entity_a} and {entity_b} "
            f"show similar influence "
            f"on ecosystem risk."
        )

    print(
        "[DEBUG] winner =",
        winner
    )

    # --------------------------------------------------
    # FEATURE TEXT
    # --------------------------------------------------

    feature_a_text = feature_to_text(
        feature_a
    )

    feature_b_text = feature_to_text(
        feature_b
    )

    # --------------------------------------------------
    # RETRIEVAL QUERY
    # --------------------------------------------------

    rag_query = f"""
    {feature_a_text}

    {feature_b_text}

    ecosystem risk
    biodiversity
    ecosystem resilience
    land use
    hydrology
    """

    print(
        "\n[DEBUG] RAG QUERY:"
    )

    print(
        rag_query
    )

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if USE_LEGACY_PROMPTS:

            prompt = build_legacy_prompt(
                question,
                comparison_statement
            )

    else:

            report = build_importance_compare_report(
                question,
                entity_a,
                entity_b,
                score_a,
                score_b,
                comparison_statement
            )

            notes = build_importance_compare_notes()

            prompt = (
                build_prompt("importance_compare")
                + f"""

QUESTION:
{question}

{report}

{notes}

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

"""
            )

    # --------------------------------------------------
    # CALL
    # --------------------------------------------------

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

            print(
                "\n[RAG OUTPUT]"
            )

            print(
                cleaned
            )

            print(
                "\n[RAG-IMPORTANCE-COMPARE] END\n"
            )

            return cleaned

        return comparison_statement

    except Exception as e:

        print(
            "\n[RAG ERROR]"
        )

        print(e)

        return fallback_compare_explanation(

            entity_a,
            entity_b,

            score_a,
            score_b
        )