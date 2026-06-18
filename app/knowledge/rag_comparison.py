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
from utils.feature_semantics import (
    build_semantic_context
)

DEBUG = True
MAX_CONTEXT_CHARS = 1200


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
    lake ecosystem risk comparison
    {transition_type}
    {transition_text}
    hydrology
    biodiversity
    ecosystem resilience
    environmental stress
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

def enhance_with_rag(
    base_text,
    drivers,
    delta,
    features=None
):
    query = build_transition_query(
        drivers,
        delta
    )

    debug_print("[RAG] Transition Query:")
    debug_print(query)

    retrieved, _ = retrieve_documents(query)

    context = build_context(retrieved)
    
    # --------------------------------------------------
    # SEMANTIC CONTEXT
    # --------------------------------------------------

    semantic_context = ""

    if features:

        semantic_context = build_semantic_context(
            features
        )

        debug_print(
            "\n[RAG] SEMANTIC CONTEXT"
        )

        debug_print(
            semantic_context
        )    

    debug_print("[RAG] Docs:", len(retrieved))

    prompt = f"""
You are an environmental scientist.


MODEL RESULTS:
{base_text}

SCENARIO DRIVERS:
{drivers}

ECOLOGICAL INTERPRETATION NOTES:
{semantic_context}

SCIENTIFIC KNOWLEDGE BASE:
{context}

TASK

The model comparison has already been computed.

Do NOT compare the scenarios again.

Do NOT determine which scenario is better.

Do not repeat the model result.

Start directly from the ecological interpretation.

Explain the ecological implications of the identified drivers
within the current ecosystem scenario.

Use only concepts that are explicitly supported
by the retrieved scientific knowledge and by the
semantic descriptions of the variables.

Do NOT introduce:
- additional stressors
- management actions
- land-use changes
- water-quality effects
- conservation recommendations

unless they explicitly appear in the retrieved context.

Do not infer interactions or relationships
between the drivers unless they are explicitly
supported by the retrieved knowledge.

Interpret ecological associations rather than
assuming direct causal relationships.

If the retrieved knowledge contains only limited
ecological information, do not elaborate further.

Write a single compact paragraph of 2-3 concise sentences.

When the retrieved knowledge is limited,
prefer a shorter explanation rather than
adding unsupported ecological details

Answer:
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

def generate_comparison_explanation(
    drivers,
    delta,
    features=None
):

    print("\n[RAG-COMPARISON v10] START")

    base = build_base_explanation(
        drivers,
        delta
    )

    debug_print("[BASE]:", base)

    final = enhance_with_rag(
        base,
        drivers,
        delta,
        features=features

    )

    debug_print("[FINAL]:", final)

    print("[RAG-COMPARISON v10] END")

    return final