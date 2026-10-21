# -*- coding: utf-8 -*-
"""RAG Drivers — v10.

The Digital Twin owns driver selection, ranking, direction and strength.
The LLM supplies ecological context only; the authoritative association
statements in the final interpretation are assembled deterministically.
"""

import re

from knowledge.rag_pipeline import generate_answer
from utils.feature_semantics import build_semantic_context
from utils.prompt_builder import load_base_prompt, load_model_prompt, load_style_prompt

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


def build_drivers_notes(semantic_context):
    return f"""
============================================================
ECOLOGICAL INTERPRETATION NOTES
============================================================

The Digital Twin has already selected and ranked the reported
statistical associations. Positive and negative describe the
reported direction; strong and moderate describe the supplied
association-strength categories.

These categories are not, by themselves, statistical significance
tests. Do not claim that an association is or is not statistically
significant unless the input explicitly reports such a test.

Semantic descriptions provide ecological context only. They do not
prove that a variable causes or mechanistically explains the target.

Semantic descriptions of the target and reported variables:

{semantic_context}
"""


# ======================================================
# PROMPT
# ======================================================


def build_legacy_prompt(target, drivers, semantic_context):
    drivers_text = "\n".join(
        f"- {d['feature']} (direction: {d['direction']}, strength: {d['strength']})"
        for d in drivers
    )
    return f"""
You are a scientific assistant for the Massaciuccoli Digital Twin.

TARGET VARIABLE:
{target}

AUTHORITATIVE DRIVERS REPORT:
{drivers_text}

ECOLOGICAL INTERPRETATION NOTES:
{semantic_context}

Your role in this generation is limited to giving ecological context for
the reported variables. The final answer will state the authoritative
association directions separately using the Digital Twin's data.
Do not restate or reinterpret association directions and strengths.
Do not describe a causal relationship between any driver and the target.
Do not mention the target variable in your generated text.

Use only context supported by the supplied semantic notes and retrieved
scientific evidence. Do not introduce observed changes, mechanisms,
recommendations, numerical results, or statistical-significance claims.
If the sources do not provide relevant context, say that the supplied
material does not establish a specific ecological explanation.

Write 1–3 concise sentences of ecological context only.
ECOLOGICAL CONTEXT:
"""


# ======================================================
# OUTPUT VALIDATION
# ======================================================


def is_valid(text):
    if not text or len(str(text).strip()) < 25:
        return False
    if "interpretation not available" in str(text).lower():
        return False
    return True


def _normalise_for_match(text):
    """Normalise prose for stable phrase checks."""
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _claims_unreported_significance(text):
    """Catch unsupported judgements that associations are/aren't significant."""
    normalised = _normalise_for_match(text)
    patterns = (
        r"\bstatistically significant\b",
        r"\bnot significant\b",
        r"\bno other reported associations\b",
        r"\bno other associations\b",
        r"\bonly .* significant\b",
    )
    return any(re.search(pattern, normalised) for pattern in patterns)


# The LLM output is context-only. These checks reject generated prose that
# tries to restate associations, connect a driver to the target, or assert a
# causal mechanism. Association directions are rendered from Python data.
_CONTEXT_RELATION_PATTERNS = (
    r"\bassociated with\b",
    r"\bassociation(s)?\b",
    r"\bcorrelat(?:e|ed|es|ion|ions)\b",
    r"\brelationship(s)?\b",
    r"\blinked to\b",
    r"\brelated to\b",
    r"\bconnect(?:s|ed|ing)? to\b",
    r"\bcause(?:s|d)?\b",
    r"\blead(?:s|ing)? to\b",
    r"\bresult(?:s|ing)? in\b",
    r"\bcontribut(?:e|es|ed|ing) to\b",
    r"\bdrive(?:s|n)?\b",
    r"\binfluenc(?:e|es|ed|ing)\b",
    r"\baffect(?:s|ed|ing)?\b",
    r"\bimpact(?:s|ed|ing)?\b",
    r"\breflect(?:s|ed|ing)?\b",
    r"\bdue to\b",
    r"\bbecause\b",
    r"\btherefore\b",
    r"\bconsequently\b",
    r"\bresponsible for\b",
    r"\bexplains?\b",
    r"\bdetermines?\b",
    r"\bmodif(?:y|ies|ied|ying)\b",
    r"\balter(?:s|ed|ing)?\b",
    r"\bexacerbat(?:e|es|ed|ing)\b",
    r"\b(?:increas(?:e|es|ed|ing)|decreas(?:e|es|ed|ing)|reduc(?:e|es|ed|ing)|lower(?:s|ed|ing)?|rais(?:e|es|ed|ing)|higher|lower|greater|less|more|positive|negative)\b",
    r"\bplay(?:s|ed|ing)? a role\b",
)


