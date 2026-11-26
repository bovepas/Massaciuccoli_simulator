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

    prompt = f"""
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

    # --------------------------------------------------
    # CALL
    # --------------------------------------------------

    try:

        result = generate_answer(

            question=rag_query,

            features=features,

            extra_prompt=prompt
        )

        cleaned = clean_output(
            result
        )

        if cleaned:

            final_text = (

                comparison_statement
                + "\n\n"
                + cleaned
            )

            print(
                "\n[RAG OUTPUT]"
            )

            print(
                final_text
            )

            print(
                "\n[RAG-IMPORTANCE-COMPARE] END\n"
            )

            return final_text

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