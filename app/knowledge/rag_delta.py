# -*- coding: utf-8 -*-

"""
RAG Delta — v38 (epistemic + significance-aware)

✔ Uses centralized llm_client
✔ Deterministic ecological logic preserved
✔ Softer ecological language
✔ Epistemic risk phrasing
✔ Delta significance semantics
✔ Cleaner text generation
✔ Strong fallback
✔ Tree cover + biodiversity support
"""

import re
from tools.llm_client import call_llm

from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# DELTA SIGNIFICANCE
# ======================================================

def classify_delta(delta):

    if delta is None:
        return "moderate"

    d = abs(delta)

    if d < 0.01:
        return "negligible"

    elif d < 0.05:
        return "slight"

    elif d < 0.15:
        return "moderate"

    elif d < 0.35:
        return "strong"

    else:
        return "substantial"


# ======================================================
# BUILD FACTS
# ======================================================

def build_facts(drivers):

    facts = []

    for feature, v_from, v_to in drivers:

        name = feature.lower()
        delta = v_to - v_from

        # --------------------------------------------------
        # TEMPERATURE
        # --------------------------------------------------

        if "temperature" in name:

            if delta > 0:

                facts += [
                    "temperature increases",
                    "higher evapotranspiration may occur",
                    "water availability may decrease",
                    "ecosystem stress may increase",
                ]

            else:

                facts += [
                    "temperature decreases",
                    "evapotranspiration may decrease",
                    "water availability may increase",
                    "ecosystem stress may decrease",
                ]

        # --------------------------------------------------
        # PRECIPITATION
        # --------------------------------------------------

        elif "precipitation" in name:

            if delta > 0:

                facts += [
                    "precipitation increases",
                    "water availability may increase",
                    "ecosystem stress may decrease",
                ]

            else:

                facts += [
                    "precipitation decreases",
                    "water availability may decrease",
                    "ecosystem stress may increase",
                ]

        # --------------------------------------------------
        # EVAPOTRANSPIRATION
        # --------------------------------------------------

        elif "evapotranspiration" in name:

            if delta > 0:

                facts += [
                    "evapotranspiration increases",
                    "water loss may increase",
                    "ecosystem stress may increase",
                ]

            else:

                facts += [
                    "evapotranspiration decreases",
                    "water loss may decrease",
                    "ecosystem stress may decrease",
                ]

        # --------------------------------------------------
        # TREE COVER
        # --------------------------------------------------

        elif "tree cover" in name:

            if delta > 0:

                facts += [
                    "tree cover increases",
                    "forest habitats may be better preserved",
                    "ecosystem resilience may increase",
                    "ecosystem structure may change",
                ]

            else:

                facts += [
                    "tree cover decreases",
                    "vegetation density may decrease",
                    "habitat conditions may deteriorate",
                    "ecosystem structure may change",
                ]

        # --------------------------------------------------
        # GRASSLAND
        # --------------------------------------------------

        elif "grassland" in name:

            if delta > 0:

                facts += [
                    "grassland extent increases",
                    "open habitat availability may increase",
                    "ecosystem composition may change",
                ]

            else:

                facts += [
                    "grassland extent decreases",
                    "open habitat availability may decrease",
                    "ecosystem composition may change",
                ]

        # --------------------------------------------------
        # BIODIVERSITY
        # --------------------------------------------------

        elif "species" in name or "biodiversity" in name:

            if delta > 0:

                facts += [
                    "biodiversity increases",
                    "ecosystem resilience may increase",
                    "ecosystem stress may decrease",
                ]

            else:

                facts += [
                    "biodiversity decreases",
                    "ecosystem resilience may decrease",
                    "ecosystem stress may increase",
                ]

        # --------------------------------------------------
        # PRODUCTIVITY
        # --------------------------------------------------

        elif "productivity" in name or "phenology" in name:

            if delta > 0:

                facts += [
                    "vegetation productivity increases",
                    "primary production may increase",
                    "ecosystem functioning may change",
                ]

            else:

                facts += [
                    "vegetation productivity decreases",
                    "primary production may decrease",
                    "ecosystem functioning may change",
                ]

        # --------------------------------------------------
        # IMPERVIOUSNESS / URBANIZATION
        # --------------------------------------------------

        elif "impervious" in name:

            if delta > 0:

                facts += [
                    "land imperviousness increases",
                    "surface sealing may increase",
                    "hydrological processes may be altered",
                ]

            else:

                facts += [
                    "land imperviousness decreases",
                    "surface sealing may decrease",
                    "hydrological processes may change",
                ]

        # --------------------------------------------------
        # LAND USE CHANGE
        # --------------------------------------------------

        elif "land use" in name:

            if delta > 0:

                facts += [
                    "land use change increases",
                    "ecosystem conditions may become more altered",
                    "ecological dynamics may change",
                ]

            else:

                facts += [
                    "land use change decreases",
                    "ecosystem conditions may remain more stable",
                    "ecological dynamics may change",
                ]

    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    return list(
        dict.fromkeys(facts)
    )


