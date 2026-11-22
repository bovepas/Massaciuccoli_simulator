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

def format_risk_delta_for_display(delta, decimals=4):
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

# ======================================================
# RF SENSITIVITY — DELTA ZERO
# ======================================================

ZERO_DELTA_TOLERANCE = 1e-4


# Evidenze sperimentali disponibili.
#
# ATTENZIONE:
# 14% indica una perturbazione pari al 14% del range osservato
# della feature, NON un aumento di 14 punti percentuali.
#
# Il risultato positivo è stato osservato sul baseline sintetico.
# Il test spaziale non lo ha confermato: il clipping ha limitato
# una parte rilevante delle perturbazioni.

RF_SENSITIVITY_EVIDENCE = {
    # Spatial experiment: 49,382 cells; one feature at a time; +/- 2% of
    # observed range. Percentages are based on the summary CSV.
    # "changed_cells_pct" uses all cells; "changed_perturbed_pct" uses only
    # cells where the feature value actually changed.
    # Synthetic-baseline results are retained as complementary evidence.
    ("impervious", "increase"): {
        "status": "no_change_observed",
        "spatial_changed_cells_pct": 0.00,
        "spatial_changed_perturbed_pct": 0.00,
        "spatial_feature_perturbed_pct": 21.19,
        "spatial_clipping_pct": 78.82,
        "spatial_score_increased_pct_among_perturbed": 0.00,
        "spatial_score_decreased_pct_among_perturbed": 0.00,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 14},
    },
    ("impervious", "decrease"): {
        "status": "no_change_observed",
        "spatial_changed_cells_pct": 0.00,
        "spatial_changed_perturbed_pct": 0.00,
        "spatial_feature_perturbed_pct": 79.02,
        "spatial_clipping_pct": 20.98,
        "spatial_score_increased_pct_among_perturbed": 0.00,
        "spatial_score_decreased_pct_among_perturbed": 0.00,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "no_response_observed"},
    },
    ("tree cover", "increase"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 4.56,
        "spatial_changed_perturbed_pct": 4.57,
        "spatial_feature_perturbed_pct": 99.74,
        "spatial_clipping_pct": 0.37,
        "spatial_score_increased_pct_among_perturbed": 3.20,
        "spatial_score_decreased_pct_among_perturbed": 1.37,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "no_response_observed"},
    },
    ("tree cover", "decrease"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 4.56,
        "spatial_changed_perturbed_pct": 15.98,
        "spatial_feature_perturbed_pct": 28.53,
        "spatial_clipping_pct": 71.48,
        "spatial_score_increased_pct_among_perturbed": 5.03,
        "spatial_score_decreased_pct_among_perturbed": 10.95,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "no_response_observed"},
    },
    ("productivity", "increase"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 17.82,
        "spatial_changed_perturbed_pct": 17.82,
        "spatial_feature_perturbed_pct": 100.00,
        "spatial_clipping_pct": 0.00,
        "spatial_score_increased_pct_among_perturbed": 11.25,
        "spatial_score_decreased_pct_among_perturbed": 6.57,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 4},
    },
    ("productivity", "decrease"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 15.15,
        "spatial_changed_perturbed_pct": 15.16,
        "spatial_feature_perturbed_pct": 99.91,
        "spatial_clipping_pct": 6.35,
        "spatial_score_increased_pct_among_perturbed": 5.75,
        "spatial_score_decreased_pct_among_perturbed": 9.41,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 6},
    },
    ("temperature", "increase"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 0.47,
        "spatial_changed_perturbed_pct": 0.48,
        "spatial_feature_perturbed_pct": 98.50,
        "spatial_clipping_pct": 1.50,
        "spatial_score_increased_pct_among_perturbed": 0.38,
        "spatial_score_decreased_pct_among_perturbed": 0.10,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 6},
    },
    ("temperature", "decrease"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 0.14,
        "spatial_changed_perturbed_pct": 0.16,
        "spatial_feature_perturbed_pct": 90.08,
        "spatial_clipping_pct": 9.92,
        "spatial_score_increased_pct_among_perturbed": 0.10,
        "spatial_score_decreased_pct_among_perturbed": 0.06,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "no_response_observed"},
    },
    ("evapotranspiration", "increase"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 0.93,
        "spatial_changed_perturbed_pct": 0.96,
        "spatial_feature_perturbed_pct": 97.30,
        "spatial_clipping_pct": 2.70,
        "spatial_score_increased_pct_among_perturbed": 0.35,
        "spatial_score_decreased_pct_among_perturbed": 0.61,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "no_response_observed"},
    },
    ("evapotranspiration", "decrease"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 0.59,
        "spatial_changed_perturbed_pct": 0.60,
        "spatial_feature_perturbed_pct": 98.50,
        "spatial_clipping_pct": 1.50,
        "spatial_score_increased_pct_among_perturbed": 0.56,
        "spatial_score_decreased_pct_among_perturbed": 0.04,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 26},
    },
    ("precipitation", "increase"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 0.21,
        "spatial_changed_perturbed_pct": 0.23,
        "spatial_feature_perturbed_pct": 93.47,
        "spatial_clipping_pct": 6.53,
        "spatial_score_increased_pct_among_perturbed": 0.03,
        "spatial_score_decreased_pct_among_perturbed": 0.20,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 20},
    },
    ("precipitation", "decrease"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 1.18,
        "spatial_changed_perturbed_pct": 1.29,
        "spatial_feature_perturbed_pct": 91.13,
        "spatial_clipping_pct": 8.87,
        "spatial_score_increased_pct_among_perturbed": 1.26,
        "spatial_score_decreased_pct_among_perturbed": 0.04,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "no_response_observed"},
    },
    ("species", "increase"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 9.41,
        "spatial_changed_perturbed_pct": 9.42,
        "spatial_feature_perturbed_pct": 99.87,
        "spatial_clipping_pct": 0.16,
        "spatial_score_increased_pct_among_perturbed": 6.56,
        "spatial_score_decreased_pct_among_perturbed": 2.87,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 2},
    },
    ("species", "decrease"): {
        "status": "spatially_observed",
        "spatial_changed_cells_pct": 9.44,
        "spatial_changed_perturbed_pct": 9.45,
        "spatial_feature_perturbed_pct": 99.99,
        "spatial_clipping_pct": 0.02,
        "spatial_score_increased_pct_among_perturbed": 3.24,
        "spatial_score_decreased_pct_among_perturbed": 6.20,
        "spatial_perturbation_pct_of_range": 2,
        "synthetic_baseline": {"status": "response_observed", "first_change_pct_of_range": 4},
    },
}


