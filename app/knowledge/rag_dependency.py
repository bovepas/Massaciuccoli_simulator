# -*- coding: utf-8 -*-

"""
RAG Dependency Explanation — v15

✔ Reduced prompt verbosity
✔ Smaller retrieval context
✔ Cleaner dependency grounding
✔ Faster generation
✔ Preserved uncertainty handling
✔ More compact scientific explanations
"""

from knowledge.rag_pipeline import generate_answer

from utils.prompt_builder import (
    build_prompt,
    USE_LEGACY_PROMPTS
)

# ======================================================
# CONFIG
# ======================================================

MAX_CONTEXT_CHARS = 1000
DEBUG = True

# ======================================================
# TARGET NORMALIZATION FOR RETRIEVAL
# ======================================================

TARGET_QUERY_MAP = {

    "hydrological dynamics":
        "water balance lake level hydrology",

    "ecosystem stability":
        "ecosystem stability lake dynamics",

    "ecosystem productivity":
        "primary productivity lake ecosystem",

    "biodiversity":
        "species richness biodiversity ecosystem",

    "ecosystem risk":
        "ecosystem risk environmental stress lake",

    "risk_score":
        "ecosystem risk environmental stress lake"
}


def normalize_target_for_query(target: str):

    if not target:
        return ""

    return TARGET_QUERY_MAP.get(
        target,
        target
    )


# ======================================================
# DEPENDENCY EVIDENCE BLOCK
# ======================================================

def build_dependency_block(dependency_info):

    if not dependency_info:

        return """
DEPENDENCY EVIDENCE:
No quantitative dependency evidence available.
"""

    return f"""
DEPENDENCY EVIDENCE:

- Strength:
  {dependency_info.get('strength')}

- Score:
  {dependency_info.get('score')}

- Interaction type:
  {dependency_info.get('interaction_type')}

- Confidence:
  {dependency_info.get('confidence')}

- Direction:
  {dependency_info.get('direction')}
"""

# ======================================================
# DEPENDENCY REPORT
# ======================================================

def _format_number(value, digits=6):
    """Format numeric report values without failing on missing data."""
    if value is None:
        return "not available"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _format_fraction_as_percent(value):
    """Convert model response fractions (0-1) to readable percentages."""
    if value is None:
        return "not available"
    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return str(value)


def _is_random_forest_perturbation(dependency_info):
    method = str((dependency_info or {}).get("method", "")).lower()
    return "random_forest" in method and "perturbation" in method


def _get_perturbation_label(perturbation):
    """Build a method-neutral label supporting Q10-Q90, Q25-Q75, etc."""
    if not isinstance(perturbation, dict):
        return "distribution-based interval"

    quantile_keys = [
        key for key in ("q05", "q10", "q25", "q75", "q90", "q95")
        if key in perturbation
    ]
    if len(quantile_keys) >= 2:
        return " to ".join(key.upper() for key in quantile_keys)

    ptype = str(perturbation.get("type", "")).replace("_", " ")
    return ptype or "distribution-based interval"


# ======================================================
# DEPENDENCY REPORT
# ======================================================

