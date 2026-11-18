# -*- coding: utf-8 -*-

"""
RAG Delta — v39 (ecological interpretation separated from model results)

- Keeps ecological facts deterministic and task-local.
- The LLM generates only the ecological interpretation.
- Python appends the canonical, rounded risk result.
- A zero environmental change is not misclassified as a decrease.
- The Delta retrieval query focuses on ecological effects, not generic risk methodology.
"""

import math
import re
from knowledge.rag_pipeline import generate_answer

from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# DELTA SIGNIFICANCE
# ======================================================

def format_risk_delta_for_display(delta, decimals=3):
    """Format a risk-score difference for prompts without changing its source value.

    Three decimals are used for consistency with the displayed risk scores.
    Values that round to zero are rendered as 0.000, never -0.000 or scientific
    notation (for example, 1.1102230246251565e-16).
    """
    if delta is None:
        return None

    try:
        numeric = float(delta)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(numeric):
        return None

    rounded = round(numeric, decimals)
    if rounded == 0.0:  # also normalizes negative zero
        rounded = 0.0

    return rounded


def classify_delta(delta):

    if delta is None:
        return "moderate"

    d = abs(delta)

    if d < 0.01:
        return "negligible"

    elif d < 0.05:
        return "slight"

    elif d < 0.15:
        return "moderate"

    elif d < 0.35:
        return "strong"

    else:
        return "substantial"


# ======================================================
# BUILD FACTS
# ======================================================

def build_facts(drivers):

    facts = []

    for feature, v_from, v_to in drivers:

        name = feature.lower()
        delta = v_to - v_from

        # A zero change must not be treated as a decrease by the branches below.
        # Keep the fact ecological and neutral; do not infer gains or losses.
        if math.isclose(float(delta), 0.0, abs_tol=1e-12):
            if "temperature" in name:
                label = "temperature"
            elif "precipitation" in name:
                label = "precipitation"
            elif "evapotranspiration" in name:
                label = "evapotranspiration"
            elif "tree cover" in name:
                label = "tree cover"
            elif "grassland" in name:
                label = "grassland extent"
            elif "species" in name or "biodiversity" in name:
                label = "biodiversity"
            elif "productivity" in name or "phenology" in name:
                label = "vegetation productivity"
            elif "impervious" in name:
                label = "land imperviousness"
            elif "land use" in name:
                label = "land use change"
            else:
                label = feature
            facts.append(f"{label} remains unchanged")
            continue

        # --------------------------------------------------
        # TEMPERATURE
        # --------------------------------------------------

        if "temperature" in name:

            if delta > 0:

                facts += [
                    "temperature increases",
                    "higher evapotranspiration may occur",
                    "water availability may decrease",
                    "ecosystem stress may increase",
                ]

            else:

                facts += [
                    "temperature decreases",
                    "evapotranspiration may decrease",
                    "water availability may increase",
                    "ecosystem stress may decrease",
                ]

        # --------------------------------------------------
        # PRECIPITATION
        # --------------------------------------------------

        elif "precipitation" in name:

            if delta > 0:

                facts += [
                    "precipitation increases",
                    "water availability may increase",
                    "ecosystem stress may decrease",
                ]

            else:

                facts += [
                    "precipitation decreases",
                    "water availability may decrease",
                    "ecosystem stress may increase",
                ]

        # --------------------------------------------------
        # EVAPOTRANSPIRATION
        # --------------------------------------------------

        elif "evapotranspiration" in name:

            if delta > 0:

                facts += [
                    "evapotranspiration increases",
                    "water loss may increase",
                    "ecosystem stress may increase",
                ]

            else:

                facts += [
                    "evapotranspiration decreases",
                    "water loss may decrease",
                    "ecosystem stress may decrease",
                ]

        # --------------------------------------------------
        # TREE COVER
        # --------------------------------------------------

        elif "tree cover" in name:

            if delta > 0:

                facts += [
                    "tree cover increases",
                    "forest habitats may be better preserved",
                    "ecosystem resilience may increase",
                    "ecosystem structure may change",
                ]

            else:

                facts += [
                    "tree cover decreases",
                    "vegetation density may decrease",
                    "habitat conditions may deteriorate",
                    "ecosystem structure may change",
                ]

        # --------------------------------------------------
        # GRASSLAND
        # --------------------------------------------------

        elif "grassland" in name:

            if delta > 0:

                facts += [
                    "grassland extent increases",
                    "open habitat availability may increase",
                    "ecosystem composition may change",
                ]

            else:

                facts += [
                    "grassland extent decreases",
                    "open habitat availability may decrease",
                    "ecosystem composition may change",
                ]

        # --------------------------------------------------
        # BIODIVERSITY
        # --------------------------------------------------

        elif "species" in name or "biodiversity" in name:

            if delta > 0:

                facts += [
                    "biodiversity increases",
                    "ecosystem resilience may increase",
                    "ecosystem stress may decrease",
                ]

            else:

                facts += [
                    "biodiversity decreases",
                    "ecosystem resilience may decrease",
                    "ecosystem stress may increase",
                ]

        # --------------------------------------------------
        # PRODUCTIVITY
        # --------------------------------------------------

        elif "productivity" in name or "phenology" in name:

            if delta > 0:

                facts += [
                    "vegetation productivity increases",
                    "primary production may increase",
                    "ecosystem functioning may change",
                ]

            else:

                facts += [
                    "vegetation productivity decreases",
                    "primary production may decrease",
                    "ecosystem functioning may change",
                ]

        # --------------------------------------------------
        # IMPERVIOUSNESS / URBANIZATION
        # --------------------------------------------------

        elif "impervious" in name:

            if delta > 0:

                facts += [
                    "land imperviousness increases",
                    "surface sealing may increase",
                    "hydrological processes may be altered",
                ]

            else:

                facts += [
                    "land imperviousness decreases",
                    "surface sealing may decrease",
                    "hydrological processes may change",
                ]

        # --------------------------------------------------
        # LAND USE CHANGE
        # --------------------------------------------------

        elif "land use" in name:

            if delta > 0:

                facts += [
                    "land use change increases",
                    "ecosystem conditions may become more altered",
                    "ecological dynamics may change",
                ]

            else:

                facts += [
                    "land use change decreases",
                    "ecosystem conditions may remain more stable",
                    "ecological dynamics may change",
                ]

    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    return list(
        dict.fromkeys(facts)
    )

