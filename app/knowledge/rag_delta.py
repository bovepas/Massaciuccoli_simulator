"""
RAG Delta — v34 (clean, no duplication, robust alignment)
"""

import requests
import os
import re

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

LLM_MODEL = "llama3:8b"

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# BUILD FACTS (uses delta direction)
# ======================================================

def build_facts(drivers):

    facts = []

    for feature, v_from, v_to in drivers:

        name = feature.lower()
        delta = v_to - v_from

        # ---------------- TEMPERATURE ----------------
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

        # ---------------- PRECIPITATION ----------------
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

        # ---------------- EVAPOTRANSPIRATION ----------------
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

    # remove duplicates while preserving order
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

    text = text.strip()

    # remove typical prefixes
    text = re.sub(r"^here is.*?:", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^this means.*?:", "", text, flags=re.IGNORECASE)

    # normalize whitespace
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ======================================================
# ADD RISK SENTENCE (SAFE)
# ======================================================

def add_risk_alignment(text, delta):

    if delta is None:
        return text

    # avoid duplication
    if "ecosystem risk" in text.lower():
        return text

    if delta > 0:
        return text + " This leads to an increase in ecosystem risk."
    elif delta < 0:
        return text + " This leads to a decrease in ecosystem risk."
    else:
        return text + " This does not significantly change ecosystem risk."


# ======================================================
# LLM CALL
# ======================================================

def call_llm(prompt):

    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        }
    )

    response.raise_for_status()
    return response.json()["response"]


# ======================================================
# FALLBACK
# ======================================================

def fallback(facts):

    if not facts:
        return "No clear environmental pattern detected."

    return " ".join(facts[:2]) + "."


# ======================================================
# MAIN
# ======================================================

def generate_delta_explanation(question, drivers, delta=None):

    print("\n[RAG-DELTA v34] START")

    facts = build_facts(drivers)
    debug_print("[FACTS]:", facts)

    if not facts:
        return "No clear environmental pattern detected."

    prompt = build_prompt(facts)
    debug_print("\n[PROMPT]:\n", prompt)

    try:
        raw = call_llm(prompt)
        debug_print("\n[RAW]:", raw)

        cleaned = clean_output(raw)

        # 🔥 SAFE ALIGNMENT
        final = add_risk_alignment(cleaned, delta)

        print("[FINAL]:", final)
        print("[RAG-DELTA v34] END")

        return final

    except Exception as e:
        print("[RAG ERROR]", e)
        return fallback(facts)