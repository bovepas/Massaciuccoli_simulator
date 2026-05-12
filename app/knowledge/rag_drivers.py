# -*- coding: utf-8 -*-

"""
RAG Drivers — v5 (centralized LLM + strong fallback)

✔ Uses centralized LLM client
✔ No direct HTTP calls
✔ Robust fallback (structured)
✔ Demo-ready output
"""

from tools.llm_client import call_llm

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# PROMPT (STRICT + DEMO READY)
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
- DO NOT explain mechanisms
- DO NOT introduce external concepts
- DO NOT infer causality
- DO NOT generalize beyond the listed variables
- Use only the variable names provided

STYLE:
- 2 short paragraphs
- Simple and factual
- Use ONLY associative language:
  "is positively associated with"
  "is negatively associated with"
  "shows a strong relationship with"
"""


# ======================================================
# FALLBACK (🔥 MUCH BETTER)
# ======================================================

def fallback_explanation(target, drivers):

    if not drivers:
        return "No relevant statistical relationships were identified."

    sentences = []

    for d in drivers[:3]:  # top 3 for readability
        sentences.append(
            f"{d['feature']} is {d['direction']}ly associated with {target} "
            f"with a {d['strength']} relationship."
        )

    return " ".join(sentences)


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

        # 🔥 fallback if LLM fails silently
        if not raw or "Interpretation not available" in raw:
            return fallback_explanation(target, drivers)

        final = raw.strip()

        debug_print("\n[RAG-DRIVERS] Final output:")
        debug_print(final)

        return final

    except Exception as e:

        print("\n🔥 RAG-DRIVERS ERROR:")
        print(e)

        return fallback_explanation(target, drivers)

    finally:
        print("[RAG-DRIVERS] END\n")