def is_zero_rf_delta(delta, tolerance=ZERO_DELTA_TOLERANCE):
    """
    True se il delta RF è numericamente trascurabile.

    None o valori non numerici non vengono considerati zero:
    indicano un risultato non disponibile.
    """
    if delta is None:
        return False

    try:
        value = float(delta)
    except (TypeError, ValueError):
        return False

    return math.isfinite(value) and abs(value) < tolerance


def get_change_direction(value_from, value_to):
    """
    Ricava la direzione della variazione ambientale dai valori
    iniziale e finale, indipendentemente dal delta RF.
    """
    try:
        start = float(value_from)
        end = float(value_to)
    except (TypeError, ValueError):
        return None

    if end > start:
        return "increase"

    if end < start:
        return "decrease"

    return None


def get_driver_change(drivers):
    """
    Restituisce feature, valori e direzione del primo driver Delta.
    Il task Delta considera una sola variabile.
    """
    if not drivers:
        return None

    try:
        feature, value_from, value_to = drivers[0]
    except (TypeError, ValueError):
        return None

    direction = get_change_direction(value_from, value_to)

    if direction is None:
        return None

    return {
        "feature": str(feature),
        "value_from": value_from,
        "value_to": value_to,
        "direction": direction,
    }


def get_rf_sensitivity_evidence(feature, direction):
    """
    Recupera esclusivamente evidenze sperimentali della stessa
    feature e della stessa direzione.
    """
    feature_lower = str(feature).lower()

    for (feature_key, tested_direction), evidence in RF_SENSITIVITY_EVIDENCE.items():
        if feature_key in feature_lower and tested_direction == direction:
            return evidence

    return None


