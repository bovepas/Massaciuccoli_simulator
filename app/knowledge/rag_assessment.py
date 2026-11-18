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

def _format_scenario_modifications(scenario_modifications) -> str:
    """Format the actual feature values applied to the assessment scenario."""

    if not scenario_modifications:
        return "No scenario modifications provided to the RAG component"

    return "\n".join(
        f"• {name}: applied scenario value = {value}"
        for name, value in scenario_modifications.items()
    )

def has_contribution_sign_contradiction(
    text,
    primary_drivers,
    secondary_responses,
) -> bool:
    """Detect explicit positive/negative contribution claims that contradict Python values.

    This deliberately checks only explicit polarity language near a feature name.
    Scenario wording such as "reduced tree cover" is not treated as a contribution
    sign unless the answer also explicitly describes a positive/negative or
    upward/downward model contribution.
    """
    if not text:
        return False

    features = []
    for group in (primary_drivers or {}, secondary_responses or {}):
        for name, value in group.items():
            number = _as_finite_float(value)
            if number is not None and number != 0:
                features.append((str(name), number))

    if not features:
        return False

    # Keep the vocabulary intentionally narrow: these words explicitly describe
    # contribution polarity, unlike "increased/decreased", which may describe
    # the environmental input itself.
    polarity_pattern = re.compile(
        r"\bpositive\b|\bpositively\b|\bupward\b|"
        r"\bnegative\b|\bnegatively\b|\bdownward\b",
        re.IGNORECASE,
    )

    # Sentence boundaries prevent a polarity statement from leaking into the
    # next sentence. The nearest named feature is associated with each polarity
    # cue, avoiding attribution to every feature mentioned in a long sentence.
    sentences = re.split(r"(?<=[.!?;])\s+", clean_text(text))
    for sentence in sentences:
        feature_occurrences = []
        for name, value in features:
            pattern = re.compile(
                rf"(?<!\w){re.escape(name)}(?!\w)",
                re.IGNORECASE,
            )
            for match in pattern.finditer(sentence):
                feature_occurrences.append((match.start(), match.end(), name, value))

        if not feature_occurrences:
            continue

        for cue in polarity_pattern.finditer(sentence):
            cue_word = cue.group(0).lower()
            claimed_sign = (
                1 if cue_word in {"positive", "positively", "upward"}
                else -1
            )

            # Prefer an explicit construction such as "negative contributions,
            # such as vegetation productivity" or "positive contribution from X".
            following = [
                item for item in feature_occurrences if item[0] >= cue.end()
            ]
            linked = None
            if following:
                candidate = min(following, key=lambda item: item[0])
                bridge = sentence[cue.end():candidate[0]]
                if (
                    len(bridge) <= 100
                    and re.search(r"\bcontributions?\b", bridge, re.IGNORECASE)
                    and re.search(
                        r"\b(?:such as|including|like|from|of)\b",
                        bridge,
                        re.IGNORECASE,
                    )
                ):
                    linked = candidate

            if linked is None:
                linked = min(
                    feature_occurrences,
                    key=lambda item: min(
                        abs(cue.start() - item[1]),
                        abs(item[0] - cue.end()),
                    ),
                )

            start, end, name, actual_value = linked
            distance = min(abs(cue.start() - end), abs(start - cue.end()))

            # A polarity word far from the feature is too ambiguous to judge.
            if distance <= 100 and claimed_sign != (1 if actual_value > 0 else -1):
                print(
                    "[RAG] CONTRIBUTION SIGN CONTRADICTION:",
                    name,
                    "actual=", actual_value,
                    "claimed=", cue_word,
                )
                return True

    return False


# ======================================================
# REPORT
# ======================================================

