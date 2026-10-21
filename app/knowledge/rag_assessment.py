# -*- coding: utf-8 -*-

"""RAG Assessment — v3.1, with explicit and unambiguous risk values.

The LLM explains already-computed assessment results. It must not calculate
risk or confuse an absolute risk score with the difference from baseline.
"""

import math
import re

from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm
from utils.prompt_builder import build_prompt, USE_LEGACY_PROMPTS


# ======================================================
# CONFIG
# ======================================================

MAX_CONTEXT_CHARS = 1500
DEBUG = True
DEBUG_DISABLE_RAG = False


# ======================================================
# UTILS
# ======================================================

def clean_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def build_context(retrieved) -> str:
    if not retrieved:
        return ""

    chunks = [item["text"] for item in retrieved if item.get("text")]
    context = "\n\n".join(chunks)
    return context[:MAX_CONTEXT_CHARS]


def is_valid_output(text: str) -> bool:
    return bool(text and len(text.strip()) >= 30)


def fallback() -> str:
    return (
        "The Digital Twin's assessment results are available, but a reliable "
        "ecological explanation could not be generated. Please refer to the "
        "reported baseline risk, scenario risk, and risk-score difference."
    )


def _as_finite_float(value):
    """Return a finite float, or None when the supplied value is unavailable."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _format_score(value) -> str:
    """Format an absolute risk score to three decimals without hiding tiny values."""
    number = _as_finite_float(value)
    if number is None:
        return "Not provided to the RAG component"

    rounded = round(number, 3)
    if number != 0 and rounded == 0:
        sign = "−" if number < 0 else ""
        return f"{sign}<0.001"
    return f"{rounded:.3f}"


def _format_delta(value) -> str:
    """Format scenario-minus-baseline with its sign and three decimal places."""
    number = _as_finite_float(value)
    if number is None:
        return "Not provided to the RAG component"

    rounded = round(number, 3)
    if number != 0 and rounded == 0:
        sign = "+" if number > 0 else "−"
        return f"{sign}<0.001"
    if rounded == 0:
        return "0.000"
    sign = "+" if rounded > 0 else "−"
    return f"{sign}{abs(rounded):.3f}"


def _risk_direction(risk_delta) -> str:
    number = _as_finite_float(risk_delta)
    if number is None:
        return "Cannot be determined from the values provided"
    if number > 0:
        return "The scenario risk score is higher than the baseline risk score"
    if number < 0:
        return "The scenario risk score is lower than the baseline risk score"
    return "The scenario risk score equals the baseline risk score"


# ======================================================
# REPORT
# ======================================================

def build_assessment_report(
    question,
    risk_delta,
    primary_drivers,
    secondary_responses,
    baseline_risk=None,
    scenario_risk=None,
):
    """Build the RAG report while keeping absolute scores and their delta distinct.

    The first four parameters preserve compatibility with older callers.
    The absolute risk values are optional until task_assessment passes them.
    """
    baseline_text = _format_score(baseline_risk)
    scenario_text = _format_score(scenario_risk)
    delta_text = _format_delta(risk_delta)
    direction_text = _risk_direction(risk_delta)

    primary = "None"
    if primary_drivers:
        primary = "\n".join(
            f"• {name} (association score: {abs(value):.2f})"
            for name, value in primary_drivers.items()
        )

    secondary = "None"
    if secondary_responses:
        secondary = "\n".join(
            f"• {name} (association score: {abs(value):.2f})"
            for name, value in secondary_responses.items()
        )

    report = f"""
============================================================
DIGITAL TWIN ASSESSMENT REPORT
============================================================

ORIGINAL USER QUESTION / REQUESTED SCENARIO
------------------------------------------------------------
{question}

============================================================
PREDICTED RISK RESULTS — AUTHORITATIVE NUMERICAL OUTPUTS
------------------------------------------------------------

Baseline risk score: {baseline_text}
Scenario risk score: {scenario_text}
Risk-score difference (scenario minus baseline): {delta_text}
Risk-score direction relative to baseline: {direction_text}

IMPORTANT DISTINCTION:
- The baseline risk score is the predicted risk for the reference state.
- The scenario risk score is the predicted risk for the modified scenario.
- The risk-score difference is scenario risk score minus baseline risk score.
- A risk-score difference is NOT an absolute risk score.
- If an absolute score says it was not provided, do not infer it from the difference.

============================================================
PRIMARY MODEL DRIVERS
------------------------------------------------------------
{primary}

============================================================
SECONDARY ECOSYSTEM ASSOCIATIONS
------------------------------------------------------------
{secondary}
"""
    return report


# ======================================================
# ECOLOGICAL NOTES
# ======================================================

def build_ecological_notes(primary_drivers, secondary_responses):
    notes = [
        "Primary model drivers identify variables most strongly associated "
        "with the predicted ecosystem response.",
        "Secondary ecosystem associations describe components statistically "
        "associated with the simulated scenario. An association does not, by "
        "itself, mean that a component increased or decreased during the simulation.",
    ]

    if primary_drivers:
        notes.extend(["", "Primary drivers reported by the Digital Twin:"])
        for feature in primary_drivers:
            notes.append(
                f"• {feature} is identified as a primary model driver associated "
                "with the predicted ecosystem response."
            )

    if secondary_responses:
        notes.extend(["", "Secondary ecosystem associations:"])
        for feature in secondary_responses:
            notes.append(
                f"• {feature} is identified as a secondary ecosystem association. "
                "This does not establish that the variable itself changed."
            )

    return (
        "============================================================\n"
        "ECOLOGICAL INTERPRETATION NOTES\n"
        "============================================================\n\n"
        + "\n".join(notes)
        + "\n"
    )


# ======================================================
# PROMPT
# ======================================================

def build_legacy_prompt(
    question,
    risk_text,
    primary_text,
    secondary_text,
    context,
    baseline_risk=None,
    scenario_risk=None,
):
    """Compatibility prompt for legacy prompt mode."""
    return f"""