def build_sensitivity_notice(drivers, delta):
    """
    Build a notice for a negligible RF delta.

    The spatial experiment is the primary evidence. Synthetic-baseline
    results are retained and reported separately as complementary evidence.
    """
    if not is_zero_rf_delta(delta):
        return []

    change = get_driver_change(drivers)
    if change is None:
        return []

    feature = change["feature"]
    direction = change["direction"]
    evidence = get_rf_sensitivity_evidence(feature, direction)

    notice = [
        "**Model sensitivity notice**",
        (
            f"The requested {direction} in {feature} produced no substantial "
            "change in the RF risk score."
        ),
    ]

    if evidence is None:
        notice.extend([
            "No matching feature- and direction-specific sensitivity record is available.",
            (
                "The zero RF variation must not be interpreted as proof "
                "that the variable has no ecological relevance."
            ),
        ])
        return notice

    changed_all = evidence["spatial_changed_cells_pct"]
    changed_perturbed = evidence["spatial_changed_perturbed_pct"]
    feature_perturbed = evidence["spatial_feature_perturbed_pct"]
    clipping = evidence["spatial_clipping_pct"]
    step = evidence["spatial_perturbation_pct_of_range"]
    score_up = evidence["spatial_score_increased_pct_among_perturbed"]
    score_down = evidence["spatial_score_decreased_pct_among_perturbed"]

    notice.append(
        (
            f"In the spatial sensitivity experiment, a {direction} perturbation "
            f"equal to {step}% of the feature's observed range changed the RF "
            f"score in {changed_all:.2f}% of all cells. Among cells where the "
            f"feature value was actually modified, {changed_perturbed:.2f}% "
            "showed a score change."
        )
    )
    notice.append(
        (
            f"The feature was effectively modified in {feature_perturbed:.2f}% "
            f"of valid cells; {clipping:.2f}% of valid feature values were "
            "clipped at the observed bounds."
        )
    )

    if evidence["status"] == "spatially_observed":
        notice.append(
            (
                f"Among cells with an actual feature perturbation, the RF score "
                f"increased in {score_up:.2f}% and decreased in {score_down:.2f}%. "
                "The response is spatially heterogeneous, not uniformly directional."
            )
        )
    else:
        notice.append(
            (
                "No RF score changes were observed in the spatial test for this "
                "feature and direction. This finding is limited to the tested "
                "perturbation and dataset conditions; clipping reduced the "
                "number of cells that could be perturbed."
            )
        )

    synthetic = evidence.get("synthetic_baseline")
    if synthetic:
        if synthetic["status"] == "response_observed":
            threshold = synthetic.get("first_change_pct_of_range")
            if threshold is not None:
                notice.append(
                    (
                        "A separate test at one synthetic baseline detected an "
                        f"RF response at a perturbation of {threshold}% of the "
                        "observed feature range. This is complementary evidence "
                        "from a single baseline and is not directly equivalent "
                        "to the spatial experiment."
                    )
                )
        elif synthetic["status"] == "no_response_observed":
            notice.append(
                (
                    "The separate synthetic-baseline test did not detect an RF "
                    "response in this direction within its tested range."
                )
            )

    notice.append(
        (
            "These experiments measure sensitivity of the RF surrogate, not "
            "ecological causality, and do not alter the zero RF result for the "
            "requested scenario. Zero RF variation is not evidence that the "
            "variable has no ecological relevance."
        )
    )
    return notice



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
    """
    Describe only the simulated feature modification.

    This function must not infer ecological effects or mechanisms.
    Those interpretations must come from relevant retrieved evidence.
    """
    if not drivers:
        return []

    facts = []

    for feature, value_from, value_to in drivers:
        facts.append(
            f"The Digital Twin feature '{feature}' changes "
            f"from {value_from} to {value_to}."
        )

    return facts


# ======================================================
# DELTA REPORT
# ======================================================

def build_delta_report(drivers, facts, delta=None):
    """Build a neutral scenario definition for the ecological interpretation."""
    if not drivers:
        return "No valid feature modification was supplied."

    feature, value_from, value_to = drivers[0]
    scenario = "\n".join(f"• {fact}" for fact in facts)

    return f"""
============================================================
DIGITAL TWIN DELTA REPORT — SCENARIO DEFINITION
============================================================

MODIFIED DIGITAL TWIN FEATURE
------------------------------------------------------------
{feature}

APPLIED MODIFICATION
------------------------------------------------------------
Initial feature value: {value_from}
Modified feature value: {value_to}

SCENARIO DESCRIPTION
------------------------------------------------------------
{scenario}

INTERPRETATION SCOPE
------------------------------------------------------------
The values above describe a change in the Digital Twin feature.
Do not automatically interpret this as an equivalent change in
the underlying physical or ecological variable. In particular,
do not infer a direction or magnitude for a physical process
unless the retrieved scientific evidence supports that relationship.

Use retrieved scientific evidence to discuss only ecological
implications that are relevant to this feature modification.
Distinguish documented relationships from possible interpretations
and explicitly acknowledge when the retrieved evidence is insufficient.

Do not mention ecosystem risk, risk scores, risk classifications,
score variations, or model predictions. Python adds the quantitative
model result separately after this interpretation.
"""