def build_dependency_report(
    source,
    target,
    dependency_info
):

    if not dependency_info:
        return """
============================================================
DIGITAL TWIN DEPENDENCY REPORT
============================================================

No dependency analysis is available.
"""

    if _is_random_forest_perturbation(dependency_info):
        report = f"""
============================================================
DIGITAL TWIN DEPENDENCY REPORT
============================================================

SOURCE VARIABLE
------------------------------------------------------------

{source}

TARGET VARIABLE
------------------------------------------------------------

{target}

IDENTIFIED RELATIONSHIP
------------------------------------------------------------

Relationship type:
{dependency_info.get('interaction_type', 'not available')}

Relationship direction:
{dependency_info.get('direction', 'unknown')}

MODEL RESPONSE
------------------------------------------------------------

Intensity of the model response:
{dependency_info.get('strength', 'unknown')}

How consistently the area responds:
{dependency_info.get('confidence', 'unknown')}

Size of the average change in predicted ecological risk:
{_format_number(dependency_info.get('score'))}

Method:
{dependency_info.get('method', 'not available')}
"""
    else:
        report = f"""
============================================================
DIGITAL TWIN DEPENDENCY REPORT
============================================================

SOURCE VARIABLE
------------------------------------------------------------

{source}

TARGET VARIABLE
------------------------------------------------------------

{target}

IDENTIFIED RELATIONSHIP
------------------------------------------------------------

Relationship type:
{dependency_info.get('interaction_type', 'not available')}

Relationship direction:
{dependency_info.get('direction', 'unknown')}

MODEL CONFIDENCE
------------------------------------------------------------

Association strength:
{dependency_info.get('strength', 'unknown')}

Confidence:
{dependency_info.get('confidence', 'unknown')}

Association score:
{_format_number(dependency_info.get('score'))}

Method:
{dependency_info.get('method', 'not available')}
"""

    if _is_random_forest_perturbation(dependency_info):
        perturbation = dependency_info.get("perturbation") or {}
        interval_label = _get_perturbation_label(perturbation)
        report += f"""

RANDOM-FOREST COUNTERFACTUAL PERTURBATION RESULTS
------------------------------------------------------------

Perturbation method:
{dependency_info.get('method')}

Perturbed variable:
{source}

Perturbation direction:
{dependency_info.get('change_direction', 'not available')}

Empirical input interval in the dataset:
{interval_label}

Starting value:
{_format_number(perturbation.get('from_value'))}

Ending value:
{_format_number(perturbation.get('to_value'))}

Mean predicted risk before perturbation:
{_format_number(dependency_info.get('baseline_mean_risk'))}

Mean predicted risk after perturbation:
{_format_number(dependency_info.get('perturbed_mean_risk'))}

Mean change in predicted risk (after - before):
{_format_number(dependency_info.get('mean_delta_risk'))}

Mean absolute cell-level change in predicted risk:
{_format_number(dependency_info.get('mean_absolute_delta_risk'))}

Spatial distribution of cell-level model responses:
- Cells with increased predicted risk:
  {_format_fraction_as_percent(dependency_info.get('positive_response_fraction'))}
- Cells with decreased predicted risk:
  {_format_fraction_as_percent(dependency_info.get('negative_response_fraction'))}
- Cells with unchanged predicted risk:
  {_format_fraction_as_percent(dependency_info.get('unchanged_fraction'))}

Number of analysed cells:
{dependency_info.get('n_cells', 'not available')}

Confidence basis:
{dependency_info.get('confidence_basis', 'not available')}

INTERPRETATION OF THESE NUMBERS
------------------------------------------------------------

The mean change describes the average model response across all
analysed cells. The three percentages describe the spatial
distribution of cell-level responses. They are different
statistics and must not be conflated.
"""

    return report


# ======================================================
# ECOLOGICAL NOTES
# ======================================================

def build_dependency_notes(
    source,
    target
):

    return f"""
============================================================
ECOLOGICAL INTERPRETATION NOTES
============================================================

The reported dependency is a statistical relationship or a
sensitivity of the Digital Twin's trained surrogate model.
It is not, by itself, evidence of direct ecological causality,
an observed environmental change, or a forecast.

For Random-Forest perturbation results, one input variable is
changed across the stated interval while the other cell-level
input features are held fixed. The reported outputs therefore
describe how the surrogate model responds to that controlled
input change.

The mean change in predicted risk is an average across cells.
The percentages of cells with increased, decreased, or unchanged
predicted risk describe spatial heterogeneity. A positive mean
does not mean that every cell responds positively.

The association strength and confidence must be reported
separately. Confidence describes the stated confidence basis;
it must not be presented as predictive uncertainty unless the
report explicitly defines it that way.

Use retrieved scientific evidence to explain why the analysed
driver and target are ecologically relevant in the Massaciuccoli
basin. Distinguish evidence about broader climate or biodiversity
changes from evidence that directly supports this particular
modelled relationship.

Do not invent mechanisms, species-level effects, thresholds,
future projections, or numerical impacts that are absent from
the dependency report and retrieved evidence. Do not turn
statistical association or surrogate-model sensitivity into
causality.
"""


# ======================================================
# LEGACY PROMPT (FEATURE)
# ======================================================

def build_legacy_feature_prompt(
    source,
    target,
    dependency_block
):

    return f"""
You are an environmental scientist.

QUESTION:
How does {source} influence {target}?

MODEL RESULTS:
{dependency_block}

TASK

Provide a concise scientific explanation
of the observed ecological association.

Use the scientific knowledge base to
describe possible ecological mechanisms.

Interpret the relationship as an association,
not as direct causality.

Use cautious scientific language such as:
- "is associated with"
- "may contribute to"
- "appears related to"

Focus on:
- biodiversity
- hydrology
- climate interactions
- ecosystem stress

Write 3-4 concise sentences.

Answer:
"""

# ======================================================
# LEGACY PROMPT (RISK)
# ======================================================

def build_legacy_risk_prompt(
    source,
    dependency_block
):

    return f"""
You are an environmental scientist.

QUESTION:
How does {source} affect ecosystem risk?

MODEL RESULTS:
{dependency_block}

TASK

Provide a concise scientific explanation
of the observed ecological association.

Use the scientific knowledge base to
describe possible ecological mechanisms.

Interpret the relationship as an association,
not as direct causality.

Focus on:
- ecosystem stress
- biodiversity
- hydrology
- environmental pressures

Write 3-4 concise sentences.

Answer:
"""


# ======================================================
# MAIN
# ======================================================