# ======================================================
# DELTA REPORT
# ======================================================

def build_delta_report(drivers, facts, delta=None):
    """Build scenario context for the LLM without exposing model-risk outputs."""
    feature, value_from, value_to = drivers[0]
    effects = "\n".join(f"• {fact}" for fact in facts)

    return f"""
============================================================
DIGITAL TWIN DELTA REPORT — ECOLOGICAL CONTEXT
============================================================

MODIFIED ENVIRONMENTAL VARIABLE
------------------------------------------------------------
{feature}

APPLIED MODIFICATION
------------------------------------------------------------
Initial value: {value_from}
Modified value: {value_to}

REPORTED ENVIRONMENTAL EFFECTS
------------------------------------------------------------
{effects}

OUTPUT SCOPE
------------------------------------------------------------
Write only the ecological interpretation of the reported effects.
Do not mention ecosystem risk, risk scores, risk classifications,
score variations, or model predictions. Python adds the quantitative
model result separately after this interpretation has been generated.
"""

# ======================================================
# ECOLOGICAL NOTES
# ======================================================

def build_delta_notes(drivers):

    feature, _, _ = drivers[0]

    return f"""
============================================================
ECOLOGICAL INTERPRETATION NOTES
============================================================

The reported environmental effects describe the
expected ecological implications of modifying
{feature} between two baseline-derived scenarios.

The retrieved scientific evidence should only be
used to explain the ecological relevance of the
reported environmental effects.

Do not infer additional environmental modifications,
ecological mechanisms or ecosystem responses that
are not reported by the Digital Twin.

The LLM output is only the ecological interpretation.
Do not answer the risk-score part of the user's request.
Do not mention ecosystem risk, a risk score, a risk level,
or any numerical model prediction. Python appends those results.
If the modified variable is unchanged, do not describe an increase,
decrease, loss, gain, or other directional ecological effect.
"""

# ======================================================
# DELTA SEMANTIC MAPPING FOR SCIENTIFIC RETRIEVAL
# ======================================================

# Maps technical Digital Twin variable names to the scientific concept
# used to search the scientific KB. This mapping is local to Delta;
# the global retriever is intentionally unchanged.
DELTA_RAG_CONCEPTS = (
    ("evapotranspiration", "evapotranspiration"),
    ("precipitation", "precipitation"),
    ("temperature", "temperature"),
    ("tree cover", "tree cover"),
    ("grassland", "grassland"),
    ("species", "biodiversity"),
    ("biodiversity", "biodiversity"),
    ("productivity", "ecosystem productivity"),
    ("phenology", "ecosystem productivity"),
    ("impervious", "land imperviousness"),
    ("land use", "land use"),
)


def get_delta_rag_concept(feature):
    """Translate a Digital Twin variable name into a scientific KB concept."""
    feature_lower = feature.lower()

    for keyword, concept in DELTA_RAG_CONCEPTS:
        if keyword in feature_lower:
            return concept

    # Safe fallback: preserve the original variable name if no mapping exists.
    return feature