def is_safe_context(text):
    """Return True only for context prose, not a new association analysis."""
    if not is_valid(text):
        return False
    normalised = _normalise_for_match(text)
    if _claims_unreported_significance(text):
        return False
    # The contextual paragraph must not contain figures, coefficients or years.
    if re.search(r"\d", str(text)):
        return False
    if any(re.search(pattern, normalised) for pattern in _CONTEXT_RELATION_PATTERNS):
        return False
    return True


# ======================================================
# DETERMINISTIC ASSOCIATION SUMMARY AND FALLBACK
# ======================================================


def _selected_associations_for_interpretation(drivers):
    """Return strong associations; if none are strong, use the first three."""
    strong = [
        d for d in drivers
        if str(d.get("strength", "")).strip().lower() == "strong"
    ]
    return strong if strong else list(drivers[:3])


def build_authoritative_association_summary(target, drivers):
    """Render directions/strength from Digital Twin data, never from the LLM."""
    selected = _selected_associations_for_interpretation(drivers)
    if not selected:
        return (
            f"The Digital Twin did not report environmental associations for {target}."
        )

    clauses = []
    for driver in selected:
        feature = str(driver.get("feature", "Unnamed variable"))
        direction = str(driver.get("direction", "unspecified")).strip().lower()
        strength = str(driver.get("strength", "reported")).strip().lower()

        if direction in ("positive", "negative"):
            description = f"a {strength} {direction} statistical association"
        else:
            description = f"a {strength} statistical association"

        clauses.append(f"{description} between {feature} and {target}")

    # One sentence keeps the interpretation compact while preserving the
    # report order and the direction of every included association.
    if len(clauses) == 1:
        return f"The Digital Twin reports {clauses[0]}."
    joined = "; ".join(clauses[:-1]) + "; and " + clauses[-1]
    return "The Digital Twin reports " + joined + "."


def build_context_fallback():
    """A conservative context statement used when the LLM crosses its scope."""
    return (
        "The supplied semantic notes provide ecological context for the reported "
        "variables, but do not by themselves establish a specific mechanism "
        "connecting these variables to the target. The retrieved material does "
        "not support a stronger mechanistic explanation; the reported directions "
        "should therefore be interpreted as statistical associations, not causal effects."
    )


def fallback_explanation(target, drivers):
    """Safe complete interpretation without relying on unvalidated LLM prose."""
    if not drivers:
        return (
            f"The Digital Twin did not report environmental associations for {target}. "
            "The supplied material does not establish a specific ecological explanation."
        )
    summary = build_authoritative_association_summary(target, drivers)
    return f"{summary} {build_context_fallback()}".strip()


# ======================================================
# CLEAN OUTPUT
# ======================================================


def clean_output(text):
    return re.sub(r"\s+", " ", str(text).strip())


# ======================================================
# DRIVERS REPORT
# ======================================================