# ======================================================
# ECOLOGICAL NOTES
# ======================================================

def build_delta_notes(drivers):
    if not drivers:
        feature = "the modified feature"
    else:
        feature = drivers[0][0]

    return f"""
============================================================
ECOLOGICAL INTERPRETATION NOTES
============================================================

The scenario modifies the Digital Twin feature:
{feature}

The feature name and its numerical change define the model input.
They do not, by themselves, establish an equivalent change in
an underlying physical variable, ecological process, habitat,
or ecosystem response.

Use retrieved scientific evidence to explain the ecological
meaning of the feature and any implications that are directly
supported by that evidence.

IMPORTANT:
- Do not treat the feature's numerical direction as proof that
  the corresponding physical variable increased or decreased.
- Do not invent causal mechanisms or ecological responses.
- Distinguish evidence explicitly supported by the retrieved
  material from plausible but unverified interpretations.
- If the retrieved material does not support a specific
  ecological implication, state that the available evidence
  is insufficient rather than filling the gap with general
  assumptions.
- Do not present general scientific knowledge as if it were
  a result measured by the Digital Twin.

The LLM output is only the ecological interpretation.
Do not answer the risk-score part of the user's request.
Do not mention ecosystem risk, a risk score, a risk level,
or any numerical model prediction. Python appends those results.
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


def build_delta_retrieval_query(feature, value_from, value_to):
    """
    Build a Delta-specific query for scientific evidence relating the
    environmental feature to ecosystem condition and ecological risk.

    Preserve the exact Digital Twin feature name and describe only the
    direction of its feature-value change. Do not assume a physical or
    ecological mechanism from that direction.
    """
    concept = get_delta_rag_concept(feature)
    direction = get_change_direction(value_from, value_to)

    if direction is None:
        direction_text = "no change in feature value"
    else:
        direction_text = f"{direction} in feature value"

    return (
        f"Scientific evidence on the relationship between {concept} and "
        "ecosystem condition, ecological vulnerability and ecological risk "
        "in wetland ecosystems; "
        f"Digital Twin feature: {feature}; {direction_text}. "
        "Relevant empirical findings and documented associations; "
        "do not assume causation."
    )


# ======================================================
# PROMPT
# ======================================================

def build_legacy_prompt(facts):
    scenario_text = "\n".join(
        [f"- {fact}" for fact in facts]
    )

    return f"""
    Provide a concise ecological interpretation of the supplied
    Digital Twin feature modification.

    SCENARIO DEFINITION:
    {scenario_text}

    Use the retrieved scientific evidence to interpret the scenario.
    The scenario definition is not, by itself, evidence of an ecological
    effect or of a change in an underlying physical variable.

    RULES:
    - Do not infer physical changes, ecological mechanisms, or ecosystem
      responses solely from the numerical direction of the feature.
    - Use cautious language and distinguish supported evidence from
      possible interpretations.
    - If the retrieved evidence does not support an implication,
      state that the available evidence is insufficient.
    - Do not present associations as proven causal mechanisms.
    - Do not mention risk scores, risk levels, or model predictions.
    - Produce at most two concise sentences.
