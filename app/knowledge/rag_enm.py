# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG ENM — Ecological Explanation Layer v8

✔ Uses centralized RAG pipeline
✔ Strong fallback
✔ Ecological interpretation only
✔ No repetition of ENM metrics
✔ Uses pre-computed driver interpretation
✔ Uses scenario comparison
✔ Interprets increase / decrease / stability
✔ Prevents unsupported climate narratives
"""

from knowledge.rag_pipeline import generate_answer
from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)

DEBUG = True

# ======================================================
# FALLBACK
# ======================================================

def fallback_explanation(
    species,
    drivers,
    model_summary=None
):

    if not drivers:

        return (
            f"Habitat suitability for {species} "
            f"depends on environmental conditions "
            f"represented in the model."
        )

    driver_text = ", ".join(drivers[:3])

    return (
        f"Habitat suitability for {species} is "
        f"influenced by environmental variables such as "
        f"{driver_text}, which define the ecological "
        f"conditions supporting species presence."
    )


# ======================================================
# DRIVER INTERPRETATION
# ======================================================

def build_driver_interpretation(
    driver_analysis
):

    if not driver_analysis:

        return ""

    structure = driver_analysis.get(
        "driver_structure",
        ""
    )

    dominant_driver = driver_analysis.get(
        "dominant_driver",
        ""
    )

    if (
        structure ==
        "single dominant driver"
    ):

        return (
            f"Habitat suitability is primarily  "
            f"associated  with {dominant_driver}."
        )

    elif (
        structure ==
        "dominant driver with secondary influences"
    ):

        return (
            f"{dominant_driver} is the dominant "
            f"environmental variable associated with "
            f"habitat suitability, although other "
            f"variables also contribute."
        )

    elif (
        structure ==
        "multiple co-dominant drivers"
    ):

        return (
            "Multiple environmental drivers are "
            "similarly associated with habitat suitability, "
            "with no single dominant factor."
        )

    return ""

# ======================================================
# QUESTION FOCUS
# ======================================================

def build_focus_text(question):

    q = question.lower()

    # ----------------------------------------------
    # Driver importance
    # ----------------------------------------------

    if any(k in q for k in [

        "driver",
        "drivers",

        "dominant",
        "dominate",

        "importance",
        "important",

        "control",
        "controls",
        "controlled",

        "environmental factor",
        "main factor",
        "primary factor",

        "most important"

    ]):

        return """
Focus on the reported environmental drivers.

Explain only the reported driver structure and the ecological meaning of the reported driver associations.
Assume that the reported driver ranking has already been presented to the user.

Do not repeat or enumerate the reported drivers unless this is necessary to answer the question.

Do not discuss habitat distribution, habitat topology, or model performance unless they are necessary to answer the question.
"""

    # ----------------------------------------------
    # Model performance
    # ----------------------------------------------

    if any(k in q for k in [

        "auc",
        "accuracy",
        "performance",
        "reliable",
        "reliability",
        "confidence"

    ]):

        return """
Focus on the reported model performance.

Explain what the reported evaluation metrics indicate about model reliability.

Assume that the reported metric values have already been presented to the user.

Do not repeat or summarize the reported metric values unless necessary to answer the question.

Do not discuss habitat distribution, habitat topology, or environmental drivers unless they are directly relevant to model performance.
"""

    # ----------------------------------------------
    # Habitat topology
    # ----------------------------------------------

    if any(k in q for k in [

        "fragment",
        "fragmentation",
        "connectivity",
        "connected",
        "hotspot",
        "patch",
        "topology"

    ]):

        return """
Focus on the reported habitat topology.

Interpret hotspot organization, connectivity, and fragmentation.

Do not discuss model performance or environmental drivers unless they directly explain the reported spatial pattern.
"""

    # ----------------------------------------------
    # Habitat distribution
    # ----------------------------------------------

    return """
Focus on the reported habitat distribution.

Interpret the reported habitat suitability pattern.

Do not discuss model performance, habitat topology, or environmental drivers unless they directly explain the reported distribution.
"""

# ======================================================
# PROMPT
# ======================================================

def build_legacy_prompt(
    species,
    model_summary,
    driver_interpretation,
    driver_text
):
    return f"""
You are an ecological modeler.

SPECIES:
{species}

MODEL RESULTS:
{model_summary}

PRECOMPUTED ECOLOGICAL INTERPRETATION:

{driver_interpretation}

ENVIRONMENTAL DRIVERS:
(sorted by importance)

