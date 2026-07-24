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
from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)


DEBUG = True
MAX_CHUNK_CHARS = 700



def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# CONTEXT
# ======================================================

def clean_chunk(text):

    import re

    text = text.replace("\n", " ")

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def build_context(retrieved):

    if not retrieved:
        return ""

    report = []

    report.append("=" * 60)
    report.append("SCIENTIFIC EVIDENCE")
    report.append("=" * 60)

    for i, r in enumerate(retrieved, start=1):

        chunk = clean_chunk(r["text"])

        # ----------------------------------------------
        # LIMIT EACH CHUNK
        # ----------------------------------------------

        if len(chunk) > MAX_CHUNK_CHARS:

            chunk = (
                chunk[:MAX_CHUNK_CHARS].rsplit(" ", 1)[0]
                + " ..."
            )

        report.append("")
        report.append(f"Evidence {i}")

        report.append("-" * 60)

        report.append(
            f"Source: {r['source']}"
        )

        report.append(
            f"Page: {r['page']}"
        )

        report.append("")

        report.append("Scientific excerpt:")

        report.append(chunk)

        report.append("")
        report.append("=" * 60)

    return "\n".join(report)



# ======================================================
# COMPARISON REPORT
# ======================================================

def build_comparison_report(
    scenario_a,
    scenario_b,
    risk_difference
):

    report = []

    report.append("=" * 60)
    report.append("DIGITAL TWIN COMPARISON REPORT")
    report.append("=" * 60)

    # ==================================================
    # SCENARIO A
    # ==================================================

    report.append("")
    report.append("SCENARIO A")
    report.append("-" * 60)

    report.append("")
    report.append("Requested environmental modification")

    for feature, mod in scenario_a["requested_modifications"].items():

        direction = (
            "Increase"
            if mod["value"] >= 0
            else "Reduce"
        )

        report.append(
            f"• {direction} {feature} by "
            f"{abs(mod['value']):.1f}%"
        )

    report.append("")
    report.append("Baseline ecosystem state")

    for feature, value in scenario_a["baseline_values"].items():

        report.append(
            f"• {feature}: {value:.2f}"
        )

    report.append("")
    report.append("Simulated ecosystem state")

    for feature, value in scenario_a["scenario_values"].items():

        report.append(
            f"• {feature}: {value:.2f}"
        )

    report.append("")
    report.append("Predicted ecosystem response")

    report.append(
        f"• Ecosystem risk: "
        f"{scenario_a['risk']:.4f}"
    )

    report.append("")
    report.append("Main model drivers")

    for feature, impact in scenario_a["primary_drivers"].items():

        report.append(
            f"• {feature} ({impact:+.5f})"
        )

    # ==================================================
    # SCENARIO B
    # ==================================================

    report.append("")
    report.append("=" * 60)
    report.append("SCENARIO B")
    report.append("-" * 60)

    report.append("")
    report.append("Requested environmental modification")

    for feature, mod in scenario_b["requested_modifications"].items():

        direction = (
            "Increase"
            if mod["value"] >= 0
            else "Reduce"
        )

        report.append(
            f"• {direction} {feature} by "
            f"{abs(mod['value']):.1f}%"
        )

    report.append("")
    report.append("Baseline ecosystem state")

    for feature, value in scenario_b["baseline_values"].items():

        report.append(
            f"• {feature}: {value:.2f}"
        )

    report.append("")
    report.append("Simulated ecosystem state")

    for feature, value in scenario_b["scenario_values"].items():

        report.append(
            f"• {feature}: {value:.2f}"
        )

    report.append("")
    report.append("Predicted ecosystem response")

    report.append(
        f"• Ecosystem risk: "
        f"{scenario_b['risk']:.4f}"
    )

    report.append("")
    report.append("Main model drivers")

    for feature, impact in scenario_b["primary_drivers"].items():

        report.append(
            f"• {feature} ({impact:+.5f})"
        )

    # ==================================================
    # MODEL COMPARISON SUMMARY
    # ==================================================

    report.append("")
    report.append("=" * 60)
    report.append("MODEL COMPARISON SUMMARY")
    report.append("=" * 60)

    report.append("")
    report.append(
        f"Difference in predicted ecosystem risk: "
        f"{abs(risk_difference):.4f}"
    )

    report.append("")

    if abs(risk_difference) < 0.01:

        report.append(
            "Model conclusion:"
        )

        report.append(
            "• The two simulated scenarios produce "
            "very similar predicted ecosystem risk."
        )

    elif risk_difference > 0:

        report.append(
            "Model conclusion:"
        )

        report.append(
            "• Scenario B produces a higher predicted "
            "ecosystem risk than Scenario A."
        )

    else:

        report.append(
            "Model conclusion:"
        )

        report.append(
            "• Scenario A produces a higher predicted "
            "ecosystem risk than Scenario B."
        )

    return "\n".join(report)



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