def build_assessment_report(
    question,
    risk_delta,
    primary_drivers,
    secondary_responses,
    scenario_modifications=None,
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
    modifications = _format_scenario_modifications(
        scenario_modifications
    )
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
SCENARIO MODIFICATIONS — ACTUAL MODEL INPUTS
------------------------------------------------------------
{modifications}

IMPORTANT:
These are the feature values actually applied to the scenario
model input. They identify the requested scenario modifications.
They are distinct from Delta-SHAP contributions.

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

def build_ecological_notes(
    scenario_modifications,
    primary_drivers,
    secondary_responses
):
    notes = [
        "SCENARIO MODIFICATIONS:",
        "The scenario modifications section lists the feature values "
        "actually applied to the model input.",
        "These modifications must not be confused with model "
        "contributions.",
        "",
        "PRIMARY DELTA-SHAP CONTRIBUTIONS:",
        "These are model attribution changes associated with features "
        "identified as modified in the scenario.",
        "They are not necessarily the largest contributors to the "
        "overall risk-score difference.",
        "",
        "SECONDARY DELTA-SHAP CONTRIBUTIONS:",
        "These are attribution changes for other model features.",
        "Their presence does not mean that the corresponding "
        "environmental variables were directly modified or "
        "that they physically changed during the simulation.",
        "",
        "DELTA-SHAP INTERPRETATION:",
        "Delta-SHAP for a feature is calculated as its SHAP value "
        "in the scenario minus its SHAP value in the baseline.",
        "A positive Delta-SHAP contributes positively to the "
        "scenario-minus-baseline risk difference. A negative "
        "Delta-SHAP contributes negatively.",
        "The sign describes the change in model attribution, "
        "not whether the environmental variable itself increased "
        "or decreased.",
        "Delta-SHAP values describe model attribution changes; "
        "they do not establish ecological causation.",
        "",
        "The overall risk-score difference reflects the combined "
        "contributions. Positive and negative contributions can "
        "offset one another.",
        "Do not present these contributions as ecological causes "
        "unless independent supporting evidence establishes the "
        "relevant mechanism.",
        "",
        "ECOLOGICAL INTERPRETATION:",
        "Start from the actual scenario modifications to identify "
        "the environmental changes being assessed.",
        "Use retrieved scientific evidence to explain the ecological "
        "role and relevance of these modified variables in the "
        "Massaciuccoli Lake ecosystem.",
        "Use primary and secondary Delta-SHAP contributions to "
        "describe how the model associates these features with "
        "the predicted risk-score difference.",
        "Distinguish scientific evidence describing the ecological "
        "relevance of a variable from evidence supporting a specific "
        "relationship or mechanism in the reported assessment.",
        "Retrieved evidence may provide ecological context without "
        "explaining the specific modelled risk response.",
        "If the retrieved evidence does not establish why the "
        "predicted risk changed, explicitly acknowledge this "
        "limitation rather than inferring an ecological mechanism.",
    ]

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
    scenario_modifications=None,
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
SCENARIO MODIFICATIONS — ACTUAL MODEL INPUTS:
{_format_scenario_modifications(scenario_modifications)}
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
- Distinguish actual scenario modifications from primary and secondary
  model contributions.
- Only features listed under SCENARIO MODIFICATIONS were explicitly
  modified in the model input.
- Primary Delta-SHAP contributions are model attribution results,
  not a list of all scenario modifications.
- Secondary associations must never be described as physical changes
  to environmental variables.
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
9. Treat SCENARIO MODIFICATIONS as the authoritative list of environmental
   features and values actually applied to the model input.
10. Never infer that a feature was modified merely because it appears among
    primary or secondary model contributions.
11. Primary and secondary contributions describe changes in model attribution,
    not additional scenario inputs.
12. Never describe secondary features as physically changed unless they are
    explicitly listed in SCENARIO MODIFICATIONS.
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
    scenario_modifications: dict = None,
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
    print("[RAG] SCENARIO MODIFICATIONS:", scenario_modifications)

    if USE_LEGACY_PROMPTS:
        prompt = build_legacy_prompt(
        question,
        risk_delta,
        primary_text,
        secondary_text,
        context,
        scenario_modifications=scenario_modifications,
        baseline_risk=baseline_risk,
        scenario_risk=scenario_risk,
    )
    else:
        report = build_assessment_report(
        question=question,
        risk_delta=risk_delta,
        primary_drivers=primary_drivers,
        secondary_responses=secondary_responses,
        scenario_modifications=scenario_modifications,
        baseline_risk=baseline_risk,
        scenario_risk=scenario_risk,
    )

        ecological_notes = build_ecological_notes(
        scenario_modifications,
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

When describing model contributions, upward or downward refers
only to the direction of the component's statistical contribution
to the predicted risk-score difference, not to the direction of
the environmental variable's change or to an ecological effect.

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

                sign_contradiction = has_contribution_sign_contradiction(
                    ecological_explanation,
                    primary_drivers,
                    secondary_responses,
                )

                if (
                    unsupported_causality.search(ecological_explanation)
                    or sign_contradiction
                ):
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

                    # Include both modified-input contributions and secondary responses.
                    # Keep the two groups distinct to avoid mixing their meanings.
                    primary_negative_items = sorted(
                        [(name, value) for name, value in primary_items if value < 0],
                        key=lambda item: item[1],
                    )[:2]
                    primary_positive_items = sorted(
                        [(name, value) for name, value in primary_items if value > 0],
                        key=lambda item: item[1],
                        reverse=True,
                    )[:3]
                    secondary_negative_items = sorted(
                        [(name, value) for name, value in secondary_items if value < 0],
                        key=lambda item: item[1],
                    )[:2]
                    secondary_positive_items = sorted(
                        [(name, value) for name, value in secondary_items if value > 0],
                        key=lambda item: item[1],
                        reverse=True,
                    )[:3]

                    def _format_contributions(items):
                        return ", ".join(
                            f"{name} ({value:+.5f})" for name, value in items
                        ) or "none reported"

                    primary_negative_text = _format_contributions(primary_negative_items)
                    primary_positive_text = _format_contributions(primary_positive_items)
                    secondary_negative_text = _format_contributions(secondary_negative_items)
                    secondary_positive_text = _format_contributions(secondary_positive_items)

                    ecological_explanation = (
                        f"Among the modified inputs, downward contributions include "
                        f"{primary_negative_text}, while upward contributions include "
                        f"{primary_positive_text}. Among the secondary model responses, "
                        f"downward contributions include {secondary_negative_text}, "
                        f"while upward contributions include {secondary_positive_text}. "
                        f"These are contributions to the model's prediction, not proof "
                        f"that environmental variables physically changed or caused "
                        f"the result; the retrieved knowledge base does not establish "
                        f"the specific ecological mechanism behind this scenario."
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