You are an environmental scientist assisting the Massaciuccoli Digital Twin.

ORIGINAL QUESTION AND REQUESTED SCENARIO:
{question}

AUTHORITATIVE MODEL RESULTS (scores rounded to three decimals):
Baseline risk score: {_format_score(baseline_risk)}
Scenario risk score: {_format_score(scenario_risk)}
Risk-score difference (scenario minus baseline): {_format_delta(risk_text)}

Primary drivers:
{primary_text or 'None'}

Secondary ecosystem associations:
{secondary_text or 'None'}

SCIENTIFIC KNOWLEDGE BASE:
{context}

RULES:
- Explain the provided results; do not calculate or change them.
- Never report the risk-score difference as if it were the scenario's absolute risk.
- Do not infer a missing absolute score from the difference alone.
- Preserve the modification's direction and units exactly as stated in the question.
- Do not claim a temperature decrease if the question specifies an increase, or vice versa.
- Driver associations do not, on their own, establish causal effects or actual increases/decreases in associated ecosystem variables.
- Use cautious language and only ecological interpretations supported by the supplied evidence.
- Be concise and directly answer the question.

Answer:
"""


def _assessment_answering_rules() -> str:
    return """
============================================================
MANDATORY ASSESSMENT ANSWERING RULES
============================================================

1. Python has already computed the numerical results. Do not recalculate,
   alter, or reinterpret their numerical values.
2. Keep the three results distinct: baseline risk score, scenario risk score,
   and risk-score difference (scenario minus baseline).
3. The risk-score difference is NOT the scenario risk score. Never present it
   as the absolute predicted risk.
4. If a baseline or scenario score is marked "Not provided to the RAG component",
   state that this absolute score was not provided; do not invent it or derive it
   from the risk-score difference alone.
5. Preserve the exact direction and units of the modifications in the original
   question. Never turn an increase into a decrease, or the reverse.
6. Driver and secondary-association scores describe model associations. They do
   not automatically mean that the associated environmental variable changed,
   and they do not prove a causal mechanism or confidence level.
7. Do not infer additional ecosystem responses beyond the report and the
   retrieved evidence. A cautious statement is preferable to unsupported detail.
8. Answer the original question directly and concisely. Do not repeat the same
   result in a conclusion.
============================================================
"""


# ======================================================
# MAIN
# ======================================================

def generate_assessment_explanation(
    question: str,
    drivers: list,
    primary_drivers: dict = None,
    secondary_responses: dict = None,
    risk_delta: float = None,
    features: list = None,
    baseline_risk: float = None,
    scenario_risk: float = None,
):
    """Generate a scientific explanation from the assessment's computed outputs.

    The new baseline_risk and scenario_risk parameters are appended to preserve
    compatibility with existing keyword/positional callers. task_assessment.py
    must pass them explicitly for the RAG prompt to receive all three values.
    """
    print("\n[RAG-ASSESSMENT v3.1] START")

    driver_text = ", ".join((drivers or [])[:3])
    query = f"""
    lake ecosystem risk interactions
    {driver_text}
    hydrology biodiversity resilience
    ecological stability nutrient dynamics
    """
    print("[DEBUG] RAG query:", query)

    if DEBUG_DISABLE_RAG:
        print("[RAG] DEBUG: Retrieval context disabled.")
        retrieved = []
        context = ""
    else:
        retrieved, _ = retrieve_documents(query)
        context = build_context(retrieved)
        print("[RAG] Retrieved documents:", len(retrieved))
        print("[RAG] Context length:", len(context))

    primary_text = ""
    if primary_drivers:
        primary_text = "\n".join(
            f"- {name}\n  association score: {abs(value):.2f}"
            for name, value in primary_drivers.items()
        )

    secondary_text = ""
    if secondary_responses:
        secondary_text = "\n".join(
            f"- {name}\n  association score: {abs(value):.2f}"
            for name, value in secondary_responses.items()
        )

    print("\n[RAG] BASELINE RISK:", _format_score(baseline_risk))
    print("[RAG] SCENARIO RISK:", _format_score(scenario_risk))
    print("[RAG] RISK DELTA:", _format_delta(risk_delta))
    print("[RAG] PRIMARY DRIVERS:", primary_drivers)
    print("[RAG] SECONDARY RESPONSES:", secondary_responses)

    if USE_LEGACY_PROMPTS:
        prompt = build_legacy_prompt(
            question,
            risk_delta,
            primary_text,
            secondary_text,
            context,
            baseline_risk=baseline_risk,
            scenario_risk=scenario_risk,
        )
    else:
        report = build_assessment_report(
            question=question,
            risk_delta=risk_delta,
            primary_drivers=primary_drivers,
            secondary_responses=secondary_responses,
            baseline_risk=baseline_risk,
            scenario_risk=scenario_risk,
        )
        ecological_notes = build_ecological_notes(
            primary_drivers,
            secondary_responses,
        )
        prompt = (
            build_prompt("assessment", question=question)
            + report
            + ecological_notes
            + f"""

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

{context}

"""
            + _assessment_answering_rules()
        )

    try:
        if DEBUG:
            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        raw = call_llm(prompt, role="interpretation")
        print("[RAG] RAW:", raw)

        if not is_valid_output(raw):
            return fallback()

        cleaned = clean_text(raw)
        print("[RAG-ASSESSMENT v3.1] END\n")
        return cleaned

    except Exception as exc:
        print("[RAG-ASSESSMENT ERROR]", exc)
        return fallback()
