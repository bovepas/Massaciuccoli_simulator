# -*- coding: utf-8 -*-

"""
RAG Delta — v36 (polished + stable + demo-ready)

✔ Uses centralized llm_client
✔ Deterministic ecological logic preserved
✔ Output validation
✔ Cleaner text generation
✔ Strong fallback (demo-safe)
"""

import re
from tools.llm_client import call_llm

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# BUILD FACTS
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

    # remove duplicates
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
- Combine them into 1–2 sentences
- Do NOT add causes
- Do NOT introduce new concepts
- Keep it clear and natural
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

    # 🔥 fix repetition artifacts
    text = text.replace("increases increases", "increases")
    text = text.replace("decreases decreases", "decreases")

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
# FALLBACK (🔥 MUCH BETTER)
# ======================================================

def fallback(facts, delta):

    if not facts:
        return "No clear environmental pattern detected."

    sentence = " and ".join(facts[:2]) + "."

    return add_risk_alignment(sentence, delta)


# ======================================================
# MAIN
# ======================================================

def generate_delta_explanation(question, drivers, delta=None):

    print("\n[RAG-DELTA v36] START")

    facts = build_facts(drivers)
    debug_print("[FACTS]:", facts)

    if not facts:
        return "No clear environmental pattern detected."

    prompt = build_prompt(facts)
    debug_print("\n[PROMPT]:\n", prompt)

    try:

        raw = call_llm(prompt)
        debug_print("\n[RAW]:", raw)

        if not is_valid(raw):
            return fallback(facts, delta)

        cleaned = clean_output(raw)
        final = add_risk_alignment(cleaned, delta)

        print("[FINAL]:", final)
        print("[RAG-DELTA v36] END")

        return final

    except Exception as e:

        print("[RAG ERROR]", e)
        return fallback(facts, delta)