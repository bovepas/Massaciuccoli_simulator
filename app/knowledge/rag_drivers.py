# -*- coding: utf-8 -*-

"""
RAG Drivers — v6 (polished + validated + demo-ready)

✔ Uses centralized LLM client
✔ Strict correlation-only language
✔ Output validation
✔ Natural fallback (demo-quality)
✔ Cleaner formatting
"""

from tools.llm_client import call_llm

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# PROMPT
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
- Simple and readable
- Avoid repetition
- Use ONLY associative language:
  "is positively associated with"
  "is negatively associated with"
  "shows a strong relationship with"
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

    # remove excessive newlines
    text = text.replace("\n\n\n", "\n\n")

    # normalize spaces
    text = " ".join(text.split())

    return text


# ======================================================
# FALLBACK (🔥 MUCH MORE NATURAL)
# ======================================================

def fallback_explanation(target, drivers):

    if not drivers:
        return "No relevant statistical relationships were identified for the selected variable."

    parts = []

    for d in drivers[:3]:

        direction = "positively" if d["direction"] == "positive" else "negatively"

        parts.append(
            f"{d['feature']} is {direction} associated with {target} "
            f"with a {d['strength']} relationship"
        )

    return ". ".join(parts) + "."


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

        if not is_valid(raw):
            return fallback_explanation(target, drivers)

        cleaned = clean_output(raw)

        debug_print("\n[RAG-DRIVERS] Final output:")
        debug_print(cleaned)

        return cleaned

    except Exception as e:

        print("\n🔥 RAG-DRIVERS ERROR:")
        print(e)

        return fallback_explanation(target, drivers)

    finally:
        print("[RAG-DRIVERS] END\n")