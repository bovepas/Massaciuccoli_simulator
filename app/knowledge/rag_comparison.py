# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Comparison v3 — deterministic + optional LLM enhancement

✔ Deterministic core (always works)
✔ Optional LLM for better phrasing
✔ Safe fallback
"""

from tools.llm_client import call_llm

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# BUILD BASE (DETERMINISTIC CORE)
# ======================================================

def build_base_explanation(drivers, delta):

    # ---------------- BASE ----------------
    if abs(delta) < 0.01:
        base = "The two scenarios show similar ecosystem risk."
    elif delta > 0:
        base = "The second scenario shows higher ecosystem risk."
    else:
        base = "The first scenario shows higher ecosystem risk."

    # ---------------- DRIVERS ----------------
    explanations = []

    for feature, a, b in drivers:

        if a is None or b is None:
            continue

        if b > a:
            explanations.append(f"{feature} increases")
        elif b < a:
            explanations.append(f"{feature} decreases")

    if explanations:
        drivers_text = ", ".join(explanations[:3])
        driver_sentence = f" This difference is mainly driven by {drivers_text}."
    else:
        driver_sentence = ""

    # ---------------- CONTEXT ----------------
    context = (
        " Higher risk reflects ecosystems that are more fragile "
        "or sensitive to environmental stressors."
    )

    return base + driver_sentence + context


# ======================================================
# OPTIONAL LLM REWRITE
# ======================================================

def enhance_with_llm(text):

    prompt = f"""
Rewrite the following explanation in a slightly more natural and fluid way.

TEXT:
{text}

RULES:
- Keep the same meaning
- Do NOT add new information
- Keep it concise (max 2 sentences)
"""

    try:

        raw = call_llm(prompt)

        if not raw or "Interpretation not available" in raw:
            return text

        return raw.strip()

    except Exception:
        return text


# ======================================================
# MAIN
# ======================================================

def generate_comparison_explanation(drivers, delta):

    print("\n[RAG-COMPARISON v3] START")

    base = build_base_explanation(drivers, delta)

    debug_print("[BASE]:", base)

    # 🔥 optional enhancement
    final = enhance_with_llm(base)

    debug_print("[FINAL]:", final)

    print("[RAG-COMPARISON v3] END")

    return final