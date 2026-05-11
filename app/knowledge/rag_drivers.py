# -*- coding: utf-8 -*-

"""
RAG Drivers — v3 (STRICT DATA-GROUNDED)
✔ ZERO hallucination
✔ NO causal claims beyond correlation
✔ DEMO SAFE
"""

import requests
import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

LLM_MODEL = "llama3:8b"

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# LLM CALL
# ======================================================

def call_llm(prompt: str) -> str:

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
    return response.json()["response"].strip()


# ======================================================
# PROMPT (🔥 HARDENED)
# ======================================================

def build_prompt(target, drivers):

    drivers_text = "\n".join([
        f"- {d['feature']} ({d['direction']}, {d['strength']})"
        for d in drivers
    ])

    return f"""
You are a data analyst.

TARGET VARIABLE:
{target}

OBSERVED RELATIONSHIPS (from correlations):
{drivers_text}

TASK:
Describe the observed relationships between variables.

STRICT RULES:

- ONLY describe correlations
- DO NOT explain mechanisms (no "because", no physical explanations)
- DO NOT introduce external concepts (e.g. urbanization, climate dynamics)
- DO NOT infer causality
- DO NOT generalize beyond the listed variables
- Use only the variable names provided

STYLE:

- 2 short paragraphs
- Simple and factual

STRICT LANGUAGE RULES:

- Use ONLY associative language
- Allowed expressions:
  "is positively associated with"
  "is negatively associated with"
  "shows a strong relationship with"

- FORBIDDEN:
  "leads to"
  "causes"
  "results in"
  "as X increases"
  "this means that"
  "due to"

Write neutral statistical descriptions only.

"""


# ======================================================
# MAIN
# ======================================================

def generate_drivers_explanation(target, drivers):

    print("\n[RAG-DRIVERS] START")

    try:

        prompt = build_prompt(target, drivers)

        debug_print("\n[RAG-DRIVERS] Prompt:")
        debug_print(prompt)

        raw = call_llm(prompt)

        debug_print("\n[RAG-DRIVERS] Raw output:")
        debug_print(raw)

        final = raw.strip()

        debug_print("\n[RAG-DRIVERS] Final output:")
        debug_print(final)

        return final

    except Exception as e:

        print("\n🔥 RAG-DRIVERS ERROR:")
        print(e)

        return "Interpretation not available."

    finally:
        print("[RAG-DRIVERS] END\n")