# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG — IMPORTANCE COMPARE

Interpreta il confronto tra due driver
interpretando gli effetti direzionali calcolati da
task_importance_compare.
"""

import re

from knowledge.rag_pipeline import (
    generate_answer
)

from config.llm_profiles import (
    LLM_PROFILE,
    LLM_STYLE
)

from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)
DEBUG = True

# ======================================================
# CLEAN OUTPUT
# ======================================================

def clean_output(text: str):

    if not text:
        return None

    text = text.strip()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text


# ======================================================
# FEATURE TO TEXT
# ======================================================

def feature_to_text(feature):

    if isinstance(
        feature,
        list
    ):

        return "\n".join(
            feature
        )

    return str(feature)

# ======================================================
# LEGACY PROMPT
# ======================================================

def build_legacy_prompt(
    question,
    comparison_statement
):

    return f"""
You are a scientific assistant for the Massaciuccoli Digital Twin.

QUESTION
{question}

COMPUTED DIRECTIONAL SENSITIVITY RESULTS
{comparison_statement}

TASK
Compare the changes in predicted ecosystem risk caused by the two
numerical perturbations, each evaluated against the same baseline.

This is a comparison of model sensitivity to the specific perturbations
tested. It is NOT a classical feature-importance ranking, a measure of
intrinsic ecological importance, or an evaluation of management
intervention effectiveness.

The task applies a perturbation of 0.5 standard deviations to each
numerical feature: upward for increase/unspecified and downward for
decrease. When direction is unspecified, the upward perturbation is a
computational convention, not a direction requested by the user.

A positive impact means predicted ecosystem risk increased relative to
the common baseline; a negative impact means it decreased. A zero or
near-zero value means little or no change was detected by this model for
the tested perturbation at the reported precision. It does not prove
that the variable has no ecological influence.

Do not equate broad ecological concepts with their numerical proxies.
Do not describe a feature perturbation as restoration, conservation,
stress reduction, or another real-world intervention unless that action
is explicitly represented in the scenario. The model predicts risk; it
does not directly measure ecosystem resilience.

Accept the reported values and signs exactly as provided. Do not
recalculate them or infer direct ecological causality. Use retrieved
evidence only as supported ecological context, not as an unsupported
explanation of the numerical result.

Answer the user's question directly and concisely. If the requested
comparison cannot be answered by the reported model outputs, state
that limitation explicitly.

Answer:
"""


# ======================================================
# FALLBACK
# ======================================================

def fallback_compare_explanation(
    entity_a,
    entity_b,
    direction_a,
    direction_b,
    impact_a,
    impact_b
):
    def scenario_text(entity, direction, impact):
        if direction == "unspecified":
            direction_text = (
                "with no direction specified by the user "
                "(positive-perturbation convention applied by the task)"
            )
        else:
            direction_text = f"with the requested {direction}"

        return (
            f"For {entity} {direction_text}, "
            f"the predicted risk change is {impact:+.6f}"
        )

    return (
        scenario_text(entity_a, direction_a, impact_a)
        + "; "
        + scenario_text(entity_b, direction_b, impact_b)
        + ". Positive values indicate an increase in predicted ecosystem "
        "risk; negative values indicate a decrease. These are model "
        "responses under the tested scenarios, not evidence of direct "
        "causality or intrinsic variable importance."
    )



# ======================================================
# IMPORTANCE COMPARISON REPORT
# ======================================================

def build_importance_compare_report(
    question,
    entity_a,
    entity_b,
    direction_a,
    direction_b,
    impact_a,
    impact_b,
    perturbations_a,
    perturbations_b,
    comparison_statement
):

    return f"""
============================================================
DIGITAL TWIN DIRECTIONAL SENSITIVITY COMPARISON REPORT
============================================================

QUESTION
------------------------------------------------------------

{question}

IMPORTANT DISTINCTION
------------------------------------------------------------