{driver_text}

TASK:

Provide an ecological explanation of the
predicted distribution pattern.

IMPORTANT:

Do NOT repeat information already reported
in MODEL RESULTS.

Do NOT repeat:

- habitat extent
- hotspot count
- hotspot size
- hotspot structure
- connectivity assessment
- fragmentation level
- suitability percentages
- AUC values
- comparison metrics

These have already been reported.

Your role is to explain WHY the species
shows this distribution pattern and, when
available, WHY the projected future pattern
differs from current conditions.

SCENARIO COMPARISON:

Comparison information has already been
computed and is reported in MODEL RESULTS.

If comparison information indicates:

- habitat_delta > 0:
  explain the ecological reasons that may
  support habitat expansion

- habitat_delta < 0:
  explain the ecological reasons that may
  support habitat contraction

- habitat_delta approximately 0:
  explain why habitat suitability appears
  broadly stable under the future scenario

If comparison indicates little or no change:

- describe the distribution as stable
- do not describe major redistribution
- do not describe strong range shifts

Do not invent changes that are not supported
by the comparison.

Do not claim that temperature,
precipitation, conductivity, salinity,
fragmentation, connectivity, or habitat
extent increase or decrease unless that
change is explicitly supported by the
provided results.

Use:

- PRECOMPUTED ECOLOGICAL INTERPRETATION
- ENVIRONMENTAL DRIVERS
- MODEL RESULTS
- retrieved ecological knowledge

The precomputed interpretation is already
correct and should not be contradicted.

If it states that no single environmental
factor dominates, do not describe any
variable as dominant.

Do not introduce environmental drivers,
pressures, stressors, ecological mechanisms,
or causal factors that are not explicitly
supported by:

- PRECOMPUTED ECOLOGICAL INTERPRETATION
- ENVIRONMENTAL DRIVERS
- MODEL RESULTS
- retrieved ecological knowledge

If information is not provided,
do not infer it.

Focus on:

- habitat preferences
- environmental constraints
- ecological requirements
- environmental gradients
- species-environment relationships
- future habitat stability or change

RULES:

- Focus on ecological interpretation
- Focus on species-environment relationships
- Use ecological reasoning
- Be realistic and scientifically plausible
- Use 2–4 sentences
- No lists
- No formatting
- Do not invent variables not listed
"""


# ======================================================
# MAIN
# ======================================================

def generate_enm_explanation(
    question,
    drivers,
    species,
    model_summary=None,
    driver_analysis=None
):

    print("\n[RAG-ENM] START")

    # --------------------------------------------------
    # FORMAT DRIVERS
    # --------------------------------------------------

    driver_text = "\n".join(
        [f"- {d}" for d in drivers]
    )

    if model_summary is None:

        model_summary = (
            "No model summary available."
        )

    # --------------------------------------------------
    # PRECOMPUTED DRIVER INTERPRETATION
    # --------------------------------------------------

    driver_interpretation = (
        build_driver_interpretation(
            driver_analysis
        )
    )

    question_focus = build_focus_text(
        question
    )

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if USE_LEGACY_PROMPTS:

        extra_prompt = build_legacy_prompt(
            species,
            model_summary,
            driver_interpretation,
            driver_text
        )

    else:

        extra_prompt = (
            build_prompt("enm")
            + f"""

    SPECIES:
    {species}

    MODEL RESULTS:
    {model_summary}

    PRECOMPUTED ECOLOGICAL INTERPRETATION:

    {driver_interpretation}

    ENVIRONMENTAL DRIVERS:
    (sorted by importance)

    {driver_text}

    QUESTION FOCUS:

    {question_focus}

    """
    )

    # --------------------------------------------------
    # CALL RAG
    # --------------------------------------------------

    try:
        if DEBUG:

            print("\n========== EXTRA PROMPT ==========\n")
            print(extra_prompt)
            print("\n==================================\n")

        answer = generate_answer(
            question=question,
            extra_prompt=extra_prompt
        )

        print("\n[RAG-ENM] OUTPUT:")
        print(answer)

        if (
            not answer
            or "unavailable" in answer.lower()
        ):

            return fallback_explanation(
                species,
                drivers,
                model_summary
            )

        print("[RAG-ENM] END\n")

        return answer

    except Exception as e:

        print("\n🔥 RAG-ENM ERROR:")
        print(e)

        return fallback_explanation(
            species,
            drivers,
            model_summary
        )