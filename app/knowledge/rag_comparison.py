"""
Massaciuccoli Digital Twin
RAG Comparison v2 — STRUCTURED + DETERMINISTIC
"""

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# MAIN
# ======================================================

def generate_comparison_explanation(drivers, delta):

    print("\n[RAG-COMPARISON v2] START")

    # --------------------------------------------------
    # BASE SENTENCE
    # --------------------------------------------------

    if abs(delta) < 0.01:
        base = "The two scenarios show similar ecosystem risk."
    elif delta > 0:
        base = "The second scenario shows higher ecosystem risk."
    else:
        base = "The first scenario shows higher ecosystem risk."

    # --------------------------------------------------
    # DRIVER INTERPRETATION
    # --------------------------------------------------

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

    # --------------------------------------------------
    # CONTEXT
    # --------------------------------------------------

    context = (
        " Higher risk reflects ecosystems that are more fragile "
        "or sensitive to environmental stressors."
    )

    final = base + driver_sentence + context

    debug_print("[FINAL]:", final)
    print("[RAG-COMPARISON v2] END")

    return final