The concepts in the question are the user's ecological framing.
The feature names and perturbation values below identify what the
computational task actually changed. The two are not necessarily
equivalent.

SCENARIOS EVALUATED
------------------------------------------------------------

Scenario A
Question concept/entity: {entity_a}
Direction extracted from the question: {direction_a}
Actual numerical feature perturbations (feature, baseline, delta,
scenario value): {perturbations_a}
Change in predicted ecosystem risk: {impact_a:+.6f}

Scenario B
Question concept/entity: {entity_b}
Direction extracted from the question: {direction_b}
Actual numerical feature perturbations (feature, baseline, delta,
scenario value): {perturbations_b}
Change in predicted ecosystem risk: {impact_b:+.6f}

COMPUTATIONAL METHOD
------------------------------------------------------------

Each scenario is evaluated independently against the same baseline.
The task perturbs each numerical feature by 0.5 standard deviations:
increase/unspecified applies +0.5 standard deviations; decrease applies
-0.5 standard deviations. Unspecified direction therefore means the
task's positive-perturbation convention, not a direction requested by
the user.

The reported risk impacts are rounded upstream to four decimal places.
A zero or near-zero value must be interpreted at that precision.

============================================================
COMPUTED COMPARISON
------------------------------------------------------------

{comparison_statement}
"""


def build_importance_compare_notes():

    return """
============================================================
TASK-SPECIFIC SCIENTIFIC INTERPRETATION RULES
============================================================

TASK MEANING: DIRECTIONAL SENSITIVITY COMPARISON
------------------------------------------------------------

This task compares how the model's predicted ecosystem-risk score
responds to two separate numerical perturbations, each evaluated
against the SAME baseline prediction.

It is a comparison of model sensitivity to the specific perturbations
tested. It is NOT:
- a classical feature-importance ranking;
- a ranking of intrinsic ecological importance;
- proof that one variable causes more ecological damage;
- an evaluation of the effectiveness of real-world interventions.

1. QUESTION CONCEPTS AND ACTUAL NUMERICAL FEATURES
------------------------------------------------------------

The ecological concepts in the user's question and the numerical
features used by the Digital Twin are not necessarily equivalent.

Always distinguish:
- the original ecological concept mentioned by the user;
- the numerical feature(s) actually perturbed, as listed in the
  perturbation dictionaries in the report.

The feature names and their baseline, delta and scenario values are
the authoritative description of what the task actually changed.

Do not claim that a feature fully represents a broader ecological
concept unless this correspondence is supported by the available
information. If it is an indirect representation or proxy, say so.
Do not describe the numerical simulation as a complete simulation
of the broader ecological process.

2. DIRECTION AND PERTURBATION MAGNITUDE
------------------------------------------------------------

For each numerical feature, the task applies a perturbation of
0.5 standard deviations:
- increase: +0.5 standard deviations;
- decrease: -0.5 standard deviations;
- unspecified: +0.5 standard deviations by the task's existing
  positive-perturbation convention.

When direction is unspecified, this is a computational convention,
NOT a direction requested by the user.

Use the sign of the actual DELTA in the report to determine whether
each feature increased or decreased:
- positive delta = the numerical feature increased;
- negative delta = the numerical feature decreased.

Never infer direction from whether the baseline or scenario value
is positive or negative. For example, a change from -0.94 to -0.93
is an increase in the numerical feature.

For entities mapped to multiple features, describe the actual
perturbation of each component. Do not assume that the broad
ecological concept itself was directly simulated.

Although the perturbation is standardized in units of each feature's
standard deviation, the physical/ecological meaning and magnitude
are not necessarily comparable across different features. Do not
treat the two perturbations as equivalent real-world changes.

3. NUMERICAL PERTURBATIONS ARE NOT MANAGEMENT INTERVENTIONS
------------------------------------------------------------

A numerical increase or decrease in a feature must not automatically
be described as a real-world ecological intervention or management
action.