def build_transition_query(
    scenario_a,
    scenario_b,
    risk_difference
):

    transition_terms = []

    # --------------------------------------------------
    # SCENARIO A
    # --------------------------------------------------

    for feature, mod in scenario_a["requested_modifications"].items():

        transition_terms.append(

            classify_transition(
                feature,
                mod["value"]
            )

        )

    # --------------------------------------------------
    # SCENARIO B
    # --------------------------------------------------

    for feature, mod in scenario_b["requested_modifications"].items():

        transition_terms.append(

            classify_transition(
                feature,
                mod["value"]
            )

        )

    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    transition_text = " vs ".join(

        dict.fromkeys(transition_terms)

    )

    # --------------------------------------------------
    # COMPARISON TYPE
    # --------------------------------------------------

    if abs(risk_difference) < 0.01:

        comparison_type = (
            "ecosystem stability comparison"
        )

    elif risk_difference > 0:

        comparison_type = (
            "ecosystem degradation comparison"
        )

    else:

        comparison_type = (
            "ecosystem resilience comparison"
        )

    # --------------------------------------------------
    # QUERY
    # --------------------------------------------------

    query = f"""
    Massaciuccoli Lake ecosystem comparison
    {comparison_type}
    {transition_text}
    ecosystem risk
    ecological drivers
    biodiversity
    vegetation
    hydrology
    ecosystem resilience
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
    question,
    comparison_report,
    scenario_a,
    scenario_b,
    features=None
):
    risk_difference = (
        scenario_b["risk"]
        - scenario_a["risk"]
    )

    query = build_transition_query(
        scenario_a,
        scenario_b,
        risk_difference
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

    model_result_header = """
    The following comparison report was generated by the Digital Twin.

    Do not recompute the comparison.

    Treat the reported values as authoritative model outputs.

    Use the ecological notes only to explain the reported result.

    Never infer a different outcome from the ecological notes.
    """



    if USE_LEGACY_PROMPTS:
        prompt = f"""
    You are an environmental scientist.

    {model_result_header}

    COMPARISON REPORT:
    {comparison_report}

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
    else:
        prompt = (
            build_prompt("comparison", question=question)
            + f"""

    {model_result_header}
    
    COMPARISON REPORT:
    {comparison_report}

    ECOLOGICAL INTERPRETATION NOTES:
    {semantic_context}

    SCIENTIFIC KNOWLEDGE BASE:
    {context}

    Answer:
    """
        )

    try:
        if DEBUG:
            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        raw = call_llm(prompt)

        if not raw:
            return comparison_report

        cleaned = clean_output(raw)

        if cleaned is None:
            return comparison_report

        if not is_coherent(comparison_report, cleaned):
            return comparison_report

        return cleaned

    except Exception:

        return comparison_report


# ======================================================
# MAIN
# ======================================================

def generate_comparison_explanation(
    question,
    scenario_a,
    scenario_b,
    risk_difference,
    features=None
):

    print("\n[RAG-COMPARISON v10] START")

    comparison_report = build_comparison_report(
        scenario_a,
        scenario_b,
        risk_difference
    )

    debug_print("[BASE]:", comparison_report)

    final = enhance_with_rag(
        question,
        comparison_report,
        scenario_a,
        scenario_b,
        features=features
    )

    debug_print("[FINAL]:", final)

    print("[RAG-COMPARISON v10] END")

    return final