def build_drivers_report(target, drivers):
    associations = "\n".join(
        f"{i}. {d['feature']}\n"
        f"   Direction: {d['direction']}\n"
        f"   Strength: {d['strength']}"
        for i, d in enumerate(drivers, start=1)
    )
    return f"""
============================================================
DIGITAL TWIN DRIVERS REPORT — AUTHORITATIVE
============================================================

TARGET VARIABLE:
{target}

PRIMARY ASSOCIATED VARIABLES (already ranked by the Digital Twin):
{associations}

Do not change this ranking, direction, or strength classification.
"""


# ======================================================
# MAIN
# ======================================================


def generate_drivers_explanation(target, drivers, features=None):
    print("\n[RAG-DRIVERS v10] START")

    try:
        semantic_context = ""
        if features:
            semantic_context = build_semantic_context(features)
            print("\n[RAG] SEMANTIC CONTEXT")
            print(semantic_context)

        drivers_report = build_drivers_report(target, drivers)
        drivers_notes = build_drivers_notes(semantic_context)

        # Compose only the general scientific prompt components. The task-specific
        # drivers prompt asks for association interpretation, which would conflict
        # with this deliberately narrower context-generation step.
        base_prompt = "\n\n".join(
            component for component in (
                load_base_prompt(),
                load_model_prompt(),
                load_style_prompt(),
            ) if component
        )

        # The authoritative associations are assembled separately below.
        prompt = (
            base_prompt
            + f"\n\n{drivers_report}\n{drivers_notes}\n"
            + """
NARROW SUBTASK FOR THIS GENERATION — OVERRIDES ANY BROADER WORDING ABOVE:

Generate ecological context only. The final interpretation will state the
Digital Twin's authoritative association directions separately in code.
Do not state, restate, rank, paraphrase or infer any relationship between a
reported variable and the target. Do not mention the target variable.
Do not use association language, directional relationship claims, or causal
verbs (for example: associated, correlated, linked, causes, leads to, affects,
influences, contributes to, reflects, determines). Do not claim observed changes.

Describe only ecological meanings or background explicitly supported by the
retrieved scientific evidence and the supplied semantic notes. General facts
about wetlands are not evidence for a mechanism connecting a particular driver
to the target. If there is no relevant supported context, say so cautiously.
Do not include numbers, coefficients, years, percentages, significance claims,
recommendations or additional environmental variables.

Return 1–3 concise sentences of ecological context only. Do not add headings.

ECOLOGICAL CONTEXT:
"""
        )

        if DEBUG:
            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        print("    llm_prompt_length:", len(prompt))

        top_drivers = "; ".join(
            str(d.get("feature", "")) for d in drivers
        )
        rag_query = (
            "Massaciuccoli Lake basin scientific evidence on the ecological "
            "context of the target variable and the following environmental "
            f"variables: target={target}; drivers={top_drivers}. "
            "Relevant context may include wetland ecology, water availability, "
            "climate conditions, biodiversity, and land-use characteristics. "
            "Do not assume a causal relationship."
        )

        print("\n[RAG] Query:")
        print(rag_query)

        raw = generate_answer(
            question=rag_query,
            features=features,
            extra_prompt=prompt,
        )

        debug_print("\n[RAG-DRIVERS] Raw contextual output:")
        debug_print(raw)

        context = clean_output(raw) if is_valid(raw) else ""
        if not context or not is_safe_context(context):
            debug_print(
                "[RAG-DRIVERS] Context output crossed scope or failed validation; "
                "using conservative context fallback."
            )
            context = build_context_fallback()

        association_summary = build_authoritative_association_summary(target, drivers)
        final_text = f"{association_summary} {context}".strip()

        debug_print("\n[RAG-DRIVERS] Authoritative association summary:")
        debug_print(association_summary)
        debug_print("\n[RAG-DRIVERS] Final output:")
        debug_print(final_text)
        return final_text

    except Exception as e:
        print("\n🔥 RAG-DRIVERS ERROR:")
        print(e)
        return fallback_explanation(target, drivers)

    finally:
        print("[RAG-DRIVERS] END\n")