For example:
- increasing tree-cover density is not automatically a simulation
  of tree-cover restoration;
- increasing the number of potentially living species is not
  automatically a simulation of biodiversity conservation;
- perturbing precipitation or evapotranspiration features is not
  automatically a complete simulation of hydrological stress,
  climate stress, or a stress-reduction intervention.

If the user asks which management intervention would be more
effective, state explicitly that this task does not evaluate
intervention effectiveness. Report only the model responses to the
numerical feature perturbations actually performed. Do not select
or recommend an intervention based on these results.

4. INTERPRETATION OF SIGNED RISK IMPACTS
------------------------------------------------------------

The two impacts are changes in predicted ecosystem risk calculated
independently against the SAME baseline prediction.

Interpret the signs as follows:
- positive impact = predicted ecosystem risk increased relative
  to the common baseline;
- negative impact = predicted ecosystem risk decreased relative
  to the common baseline;
- zero or near-zero impact = little or no change was detected in
  the model prediction for that tested perturbation at the reported
  numerical precision.

The task rounds impacts to four decimal places before they are
passed to this RAG layer. Therefore, a reported zero may reflect
rounding and must not be described as proof of exactly zero
sensitivity or ecological influence.

The absolute value represents the magnitude of the model response.
If one absolute impact is larger, state only that the model response
was larger for THAT tested perturbation.

Do not conclude that the corresponding variable is intrinsically
more important, more influential in general, or ecologically more
significant. Do not describe the result as a causal contribution
or as proof that a variable has no ecological influence.

5. GROUPS OF FEATURES
------------------------------------------------------------

For an entity composed of multiple numerical features, all component
features are perturbed simultaneously in the specified direction.
The group effect is computed from the combined scenario prediction;
component effects are not summed.

Describe the component features actually perturbed. Do not attribute
the combined numerical response to a specific component feature
unless the available results support that conclusion.

6. RISK IS NOT RESILIENCE
------------------------------------------------------------

The model output reported by this task is a predicted ecosystem-risk
score. It is not a direct measurement of ecosystem resilience.

If the user asks which factor controls, determines, or improves
ecosystem resilience, do not claim that this task has measured
resilience. Explain that the available result supports only a
comparison of predicted risk responses to the tested perturbations.
Do not equate lower predicted risk with a directly measured increase
in resilience.

7. ECOLOGICAL INTERPRETATION AND RETRIEVED EVIDENCE
------------------------------------------------------------

These outputs describe model responses under numerical scenarios.
They do not establish direct ecological causality or observed
environmental change.

Use retrieved scientific evidence only to provide ecological
context directly supported by the retrieved material.

Documented ecological mechanisms may be described as scientific
context when supported by retrieved evidence. Do not present them
as the explanation for a numerical model response unless the
evidence directly supports that connection. The numerical output
alone does not identify the ecological mechanism responsible
for the predicted impact.

Do not invent mechanisms, claim unsupported causal relations,
or force an ecological explanation when the retrieved evidence
is not sufficiently relevant. Do not introduce unsupported
conservation or management recommendations.

8. FINAL RESPONSE
------------------------------------------------------------

Clearly distinguish:
- the ecological concepts mentioned in the question;
- the numerical features actually perturbed;
- the actual direction and magnitude of each perturbation;
- the resulting change in predicted ecosystem risk;
- the ecological context supported by retrieved evidence.

Answer the user's specific question directly. If the requested
claim (for example, intervention effectiveness or resilience)
cannot be established by these outputs, say so explicitly and
then state what the model comparison can establish.

