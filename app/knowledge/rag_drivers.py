# -*- coding: utf-8 -*-

"""
RAG Drivers — v8

✔ Reduced verbosity
✔ Cleaner scientific grounding
✔ More compact explanations
✔ Less “ecosystem essay mode”
✔ Preserved ecological interpretation
✔ Backward compatible
"""

from tools.llm_client import call_llm
from utils.feature_semantics import (
    build_semantic_context
)

DEBUG = True


def debug_print(*args):

    if DEBUG:
        print(*args)


# ======================================================
# PROMPT
# ======================================================

def build_prompt(
    target,
    drivers,
    semantic_context
):

    drivers_text = "\n".join([

        f"- {d['feature']} "
        f"({d['direction']}, "
        f"{d['strength']})"

        for d in drivers[:4]
    ])

    return f"""
You are an environmental scientist.

TARGET VARIABLE:
{target}

OBSERVED ENVIRONMENTAL ASSOCIATIONS:
{drivers_text}

ECOLOGICAL INTERPRETATION NOTES:
{semantic_context}

TASK:
Provide a concise scientific interpretation
of how the listed variables are associated
with {target}.

Use cautious ecological language and
interpret associations rather than
direct causality.

Focus on:
- biodiversity responses
- hydrology
- habitat conditions
- ecosystem stress

Write one compact paragraph
using 3–5 sentences.

Answer:
"""


# ======================================================
# OUTPUT VALIDATION
# ======================================================

def is_valid(text):

    if not text:
        return False

    if len(text) < 30:
        return False

    if "Interpretation not available" in text:
        return False

    return True


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text):

    text = text.strip()

    text = text.replace(
        "\n\n\n",
        "\n\n"
    )

    text = " ".join(
        text.split()
    )

    return text


# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(
    target,
    drivers
):

    if not drivers:

        return (
            "No relevant environmental associations "
            "were identified for the selected variable."
        )

    parts = []

    for d in drivers[:3]:

        direction = (
            "positively associated with"
            if d["direction"] == "positive"
            else "negatively associated with"
        )

        parts.append(

            f"{d['feature']} is {direction} "
            f"{target} with a {d['strength']} "
            f"environmental relationship"

        )

    return ". ".join(parts) + "."


# ======================================================
# MAIN
# ======================================================

def generate_drivers_explanation(
    target,
    drivers,
    features=None
):

    print("\n[RAG-DRIVERS v8] START")

    try:
        # ======================================================
        # SEMANTIC CONTEXT
        # ======================================================

        semantic_context = ""

        if features:

            semantic_context = build_semantic_context(
                features
            )

            print(
                "\n[RAG] SEMANTIC CONTEXT"
            )

            print(
                semantic_context
            )

        prompt = build_prompt(
            target,
            drivers,
            semantic_context
        )

        debug_print(
            "\n[RAG-DRIVERS] Prompt:"
        )

        debug_print(prompt)

        print(
            "    llm_prompt_length:",
            len(prompt)
        )

        raw = call_llm(
            prompt
        )

        debug_print(
            "\n[RAG-DRIVERS] Raw output:"
        )

        debug_print(raw)

        if not is_valid(raw):

            return fallback_explanation(
                target,
                drivers
            )

        cleaned = clean_output(
            raw
        )

        debug_print(
            "\n[RAG-DRIVERS] Final output:"
        )

        debug_print(cleaned)

        return cleaned

    except Exception as e:

        print(
            "\n🔥 RAG-DRIVERS ERROR:"
        )

        print(e)

        return fallback_explanation(
            target,
            drivers
        )

    finally:

        print("[RAG-DRIVERS] END\n")