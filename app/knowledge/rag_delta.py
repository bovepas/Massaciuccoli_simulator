# -*- coding: utf-8 -*-

"""
RAG Delta — v35 (centralized LLM + robust + demo-ready)

✔ Uses centralized llm_client
✔ Keeps deterministic ecological logic
✔ Strong fallback
✔ Safe risk alignment
"""

import re
from tools.llm_client import call_llm

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# BUILD FACTS (UNCHANGED LOGIC)
# ======================================================

def build_facts(drivers):

    facts = []

    for feature, v_from, v_to in drivers:

        name = feature.lower()
        delta = v_to - v_from

        if "temperature" in name:
            if delta > 0:
                facts += [
                    "temperature increases",
                    "evaporation increases",
                    "water availability decreases",
                    "ecosystem stress increases",
                ]
            else:
                facts += [
                    "temperature decreases",
                    "evaporation decreases",
                    "water availability increases",
                    "ecosystem stress decreases",
                ]

        elif "precipitation" in name:
            if delta > 0:
                facts += [
                    "precipitation increases",
                    "water availability increases",
                    "ecosystem stress decreases",
                ]
            else:
                facts += [
                    "precipitation decreases",
                    "water availability decreases",
                    "ecosystem stress increases",
                ]

        elif "evapotranspiration" in name:
            if delta > 0:
                facts += [
                    "evapotranspiration increases",
                    "water loss increases",
                    "ecosystem stress increases",
                ]
            else:
                facts += [
                    "evapotranspiration decreases",
                    "water loss decreases",
                    "ecosystem stress decreases",
                ]

    return list(dict.fromkeys(facts))


# ======================================================
# PROMPT
# ======================================================

def build_prompt(facts):

    fact_text = "\n".join([f"- {f}" for f in facts])

    return f"""
Rewrite the following facts into a simple environmental explanation.

FACTS:
{fact_text}

RULES:
- Use ONLY these facts
- Do NOT add causes
- Do NOT introduce new concepts
- Keep it clear and simple
- Max 2 sentences
- No introductions
"""


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text):

    if not text:
        return ""

    text = text.strip()

    text = re.sub(r"^here is.*?:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^this means.*?:", "", text, flags=re.IGNORECASE)

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ======================================================
# ADD RISK SENTENCE
# ======================================================

def add_risk_alignment(text, delta):

    if delta is None:
        return text

    if "ecosystem risk" in text.lower():
        return text

    if delta > 0:
        return text + " This leads to an increase in ecosystem risk."
    elif delta < 0:
        return text + " This leads to a decrease in ecosystem risk."
    else:
        return text + " This does not significantly change ecosystem risk."


# ======================================================
# FALLBACK (IMPROVED)
# ======================================================

def fallback(facts, delta):

    if not facts:
        return "No clear environmental pattern detected."

    base = " ".join(facts[:2]) + "."

    return add_risk_alignment(base, delta)


# ======================================================
# MAIN
# ======================================================

def generate_delta_explanation(question, drivers, delta=None):

    print("\n[RAG-DELTA v35] START")

    facts = build_facts(drivers)
    debug_print("[FACTS]:", facts)

    if not facts:
        return "No clear environmental pattern detected."

    prompt = build_prompt(facts)
    debug_print("\n[PROMPT]:\n", prompt)

    try:

        raw = call_llm(prompt)
        debug_print("\n[RAW]:", raw)

        if not raw or "Interpretation not available" in raw:
            return fallback(facts, delta)

        cleaned = clean_output(raw)
        final = add_risk_alignment(cleaned, delta)

        print("[FINAL]:", final)
        print("[RAG-DELTA v35] END")

        return final

    except Exception as e:

        print("[RAG ERROR]", e)
        return fallback(facts, delta)