Do not change, recalculate, reverse, or contradict the reported
impact values or their signs. Do not produce an intrinsic
importance ranking.
"""


# ======================================================
# MAIN
# ======================================================

def generate_importance_compare_explanation(
    question,
    entity_a,
    entity_b,
    feature_a,
    feature_b,
    direction_a,
    direction_b,
    impact_a,
    impact_b,
    perturbations_a,
    perturbations_b,
    features=None
):

    print("\n[RAG-IMPORTANCE-COMPARE] START\n")

    print(
        f"[RAG] profile={LLM_PROFILE} "
        f"style={LLM_STYLE}"
    )

    def describe_scenario(entity, direction, impact):
        if direction == "unspecified":
            direction_text = (
                "the user did not specify a direction; "
                "the task applied its positive-perturbation convention "
                "(+0.5 standard deviations to each mapped feature)"
            )
        else:
            direction_text = (
                f"the task applied a {direction} perturbation "
                "(0.5 standard deviations) to the mapped numerical feature(s)"
            )

        return (
            f"For the question concept '{entity}', {direction_text}; "
            f"the model predicts a risk change of {impact:+.6f}"
        )

    comparison_statement = (
        describe_scenario(entity_a, direction_a, impact_a)
        + ". "
        + describe_scenario(entity_b, direction_b, impact_b)
        + "."
    )

    print("[DEBUG] computed comparison =", comparison_statement)

    # --------------------------------------------------
    # FEATURE TEXT
    # --------------------------------------------------

    feature_a_text = feature_to_text(feature_a)
    feature_b_text = feature_to_text(feature_b)

    # --------------------------------------------------
    # RETRIEVAL QUERY — keep feature-based retrieval unchanged
    # --------------------------------------------------

    rag_query = f"""
    {feature_a_text}

    {feature_b_text}

    ecosystem risk
    biodiversity
    ecosystem resilience
    land use
    hydrology
    """

    print("\n[DEBUG] RAG QUERY:")
    print(rag_query)

    # --------------------------------------------------
    # PROMPT
    # --------------------------------------------------

    if USE_LEGACY_PROMPTS:
        prompt = build_legacy_prompt(
            question,
            comparison_statement
        )
    else:
        report = build_importance_compare_report(
            question=question,
            entity_a=entity_a,
            entity_b=entity_b,
            direction_a=direction_a,
            direction_b=direction_b,
            impact_a=impact_a,
            impact_b=impact_b,
            perturbations_a=perturbations_a,
            perturbations_b=perturbations_b,
            comparison_statement=comparison_statement
        )

        notes = build_importance_compare_notes()

        prompt = f"""
    QUESTION:
    {question}

    {report}

    {notes}

    ============================================================
    FINAL INSTRUCTION — APPLY THIS TASK DEFINITION
    ============================================================

    The task-specific rules above define the meaning of this request
    and take precedence over generic or legacy wording about importance
    scores, variable rankings, driver contributions, or higher-ranked
    drivers.

    Interpret this as a comparison of model sensitivity to the two
    numerical perturbations reported above. Do not produce an intrinsic
    importance ranking. Do not infer intervention effectiveness or
    ecosystem resilience from predicted-risk changes. Explicitly state
    when the user's broader ecological concept is not directly measured.

    ============================================================
    RETRIEVED SCIENTIFIC EVIDENCE
    ============================================================

    """
        

    # --------------------------------------------------
    # CALL — preserve modular RAG invocation
    # --------------------------------------------------

    try:
        if DEBUG:
            print("\n========== EXTRA PROMPT ==========\n")
            print(prompt)
            print("\n==================================\n")

        result = generate_answer(
            question=rag_query,
            prompt_question=question,
            features=features,
            extra_prompt=prompt,
            modular_prompt=True
        )

        cleaned = clean_output(result)

        if cleaned:
            print("\n[RAG OUTPUT]")
            print(cleaned)
            print("\n[RAG-IMPORTANCE-COMPARE] END\n")
            return cleaned

        return comparison_statement

    except Exception as e:
        print("\n[RAG ERROR]")
        print(e)

        return fallback_compare_explanation(
            entity_a,
            entity_b,
            direction_a,
            direction_b,
            impact_a,
            impact_b
        )
