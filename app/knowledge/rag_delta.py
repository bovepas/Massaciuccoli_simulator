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
                    "vegetation density increases",
                    "habitat conditions may change",
                    "ecosystem dynamics may be altered",
                ]

            else:

                facts += [
                    "tree cover decreases",
                    "vegetation density decreases",
                    "habitat conditions may change",
                    "ecosystem dynamics may be altered",
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

    # remove duplicates
    return list(dict.fromkeys(facts))


# ======================================================
# PROMPT
# ======================================================

def build_prompt(facts):

    fact_text = "\n".join(
        [f"- {f}" for f in facts]
    )

    return f"""
Rewrite the following facts into a concise environmental explanation.

FACTS:
{fact_text}

RULES:
- Use ONLY these facts
- Combine them into 1–2 sentences
- Do NOT introduce new concepts
- Do NOT present associations as proven causal mechanisms
- Distinguish between ecological interpretation and model prediction
- Use cautious scientific language
- Keep it concise and natural
- No introductions
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
            + deviation_text
        )

    elif delta < 0:

        return (
            text
            + f" The model predicts a {severity} "
              f"decrease in ecosystem risk "
              f"under this scenario, "
              f"with {confidence}."
            + deviation_text
        )

    else:

        return (
            text
            + " The model predicts no "
              "substantial change in "
              "ecosystem risk."
            + deviation_text
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

    prompt = build_prompt(facts)

    debug_print(
        "\n[PROMPT]:\n",
        prompt
    )

    try:

        raw = call_llm(prompt)

        debug_print(
            "\n[RAW]:",
            raw
        )

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