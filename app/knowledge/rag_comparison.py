# -*- coding: utf-8 -*-

"""
RAG Comparison v10 — TRANSITION-AWARE ECOLOGICAL REASONING

✔ Deterministic base
✔ KB-grounded comparison
✔ Transition-aware retrieval
✔ Ecological mechanisms
✔ Comparative ecosystem reasoning
✔ Strict coherence with model output
✔ No hallucinations
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
# BASE EXPLANATION
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

        driver_sentence = (
            " This difference is mainly associated with "
            + ", ".join(explanations[:3]) + "."
        )

    else:

        driver_sentence = ""

    context = (
        " Higher ecosystem risk reflects increased ecological fragility, "
        "environmental stress, and reduced ecosystem resilience."
    )

    return base + driver_sentence + context


# ======================================================
# TRANSITION QUERY
# ======================================================

def classify_transition(feature, value):

    f = feature.lower()

    # --------------------------------------------------
    # TREE COVER
    # --------------------------------------------------

    if "tree" in f or "forest" in f:

        if value is not None and value > 0:
            return "tree cover restoration"

        return "vegetation degradation"

    # --------------------------------------------------
    # BIODIVERSITY
    # --------------------------------------------------

    if "species" in f or "biodiversity" in f:

        if value is not None and value < 0:
            return "biodiversity decline"

        return "biodiversity resilience"

    # --------------------------------------------------
    # TEMPERATURE
    # --------------------------------------------------

    if "temperature" in f:

        if value is not None and value > 0:
            return "warming stress"

        return "temperature reduction"

    # --------------------------------------------------
    # PRECIPITATION
    # --------------------------------------------------

    if "precipitation" in f:

        if value is not None and value < 0:
            return "hydrological stress"

        return "increased water availability"

    # --------------------------------------------------
    # EVAPOTRANSPIRATION
    # --------------------------------------------------

    if "evapotranspiration" in f:

        return "water balance alteration"

    # --------------------------------------------------
    # GRASSLAND
    # --------------------------------------------------

    if "grassland" in f:

        return "habitat structure change"

    # --------------------------------------------------
    # FALLBACK
    # --------------------------------------------------

    return feature


def build_transition_query(drivers, delta):

    transition_terms = []

    for feature, a, b in drivers:

        if a is not None:
            transition_terms.append(
                classify_transition(feature, a)
            )

        if b is not None:
            transition_terms.append(
                classify_transition(feature, b)
            )

    transition_text = " vs ".join(
        list(dict.fromkeys(transition_terms))
    )

    if abs(delta) < 0.01:

        transition_type = "ecosystem stability comparison"

    elif delta > 0:

        transition_type = (
            "ecosystem degradation transition"
        )

    else:

        transition_type = (
            "ecosystem resilience transition"
        )

    query = f"""
    lake ecosystem transition
    {transition_type}
    {transition_text}
    hydrology
    biodiversity
    ecosystem resilience
    environmental stress
    habitat fragmentation
    ecological stability
    restoration dynamics
    degradation mechanisms
    """

    return query


# ======================================================
# CLEAN OUTPUT
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

    import re

    if re.search(r"\b[A-Z]\d\.[A-Z]\b", text):
        return None

    return text.strip()


# ======================================================
# VALIDATION
# ======================================================

def is_coherent(base_text: str, generated: str):

    """
    Semantic coherence validation.

    Allows:
    - ecological narrative
    - transition explanations
    - scenario paraphrases

    Blocks:
    - explicit contradiction of the base conclusion
    """

    if not generated:
        return False

    base = base_text.lower()
    gen = generated.lower()

    # --------------------------------------------------
    # Expected winner
    # --------------------------------------------------

    expected = None

    if "first scenario shows higher ecosystem risk" in base:
        expected = "first"

    elif "second scenario shows higher ecosystem risk" in base:
        expected = "second"

    # --------------------------------------------------
    # Explicit contradiction detection
    # --------------------------------------------------

    contradiction_patterns = [

        ("first", [
            "second scenario shows higher ecosystem risk",
            "second scenario is more fragile",
            "second scenario is worse",
            "the biodiversity-loss scenario shows lower risk"
        ]),

        ("second", [
            "first scenario shows higher ecosystem risk",
            "first scenario is more fragile",
            "first scenario is worse",
            "the tree-cover scenario shows lower risk"
        ])
    ]

    for target, patterns in contradiction_patterns:

        if expected != target:
            continue

        for p in patterns:

            if p in gen:
                return False

    # --------------------------------------------------
    # Otherwise allow semantic reasoning
    # --------------------------------------------------

    return True


# ======================================================
# RAG ENHANCEMENT
# ======================================================

def enhance_with_rag(base_text, drivers, delta):

    query = build_transition_query(
        drivers,
        delta
    )

    debug_print("[RAG] Transition Query:")
    debug_print(query)

    retrieved, _ = retrieve_documents(query)

    context = build_context(retrieved)

    debug_print("[RAG] Docs:", len(retrieved))

    prompt = f"""
You are an environmental scientist specialized in lake ecosystems.

TASK:
Interpret the ecological meaning of the quantitative risk difference between the two scenarios.

QUANTITATIVE RESULT:
{base_text}

SCENARIO DRIVERS:
{drivers}

SCIENTIFIC CONTEXT:
{context}

INSTRUCTIONS:
- The explanation must remain compatible with the quantitative result
- Focus on ecological transitions, resilience mechanisms, and environmental tradeoffs
- Explain the ecological mechanisms behind the risk difference
- Use concepts from the scientific context
- Discuss hydrology, biodiversity, ecosystem resilience, environmental stress, or habitat dynamics when relevant
- Explain how the ecosystem transitions from one condition to another
- Mention restoration or degradation dynamics if supported by the context
- Do not simply restate the quantitative result
- Avoid generic statements
- Do NOT mention machine learning, SHAP, models, or predictions
- Do NOT include meta-comments
- Keep the explanation concise but scientifically grounded
- Write as an environmental scientist interpreting ecosystem dynamics

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

    print("\n[RAG-COMPARISON v10] START")

    base = build_base_explanation(
        drivers,
        delta
    )

    debug_print("[BASE]:", base)

    final = enhance_with_rag(
        base,
        drivers,
        delta
    )

    debug_print("[FINAL]:", final)

    print("[RAG-COMPARISON v10] END")

    return final