# ======================================================
# PROMPT
# ======================================================

def build_legacy_prompt(facts):

    fact_text = "\n".join(
        [f"- {f}" for f in facts]
    )

    return f"""
    Rewrite the following facts into a concise environmental explanation.

    MODEL-DERIVED SCENARIO:    
    {fact_text}

    RULES:

    - Use ONLY these facts.
    - Do NOT introduce ecological processes that are not explicitly supported by the facts.
    - Do NOT introduce new concepts.

    - Avoid generic statements such as:
    - overall ecosystem health
    - environmental changes
    - ecological balance
    - ecosystem functioning

    unless these concepts are explicitly supported by the provided facts.

    - Produce exactly 1-2 concise sentences. State each environmental effect only once.
    - Do not add an introduction, a generic methodological comment, or a concluding summary.
    - Do NOT present associations as proven causal mechanisms.
    - Distinguish between ecological interpretation and model prediction.
    - Use cautious scientific language.
    - Keep the explanation concise and natural.
    - Do not use introductions.
    - Do NOT independently invent ecosystem risk changes.
    - Risk predictions may be added separately by the system.
    """


# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text):
    """Normalize the LLM answer and remove redundant summary sentences."""

    if not text:
        return ""

    text = text.strip()

    # Remove common introductory framing.
    text = re.sub(
        r"^(?:here is|this means|based on the provided information)[^:]*:\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("increases increases", "increases")
    text = text.replace("decreases decreases", "decreases")

    # Keep the first useful formulation of an idea and discard clear repeats.
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    kept = []

    def content_words(sentence):
        words = re.findall(r"[a-z0-9]+", sentence.lower())
        stopwords = {
            "the", "a", "an", "and", "or", "but", "if", "of", "to",
            "in", "on", "for", "with", "by", "from", "that", "this",
            "these", "those", "is", "are", "was", "were", "be", "been",
            "being", "may", "might", "could", "would", "should", "it",
            "its", "as", "at", "than", "however", "therefore"
        }
        return {word for word in words if word not in stopwords}

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # A summary phrase is usually redundant when it repeats prior content.
        if re.match(r"^(?:in summary|to summarize|overall|in conclusion)\b", sentence, re.I):
            candidate_words = content_words(sentence)
            if any(
                len(candidate_words & content_words(previous)) /
                max(1, len(candidate_words | content_words(previous))) >= 0.30
                for previous in kept
            ):
                continue

        current_words = content_words(sentence)
        redundant = False
        for previous in kept:
            previous_words = content_words(previous)
            if not current_words or not previous_words:
                continue
            overlap = len(current_words & previous_words) / max(
                1, len(current_words | previous_words)
            )
            if overlap >= 0.55:
                redundant = True
                break

        if not redundant:
            kept.append(sentence)

    # Avoid long answers even if the model adds several distinct but peripheral points.
    return " ".join(kept[:2]).strip()



# ======================================================
# REMOVE MODEL-RISK CONTENT FROM LLM INTERPRETATION
# ======================================================

def remove_risk_sentences(text):
    """Keep the LLM's ecological prose separate from the Python-built result."""
    if not text:
        return ""

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text.strip())
    kept = []
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        # Any sentence mentioning risk belongs to the separate deterministic section.
        if re.search(r"\brisk\b|\brisk-score\b|\bscore\b|\bmodel prediction\b", sentence, re.I):
            continue
        kept.append(sentence)
    return " ".join(kept).strip()

# ======================================================
# OUTPUT VALIDATION
# ======================================================

def is_valid(text):

    if not text:
        return False

    if len(text) < 20:
        return False

    if "Interpretation not available" in text:
        return False

    return True


# ======================================================
# ADD RISK SENTENCE
# ======================================================

def _format_score(value):
    try:
        return f"{float(value):.3f}"
    except (TypeError, ValueError):
        return str(value)