"""


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
    """
    Render ecological interpretation and model estimates separately.

    A negligible RF delta is treated as zero using the raw delta value.
    Sensitivity evidence is retrieved only for the same feature and
    direction of the environmental modification.
    """
    ecological_text = remove_risk_sentences(text).strip()

    # Check the original delta BEFORE display rounding.
    zero_delta = is_zero_rf_delta(delta)

    if delta is None:
        display_delta = None
    elif zero_delta:
        display_delta = 0.0
    else:
        display_delta = format_risk_delta_for_display(delta)

    sections = []

    if ecological_text:
        sections.append(
            "**Ecological interpretation**\n" + ecological_text
        )

    if display_delta is None:
        return "\n\n".join(sections) if sections else ""

    if zero_delta or display_delta == 0.0:
        direction_label = "No substantial change"
        delta_text = "0.0000"

    elif display_delta > 0:
        direction_label = "Increase"
        delta_text = f"+{display_delta:.4f}"

    else:
        direction_label = "Decrease"
        delta_text = f"{display_delta:.4f}"

    estimate_lines = ["**Model estimate**"]

    required = {"score_from", "score_to", "risk_from", "risk_to"}

    if model_results and required.issubset(model_results):
        estimate_lines.extend([
            (
                f"Initial ecosystem risk: "
                f"{_format_score(model_results['score_from'])} "
                f"({model_results['risk_from']})"
            ),
            (
                f"Final ecosystem risk: "
                f"{_format_score(model_results['score_to'])} "
                f"({model_results['risk_to']})"
            ),
        ])

    estimate_lines.extend([
        f"Predicted risk change: {direction_label}",
        f"Risk-score change: {delta_text}",
    ])

    # --------------------------------------------------
    # RF SENSITIVITY NOTICE
    # --------------------------------------------------

    sensitivity_notice = build_sensitivity_notice(
        drivers=drivers,
        delta=delta,
    )

    if sensitivity_notice:
        estimate_lines.append("")
        estimate_lines.extend(sensitivity_notice)

    sections.append("\n".join(estimate_lines))

    return "\n\n".join(sections)

# ======================================================
# FALLBACK
# ======================================================

def fallback(facts, delta, drivers=None, model_results=None):
    sentence = (
        "The ecological implications of the simulated feature modification "
        "could not be established from the retrieved scientific evidence."
    )

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
    model_results=None,
    scenario_context=None,
    ecological_only=False
):

    print("\n[RAG-DELTA v39] START")

    facts = build_facts(drivers)

    debug_print("[FACTS]:", facts)

    if not facts:
        message = "No valid Digital Twin feature modification was supplied."
        if ecological_only:
            return message
        return add_risk_alignment(
            message,
            delta,
            drivers=drivers,
            model_results=model_results,
        )

    # --------------------------------------------------
    # RETRIEVAL QUERY
    # --------------------------------------------------

    feature, value_from, value_to = drivers[0]
    rag_concept = get_delta_rag_concept(feature)
    rag_query = build_delta_retrieval_query(
        feature,
        value_from,
        value_to,
    )

    debug_print("[DELTA RAG CONCEPT]:", rag_concept)
    debug_print("[DELTA RETRIEVAL QUERY]:", rag_query)

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if USE_LEGACY_PROMPTS:

        prompt = (
            build_legacy_prompt(facts)
            + "\n\nUse the retrieved scientific evidence below:\n"
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
    Interpret the change in the Digital Twin feature {feature} from
    {value_from} to {value_to}. Do not assume that this is an equivalent
    change in the underlying physical variable. Use only directly relevant
    retrieved scientific evidence. Do not answer the
    ecosystem-risk prediction part of the original request; Python will
    append the formatted model result separately.

    {delta_report}

    {delta_notes}

    ============================================================
    RETRIEVED SCIENTIFIC EVIDENCE
    ============================================================
    """
        )

    if scenario_context:
        prompt += f"""

    ADDITIONAL SCENARIO CONTEXT:
    ------------------------------------------------------------
    {scenario_context}

    Treat this context as the operational definition of the simulated
    environmental change. Do not reinterpret it as a different type of
    land-cover modification.
    """

    prompt_question = (
        f"Interpret the change in the Digital Twin feature {feature} "
        f"from {value_from} to {value_to}. Do not assume an equivalent "
        "change in the underlying physical variable. Use only relevant "
        "retrieved scientific evidence. Do not report risk scores, "
        "risk levels, or model predictions."
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
            if ecological_only:
                return ("The ecological implications of the simulated feature modification "
                        "could not be established from the retrieved scientific evidence.")
            return fallback(facts, delta, drivers, model_results)

        cleaned = remove_risk_sentences(clean_output(raw))
        if not is_valid(cleaned):
            cleaned = (
                "The ecological implications of the simulated feature modification "
                "could not be established from the retrieved scientific evidence."
            )

        if ecological_only:
            print("[FINAL ECOLOGICAL ONLY]:", cleaned)
            print("[RAG-DELTA v39] END")
            return cleaned

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

        if ecological_only:
            return ("The ecological implications of the simulated feature modification "
                        "could not be established from the retrieved scientific evidence.")
        return fallback(facts, delta, drivers, model_results)