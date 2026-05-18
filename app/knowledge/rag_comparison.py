# -*- coding: utf-8 -*-

"""
RAG Comparison v9 — FINAL STABLE

✔ Deterministic base (trusted)
✔ KB grounding (RAG)
✔ Strict coherence with model output
✔ No meta-output
✔ No hallucinated codes (e.g., H3.M)
✔ Safe fallback
✔ Demo-ready
"""

from tools.llm_client import call_llm
from knowledge.retriever import retrieve_documents

DEBUG = True
MAX_CONTEXT_CHARS = 3000


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# CONTEXT
# ======================================================

def build_context(retrieved):

    if not retrieved:
        return ""

    chunks = [r["text"] for r in retrieved]
    context = "\n\n".join(chunks)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]

    return context


# ======================================================
# BASE (TRUSTED SOURCE OF TRUTH)
# ======================================================

def build_base_explanation(drivers, delta):

    if abs(delta) < 0.01:
        base = "The two scenarios show similar ecosystem risk."
    elif delta > 0:
        base = "The second scenario shows higher ecosystem risk."
    else:
        base = "The first scenario shows higher ecosystem risk."

    explanations = []

    for feature, a, b in drivers:
        if a is None or b is None:
            continue
        if b > a:
            explanations.append(f"{feature} increases")
        elif b < a:
            explanations.append(f"{feature} decreases")

    if explanations:
        driver_sentence = " This difference is mainly driven by " + ", ".join(explanations[:3]) + "."
    else:
        driver_sentence = ""

    context = " Higher risk reflects ecosystems that are more fragile or sensitive to environmental stressors."

    return base + driver_sentence + context


# ======================================================
# CLEAN OUTPUT (ANTI-META + ANTI-HALLUCINATION)
# ======================================================

def clean_output(text: str):

    if not text:
        return None

    lower = text.lower()

    blacklist = [
        "here's a refined explanation",
        "note:",
        "i've kept the original meaning",
        "this explanation",
        "refined explanation"
    ]

    for b in blacklist:
        if b in lower:
            return None

    # 🔥 blocca codici tipo H3.M
    import re
    if re.search(r"\b[A-Z]\d\.[A-Z]\b", text):
        return None

    return text.strip()


# ======================================================
# VALIDATION (CRITICAL FIX)
# ======================================================

def is_coherent(base_text: str, generated: str):

    if not generated:
        return False

    base = base_text.lower()
    gen = generated.lower()

    if "first scenario" in base and "second scenario" in gen:
        return False

    if "second scenario" in base and "first scenario" in gen:
        return False

    return True


# ======================================================
# RAG ENHANCEMENT
# ======================================================

def enhance_with_rag(base_text, drivers):

    driver_text = ", ".join([f[0] for f in drivers if f[0]])

    query = f"""
    lake ecosystem risk {driver_text} hydrology biodiversity nutrient dynamics
    """

    debug_print("[RAG] Query:", query)

    retrieved, _ = retrieve_documents(query)
    context = build_context(retrieved)

    debug_print("[RAG] Docs:", len(retrieved))

    prompt = f"""
You are an environmental scientist.

TASK:
Explain which scenario has higher ecosystem risk and why.

BASE CONCLUSION:
{base_text}

VARIABLES:
{driver_text}

CONTEXT:
{context}

STRICT RULES:
- The explanation MUST be consistent with the base conclusion
- Clearly state which scenario is worse
- Explicitly refer to the variables (e.g., temperature, precipitation, biodiversity, tree cover)
- Use ecological mechanisms from the context (e.g., hydrology, water balance, ecosystem stress)
- Do NOT include meta-comments (no "refined explanation", no "note")
- Do NOT describe your reasoning process
- Do NOT introduce unrelated concepts
- Keep it concise (2–3 sentences)
- Answer directly as if responding to a user

OUTPUT:
"""

    try:
        raw = call_llm(prompt)

        if not raw:
            return base_text

        cleaned = clean_output(raw)

        if cleaned is None:
            return base_text

        if not is_coherent(base_text, cleaned):
            return base_text

        return cleaned

    except Exception:
        return base_text


# ======================================================
# MAIN
# ======================================================

def generate_comparison_explanation(drivers, delta):

    print("\n[RAG-COMPARISON v9] START")

    base = build_base_explanation(drivers, delta)

    debug_print("[BASE]:", base)

    final = enhance_with_rag(base, drivers)

    debug_print("[FINAL]:", final)

    print("[RAG-COMPARISON v9] END")

    return final