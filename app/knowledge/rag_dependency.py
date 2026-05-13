# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Dependency — v8 (robust demo version)

✔ Uses centralized LLM client
✔ Strong fallback (even for bad LLM outputs)
✔ Cleaner output validation
✔ Demo-safe
"""

from tools.llm_client import call_llm

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# PROMPT
# ======================================================

def build_prompt(source, target, strength, direction, drivers):

    drivers_text = ""
    if drivers:
        drivers_text = "\nMODEL DRIVERS:\n" + "\n".join([f"- {d}" for d in drivers])

    if strength in ["strong", "moderate"]:
        behavior_rules = """
- Describe a plausible environmental mechanism linking the variables
- Use simple causal language (e.g., "can lead to", "is associated with")
- Keep statements realistic and not overly specific
- Avoid introducing unrelated processes
"""
    else:
        behavior_rules = """
- Emphasize uncertainty and weak evidence
- Avoid strong causal claims
- Describe the effect as small, unclear, or data-dependent
"""

    return f"""
You are an environmental scientist.

RELATION:
{source} → {target} ({strength}, {direction})

{drivers_text}

TASK:
Explain the relationship between these variables in a realistic ecological context.

IMPORTANT:
- The explanation MUST be consistent with the strength ({strength})
- Do NOT contradict the strength level
- Do NOT exaggerate weak relationships

RULES:
{behavior_rules}
- Use clear and simple language
- Max 2 sentences
"""


# ======================================================
# FALLBACK
# ======================================================

def fallback_response(source, target, strength, direction):

    if strength == "negligible":
        return (
            f"The model does not detect a meaningful relationship between {source} and {target}. "
            f"Any observed effect is very small and may reflect noise rather than a consistent pattern."
        )

    elif strength == "weak":
        return (
            f"The relationship between {source} and {target} appears {direction}, "
            f"but the effect is weak and may depend on local environmental conditions."
        )

    elif strength == "moderate":
        return (
            f"{source} shows a moderate {direction} relationship with {target}, "
            f"suggesting a possible environmental link that may vary across conditions."
        )

    else:  # strong
        return (
            f"{source} is strongly associated with {target}, "
            f"indicating a consistent relationship in the observed data."
        )


# ======================================================
# OUTPUT VALIDATION (🔥 NEW)
# ======================================================

def is_valid_output(text: str) -> bool:

    if not text:
        return False

    text = text.strip()

    # troppo corto → sospetto
    if len(text) < 20:
        return False

    # fallback già presente
    if "Interpretation not available" in text:
        return False

    return True


# ======================================================
# MAIN
# ======================================================

def generate_dependency_explanation(source, target, strength, direction, drivers=None):

    print("\n[RAG-DEPENDENCY] START")

    try:

        # skip LLM for negligible
        if strength == "negligible":
            return fallback_response(source, target, strength, direction)

        prompt = build_prompt(source, target, strength, direction, drivers)

        debug_print("\n[RAG-DEPENDENCY] Prompt:")
        debug_print(prompt)

        raw = call_llm(prompt)

        debug_print("\n[RAG-DEPENDENCY] Raw output:")
        debug_print(raw)

        # 🔥 VALIDATION STRONGER
        if not is_valid_output(raw):
            return fallback_response(source, target, strength, direction)

        final = raw.strip().replace("\n", " ").replace("  ", " ")

        debug_print("\n[RAG-DEPENDENCY] Final output:")
        debug_print(final)

        return final

    except Exception as e:

        print("\n🔥 RAG-DEPENDENCY ERROR:")
        print(e)

        return fallback_response(source, target, strength, direction)

    finally:
        print("[RAG-DEPENDENCY] END\n")