def generate_dependency_explanation(
    question: str,
    source=None,
    target=None,
    dependency_info=None,
    features=None
) -> str:

    print("\n[RAG-DEPENDENCY v14] START")

    target_for_query = normalize_target_for_query(
        target
    )

    dependency_block = build_dependency_block(
        dependency_info
    )

    dependency_report = build_dependency_report(
        source,
        target,
        dependency_info
    )

    dependency_notes = build_dependency_notes(
        source,
        target
    )

    # ======================================================
    # CASE 1: FEATURE → FEATURE / ABSTRACT TARGET
    # ======================================================

    if (
        target
        and target != "risk_score"
        and not _is_random_forest_perturbation(dependency_info)
    ):

        if USE_LEGACY_PROMPTS:

            extra_prompt = build_legacy_feature_prompt(
                source,
                target,
                dependency_block
            )

        else:

            extra_prompt = (
                build_prompt("dependency")
                + f"""

ORIGINAL QUESTION:
{question}

{dependency_report}

{dependency_notes}

Use the retrieved scientific evidence to explain the
relationship. Distinguish statistical association from
causality and avoid unsupported ecological mechanisms.

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

"""
            )

    else:

        if USE_LEGACY_PROMPTS:

            extra_prompt = build_legacy_risk_prompt(
                source,
                dependency_block
            )

        else:

            if (
                str(target).strip().lower() == "ecosystem stability"
                and _is_random_forest_perturbation(dependency_info)
            ):

                extra_prompt = (
                    build_prompt("dependency")
                    + f"""

ORIGINAL QUESTION:
{question}

OPERATIONAL INTERPRETATION:

In this analysis, ecosystem stability is represented indirectly
through the Digital Twin's risk_score.

The risk_score is a proxy for ecological vulnerability, not a
direct measurement of ecosystem stability.

Interpret the relationship using the following inverse direction:
- an increase in predicted risk_score indicates a decrease in
  the stability proxy;
- a decrease in predicted risk_score indicates an increase in
  the stability proxy.

Do not describe risk_score and ecosystem stability as equivalent
quantities. Make clear that the model evaluates sensitivity of
its predicted ecological risk, not stability directly.

{dependency_report}

{dependency_notes}

When Random-Forest perturbation results are provided, explain them
explicitly and quantitatively:
- state the perturbed variable and the reported starting and ending values;
- report the mean predicted-risk change and its direction;
- explain what that change implies for the indirect stability proxy;
- report the percentages of cells with increased, decreased, and unchanged
  predicted risk;
- distinguish the average change from the spatial distribution of responses;
- explain what the retrieved ecological evidence adds to the interpretation.

Use the numerical values in the report; do not omit them merely to keep the
answer short. Do not imply that every cell responds in the same direction.
Describe these as responses of the surrogate model, not observed ecological
changes, causal effects, or forecasts.

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

"""
                )

            else:

                extra_prompt = (
                    build_prompt("dependency")
                    + f"""

QUESTION:
How does {source} affect ecosystem risk?

{dependency_report}

{dependency_notes}

When Random-Forest perturbation results are provided, explain them
explicitly and quantitatively:
- state the perturbed variable and the reported starting and ending values;
- report the mean predicted-risk change and its direction;
- report the percentages of cells with increased, decreased, and unchanged
  predicted risk;
- distinguish the average change from the spatial distribution of responses;
- explain what the retrieved ecological evidence adds to the interpretation.

Use the numerical values in the report; do not omit them merely to keep the
answer short. Do not imply that every cell responds in the same direction.
Describe these as responses of the surrogate model, not observed ecological
changes, causal effects, or forecasts.

============================================================
RETRIEVED SCIENTIFIC EVIDENCE
============================================================

"""
                )

    # ======================================================
    # QUERY
    # ======================================================

    rag_query = question

    if source:

        rag_query = f"""
        lake ecosystem
        {source}
        {target_for_query}
        biodiversity interaction
        """

    print("[RAG] Final query:")
    print(rag_query)

    print("[RAG] Dependency evidence:")
    print(dependency_info)

    # ======================================================
    # CALL RAG
    # ======================================================

    try:
        if DEBUG:

            print("\n========== EXTRA PROMPT ==========\n")
            print(extra_prompt)
            print("\n==================================\n")

        answer = generate_answer(

            question=rag_query,

            features=features,

            extra_prompt=extra_prompt
        )

        print("\n[RAG-DEPENDENCY] Output:")
        print(answer)

        print("[RAG-DEPENDENCY v14] END\n")

        return answer

    except Exception as e:

        print("[RAG-DEPENDENCY ERROR]")
        print(e)

        return (
            "Environmental interactions in lake ecosystems "
            "often emerge through coupled hydrological, "
            "climatic, and ecological processes, although "
            "the strength of specific dependencies may vary "
            "depending on available evidence and ecosystem conditions."
        )