def add_risk_alignment(text, delta, drivers=None, model_results=None):
    """Render ecological interpretation and model estimates as separate sections.

    All quantitative values come from Python/model_results; the LLM contributes
    only the ecological interpretation. Keep the text layout consistent for
    positive, negative, and zero changes.

    Add a sensitivity notice when an environmental variable changes but the
    displayed surrogate-model risk variation is zero.
    """
    ecological_text = remove_risk_sentences(text).strip()
    display_delta = format_risk_delta_for_display(delta)

    sections = []
    if ecological_text:
        sections.append(
            "**Ecological interpretation**\n" + ecological_text
        )

    if display_delta is None:
        return "\n\n".join(sections) if sections else ""

    if display_delta > 0:
        direction = "Increase"
        delta_text = f"+{display_delta:.3f}"
    elif display_delta < 0:
        direction = "Decrease"
        delta_text = f"{display_delta:.3f}"
    else:
        direction = "No substantial change"
        delta_text = "0.000"

    estimate_lines = ["**Model estimate**"]

    required = {"score_from", "score_to", "risk_from", "risk_to"}
    if model_results and required.issubset(model_results):
        estimate_lines.extend([
            f"Initial ecosystem risk: {_format_score(model_results['score_from'])} ({model_results['risk_from']})",
            f"Final ecosystem risk: {_format_score(model_results['score_to'])} ({model_results['risk_to']})",
        ])

    estimate_lines.extend([
        f"Predicted risk change: {direction}",
        f"Risk-score change: {delta_text}",
    ])

    # --------------------------------------------------
    # SURROGATE MODEL SENSITIVITY NOTICE
    # --------------------------------------------------

    environmental_change = False

    for _, value_from, value_to in (drivers or []):
        try:
            if not math.isclose(
                float(value_from),
                float(value_to),
                rel_tol=0.0,
                abs_tol=1e-12
            ):
                environmental_change = True
                break
        except (TypeError, ValueError):
            continue

    if environmental_change and display_delta == 0.0:
        estimate_lines.extend([
            "",
            "**Model sensitivity notice**",
            (
                "Despite the environmental modification, the predicted "
                "risk change is zero at the displayed precision. This result "
                "may reflect limitations in the sensitivity of the surrogate "
                "Random Forest model currently used during the system "
                "development phase. Therefore, the absence of a predicted "
                "risk variation should not necessarily be interpreted as "
                "evidence that the environmental modification has no "
                "ecological effect."
            ),
        ])

    sections.append("\n".join(estimate_lines))

    return "\n\n".join(sections)

# ======================================================
# FALLBACK
# ======================================================

def fallback(facts, delta, drivers=None, model_results=None):
    if facts:
        sentence = " and ".join(facts[:2]) + "."
    else:
        sentence = "No clear environmental pattern detected."

    return add_risk_alignment(
        sentence,
        delta,
        drivers=drivers,
        model_results=model_results,
    )


# ======================================================
# MAIN
# ======================================================

def generate_delta_explanation(
    question,
    drivers,
    delta=None,
    features=None,
    model_results=None
):

    print("\n[RAG-DELTA v39] START")

    facts = build_facts(drivers)

    debug_print("[FACTS]:", facts)

    if not facts:
        return add_risk_alignment(
            "No clear environmental pattern detected.",
            delta,
            drivers=drivers,
            model_results=model_results,
        )

    # --------------------------------------------------
    # RETRIEVAL QUERY
    # --------------------------------------------------

    feature = drivers[0][0]
    rag_concept = get_delta_rag_concept(feature)
    rag_query = f"{rag_concept} ecological effects habitat vegetation"

    debug_print("[DELTA RAG CONCEPT]:", rag_concept)

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if USE_LEGACY_PROMPTS:

        prompt = build_legacy_prompt(
            facts
        )

    else:

        delta_report = build_delta_report(
            drivers,
            facts,
        )

        delta_notes = build_delta_notes(drivers)

        prompt = (
            build_prompt("delta")
            + f"""

    ECOLOGICAL INTERPRETATION SUBTASK:
    Describe the ecological implications of changing {feature} from
    {drivers[0][1]} to {drivers[0][2]}. Use the supplied facts and only
    directly relevant retrieved scientific evidence. Do not answer the
    ecosystem-risk prediction part of the original request; Python will
    append the formatted model result separately.

    {delta_report}

    {delta_notes}

    ============================================================
    RETRIEVED SCIENTIFIC EVIDENCE
    ============================================================
    """
        )

    prompt_question = (
        f"Explain only the ecological implications of changing {feature} "
        f"from {drivers[0][1]} to {drivers[0][2]}. Do not report risk "
        "scores, risk levels, or model predictions."
    )

    try:

        if DEBUG:

            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)

            print("\n========== RETRIEVAL QUERY ==========\n")
            print(rag_query)

            print("\n=====================================\n")

        raw = generate_answer(
            question=rag_query,
            features=features,
            extra_prompt=prompt,
            prompt_question=prompt_question,
        )

        print("[RAW]:", raw)

        if not is_valid(raw):
            return fallback(facts, delta, drivers, model_results)

        cleaned = remove_risk_sentences(clean_output(raw))
        if not is_valid(cleaned):
            cleaned = " and ".join(facts[:2]) + "."

        final = add_risk_alignment(
            cleaned,
            delta,
            drivers=drivers,
            model_results=model_results,
        )

        print("[FINAL]:", final)

        print("[RAG-DELTA v39] END")

        return final

    except Exception as e:

        print("[RAG ERROR]", e)

        return fallback(facts, delta, drivers, model_results)