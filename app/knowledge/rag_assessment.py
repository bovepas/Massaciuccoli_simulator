# -*- coding: utf-8 -*-

"""RAG Assessment — v3.1, with explicit and unambiguous risk values.

The LLM explains already-computed assessment results. It must not calculate
risk or confuse an absolute risk score with the difference from baseline.
"""

import math
import re
from decimal import Decimal, ROUND_HALF_UP

from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm
from utils.prompt_builder import build_prompt, USE_LEGACY_PROMPTS


# ======================================================
# CONFIG
# ======================================================

MAX_CONTEXT_CHARS = 6000
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


def _round_to_three_decimals(number: float) -> Decimal:
    """Round decimal display values conventionally (ties away from zero)."""
    return Decimal(str(number)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _format_score(value) -> str:
    """Format an absolute risk score to three decimals without hiding tiny values."""
    number = _as_finite_float(value)
    if number is None:
        return "Not provided to the RAG component"

    rounded = _round_to_three_decimals(number)
    if number != 0 and rounded == Decimal("0.000"):
        sign = "−" if number < 0 else ""
        return f"{sign}<0.001"
    if rounded == Decimal("0.000"):
        return "0.000"
    return f"{rounded:.3f}"


def _format_delta(value) -> str:
    """Format scenario-minus-baseline with its sign and three decimal places.

    Decimal ROUND_HALF_UP avoids Python round()'s ties-to-even behaviour and
    makes halfway cases such as -0.1605 display consistently as −0.161.
    """
    number = _as_finite_float(value)
    if number is None:
        return "Not provided to the RAG component"

    rounded = _round_to_three_decimals(number)
    if number != 0 and rounded == Decimal("0.000"):
        sign = "+" if number > 0 else "−"
        return f"{sign}<0.001"
    if rounded == Decimal("0.000"):
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
            f"• {name} (Delta-SHAP contribution: {value:+.5f})"
            for name, value in primary_drivers.items()
        )

    secondary = "None"
    if secondary_responses:
        secondary = "\n".join(
            f"• {name} (Delta-SHAP contribution: {value:+.5f})"
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
PRIMARY DELTA-SHAP CONTRIBUTIONS
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
        "DELTA-SHAP INTERPRETATION:",
        "Delta-SHAP for a feature is calculated as its SHAP value "
        "in the scenario minus its SHAP value in the baseline.",
        "A positive Delta-SHAP contributes positively to the "
        "scenario-minus-baseline risk difference. A negative "
        "Delta-SHAP contributes negatively.",
        "The sign describes the change in the model attribution, "
        "not whether the environmental variable itself increased "
        "or decreased.",
        "Delta-SHAP values describe model attribution changes; "
        "they do not establish ecological causation.",
    ]

    if primary_drivers:
        notes.extend([
            "",
            "DIRECTLY MODIFIED FEATURES:",
            "This list identifies features explicitly modified "
            "in the requested scenario. Their contributions are "
            "shown separately and are not necessarily the largest "
            "contributors to the overall risk-score difference.",
        ])

    if secondary_responses:
        notes.extend([
            "",
            "OTHER FEATURE CONTRIBUTIONS:",
            "These are attribution changes for other model features. "
            "Their presence does not mean that the corresponding "
            "environmental variables were directly modified or "
            "that they physically changed during the simulation.",
        ])

    notes.extend([
        "",
        "The overall risk-score difference reflects the combined "
        "contributions. Positive and negative contributions can "
        "offset one another, so the total can decrease even when "
        "some individual contributions are positive.",
        "Do not present these contributions as ecological causes "
        "unless independent supporting evidence establishes the "
        "relevant mechanism.",
    ])

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
    """Generate ecological interpretation and render risk values deterministically."""

    print("\n[RAG-ASSESSMENT v3.2] START")

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
    print("[RAG] RISK DELTA (raw):", repr(risk_delta))
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

    # These final instructions override conflicting instructions earlier
    # in the prompt.
    prompt += """

STRICT FINAL OUTPUT CONTRACT

Return ONLY the ecological interpretation, in no more than two
concise sentences.

Do not report or repeat the baseline risk, scenario risk, or
risk-score difference. Python will append these values separately.

A risk-score difference is not an absolute risk score.

Model-driver and secondary-association scores describe statistical
associations; they do not prove causation.

Do not claim that a driver caused, explains, or is responsible for
the direction of the overall risk change.

If the available evidence does not explain the direction of the
specific result, explicitly acknowledge this limitation.

Do not use the terms SHAP, Delta-SHAP, feature attribution,
or association score in the user-facing answer.

Describe model contributions in ordinary language, explaining
which components push the predicted score upward or downward.

Do not imply that an environmental variable physically changed
unless the scenario inputs explicitly specify that change.

Distinguish the model's numerical explanation from a demonstrated
ecological mechanism.
"""

    try:
        if DEBUG:
            print("\n========== FINAL PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        raw = call_llm(prompt)
        print("[RAG] RAW:", raw)

        if not is_valid_output(raw):
            ecological_explanation = fallback()

        else:
            # 1. Remove sentences that repeat the numerical results.
            sentences = re.split(
                r"(?<=[.!?])\s+",
                clean_text(raw),
            )

            numeric_result_sentence = re.compile(
                r"\b(?:baseline risk score|scenario risk score|"
                r"risk[- ]score difference|risk score difference|"
                r"predicted risk score|ecosystem risk score)\b.*\d",
                re.IGNORECASE,
            )

            sentences = [
                sentence.strip()
                for sentence in sentences
                if sentence.strip()
                and not numeric_result_sentence.search(sentence)
            ]

            ecological_explanation = " ".join(sentences[:2]).strip()

            if not is_valid_output(ecological_explanation):
                ecological_explanation = fallback()

            else:
                # 2. Detect unsupported causal attribution even when
                #    the LLM ignores the instructions in the prompt.
                unsupported_causality = re.compile(
                    r"\battribut(?:e|es|ed|ing)\s+"
                    r"(?:(?:primarily|mainly)\s+)?to\b|"
                    r"\b(?:caused|explained|accounted for|driven)\s+by\b|"
                    r"\b(?:due to|because of|results? from|"
                    r"stems? from|arises? from)\b|"
                    r"\b(?:driver|temperature change|precipitation change)\s+"
                    r"(?:caused|explains?|accounts for)\b",
                    re.IGNORECASE,
                )

                if unsupported_causality.search(ecological_explanation):
                    primary_items = [
                        (name, _as_finite_float(value))
                        for name, value in (primary_drivers or {}).items()
                    ]
                    primary_items = [
                        (name, value)
                        for name, value in primary_items
                        if value is not None
                    ]

                    secondary_items = [
                        (name, _as_finite_float(value))
                        for name, value in (secondary_responses or {}).items()
                    ]
                    secondary_items = [
                        (name, value)
                        for name, value in secondary_items
                        if value is not None
                    ]

                    primary_text = "; ".join(
                        f"{name} ({value:+.5f})"
                        for name, value in primary_items
                    ) or "not available"

                    negative_items = sorted(
                        [
                            (name, value)
                            for name, value in secondary_items
                            if value < 0
                        ],
                        key=lambda item: item[1],
                    )[:2]

                    positive_items = sorted(
                        [
                            (name, value)
                            for name, value in secondary_items
                            if value > 0
                        ],
                        key=lambda item: item[1],
                        reverse=True,
                    )[:3]

                    negative_text = ", ".join(
                        f"{name} ({value:+.5f})"
                        for name, value in negative_items
                    ) or "none among the reported components"

                    positive_text = ", ".join(
                        f"{name} ({value:+.5f})"
                        for name, value in positive_items
                    ) or "none among the reported components"

                    ecological_explanation = (
                        f"The requested inputs have the following model "
                        f"contributions: {primary_text}. Among the other "
                        f"components, the largest downward contributions are "
                        f"{negative_text}, while the upward contributions "
                        f"include {positive_text}. These contributions describe "
                        f"the model's prediction, not proof that the corresponding "
                        f"environmental variables physically changed or caused "
                        f"the result. The retrieved knowledge base does not "
                        f"establish the specific ecological mechanism behind "
                        f"this scenario."
                    )

    except Exception as exc:
        print("[RAG-ASSESSMENT ERROR]", exc)
        ecological_explanation = fallback()

    # 3. Python produces a natural-language numerical summary.
    baseline_number = _as_finite_float(baseline_risk)
    scenario_number = _as_finite_float(scenario_risk)
    delta_number = _as_finite_float(risk_delta)

    if (
        baseline_number is not None
        and scenario_number is not None
        and delta_number is not None
    ):
        if delta_number < 0:
            relative_change = (
                abs(delta_number) / abs(baseline_number) * 100
                if baseline_number != 0
                else None
            )

            relative_text = (
                f", approximately {relative_change:.0f}% of the baseline score"
                if relative_change is not None
                else ""
            )

            quantitative_summary = (
                f"The model's predicted ecosystem-risk score falls from "
                f"{_format_score(baseline_risk)} in the baseline scenario to "
                f"{_format_score(scenario_risk)} in the requested scenario: "
                f"a decrease of {_format_score(abs(delta_number))}"
                f"{relative_text}."
            )

        elif delta_number > 0:
            relative_change = (
                abs(delta_number) / abs(baseline_number) * 100
                if baseline_number != 0
                else None
            )

            relative_text = (
                f", approximately {relative_change:.0f}% of the baseline score"
                if relative_change is not None
                else ""
            )

            quantitative_summary = (
                f"The model's predicted ecosystem-risk score rises from "
                f"{_format_score(baseline_risk)} in the baseline scenario to "
                f"{_format_score(scenario_risk)} in the requested scenario: "
                f"an increase of {_format_score(abs(delta_number))}"
                f"{relative_text}."
            )

        else:
            quantitative_summary = (
                f"The model's predicted ecosystem-risk score remains unchanged "
                f"at {_format_score(baseline_risk)}."
            )

    else:
        quantitative_summary = (
            "The model did not provide all the numerical values needed "
            "to describe the change in predicted ecosystem risk."
        )

    final_answer = (
        quantitative_summary
        + "\n\n"
        + clean_text(ecological_explanation)
    )

    print("[RAG-ASSESSMENT v3.2] FINAL RESPONSE:", final_answer)
    print("[RAG-ASSESSMENT v3.2] END\n")

    return final_answer