# ======================================================
# PROMPT
# ======================================================

def build_legacy_prompt(facts):

    fact_text = "\n".join(
        [f"- {f}" for f in facts]
    )

    return f"""
    Rewrite the following facts into a concise environmental explanation.

    FACTS:
    {fact_text}

    RULES:

    - Use ONLY these facts.
    - Do NOT introduce ecological processes that are not explicitly supported by the facts.
    - Do NOT introduce new concepts.

    - Avoid generic statements such as:
    - overall ecosystem health
    - environmental changes
    - ecological balance
    - ecosystem functioning

    unless these concepts are explicitly supported by the provided facts.

    - Combine the facts into 1-2 concise sentences.
    - Do NOT present associations as proven causal mechanisms.
    - Distinguish between ecological interpretation and model prediction.
    - Use cautious scientific language.
    - Keep the explanation concise and natural.
    - Do not use introductions.
    - Do NOT independently invent ecosystem risk changes.
    - Risk predictions may be added separately by the system.
    """


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text):

    if not text:
        return ""

    text = text.strip()

    text = re.sub(
        r"^here is.*?:",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^this means.*?:",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = text.replace("\n", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    # repetition cleanup
    text = text.replace(
        "increases increases",
        "increases"
    )

    text = text.replace(
        "decreases decreases",
        "decreases"
    )

    return text.strip()


# ======================================================
# OUTPUT VALIDATION
# ======================================================

def is_valid(text):

    if not text:
        return False

    if len(text) < 20:
        return False

    if "Interpretation not available" in text:
        return False

    return True


# ======================================================
# ADD RISK SENTENCE
# ======================================================

def add_risk_alignment(text, delta, drivers=None):

    if delta is None:
        return text

    if "ecosystem risk" in text.lower():
        return text

    severity = classify_delta(delta)

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    d = abs(delta)

    if d < 0.05:
        confidence = "low confidence"

    elif d < 0.20:
        confidence = "moderate confidence"

    else:
        confidence = "high confidence"

    # --------------------------------------------------
    # BASELINE DEVIATION
    # --------------------------------------------------

    deviation_text = ""

    if drivers:

        feature, v_from, v_to = drivers[0]

        relative_shift = abs(v_to - v_from)

        if relative_shift >= 30:

            deviation_text = (
                " This scenario represents "
                "a major deviation from "
                "baseline environmental "
                "conditions."
            )

        elif relative_shift >= 15:

            deviation_text = (
                " This scenario represents "
                "a notable deviation from "
                "baseline environmental "
                "conditions."
            )

    # --------------------------------------------------
    # RISK ALIGNMENT
    # --------------------------------------------------

    if delta > 0:

        return (
            text
            + f" The model predicts a {severity} "
              f"increase in ecosystem risk "
              f"under this scenario, "
              f"with {confidence}."
#           + deviation_text
        )

    elif delta < 0:

        return (
            text
            + f" The model predicts a {severity} "
              f"decrease in ecosystem risk "
              f"under this scenario, "
              f"with {confidence}."
#            + deviation_text
        )

    else:

        return (
            text
            + " The model predicts no "
              "substantial change in "
              "ecosystem risk."
#            + deviation_text
        )

# ======================================================
# FALLBACK
# ======================================================

def fallback(facts, delta):

    if not facts:
        return "No clear environmental pattern detected."

    sentence = " and ".join(facts[:2]) + "."

    return add_risk_alignment(
        sentence,
        delta
    )
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
# MAIN
# ======================================================

def generate_delta_explanation(
    question,
    drivers,
    delta=None
):

    print("\n[RAG-DELTA v38] START")

    facts = build_facts(drivers)

    debug_print("[FACTS]:", facts)

    if not facts:
        return (
            "No clear environmental "
            "pattern detected."
        )

    if USE_LEGACY_PROMPTS:

        prompt = build_legacy_prompt(
            facts
        )

    else:

        fact_text = "\n".join(
            f"- {f}"
            for f in facts
        )

        prompt = (
            build_prompt("delta")
            + f"""

FACTS:
{fact_text}

"""
        )

    try:
        if DEBUG:
            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        raw = call_llm(
            prompt
        )

        print("[RAW]:", raw)

        if not is_valid(raw):

            return fallback(
                facts,
                delta
            )

        cleaned = clean_output(raw)

        final = add_risk_alignment(
            cleaned,
            delta,
            drivers
        )

        print("[FINAL]:", final)

        print("[RAG-DELTA v38] END")

        return final

    except Exception as e:

        print("[RAG ERROR]", e)

        return fallback(
            facts,
            delta
        )