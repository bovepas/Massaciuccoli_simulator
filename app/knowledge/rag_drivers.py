# -*- coding: utf-8 -*-

"""
RAG Drivers — v7 (ecosystem pressure reasoning)

✔ Environmental-science framing
✔ Ecosystem-pressure interpretation
✔ Softer non-causal language
✔ Better KB alignment
✔ Cleaner scientific UX
✔ Backward compatible
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

        f"- {d['feature']} "
        f"({d['direction']}, {d['strength']})"

        for d in drivers
    ])

    return f"""
You are an environmental scientist analyzing ecosystem pressures in a lake system.

TARGET VARIABLE:
{target}

OBSERVED ENVIRONMENTAL ASSOCIATIONS:
{drivers_text}

TASK:
Explain how the listed variables are environmentally associated with {target}.

STRICT REQUIREMENTS:
- Base the explanation on the listed variables
- Use ecological and environmental interpretation
- You may discuss ecosystem pressures, environmental stress, and interacting processes
- Avoid unsupported causal claims
- Do not invent variables that are not listed
- Keep the explanation scientifically grounded and concise

STYLE:
- 2 short paragraphs
- Clear scientific language
- Readable and natural tone
- Emphasize ecosystem pressures and degradation patterns when relevant
- Prefer ecosystem-oriented wording over statistical jargon
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

    text = text.replace("\n\n\n", "\n\n")

    text = " ".join(text.split())

    return text


# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(target, drivers):

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

def generate_drivers_explanation(target, drivers):

    print("\n[RAG-DRIVERS v7] START")

    try:

        prompt = build_prompt(
            target,
            drivers
        )

        debug_print("\n[RAG-DRIVERS] Prompt:")
        debug_print(prompt)

        raw = call_llm(prompt)

        debug_print("\n[RAG-DRIVERS] Raw output:")
        debug_print(raw)

        if not is_valid(raw):

            return fallback_explanation(
                target,
                drivers
            )

        cleaned = clean_output(raw)

        debug_print("\n[RAG-DRIVERS] Final output:")
        debug_print(cleaned)

        return cleaned

    except Exception as e:

        print("\n🔥 RAG-DRIVERS ERROR:")
        print(e)

        return fallback_explanation(
            target,
            drivers
        )

    finally:

        print("[RAG-DRIVERS] END\n")