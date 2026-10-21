# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Data — modular prompt version

Purpose:
- Interpret current ecosystem indicators from Live_update.csv.
- Retrieve scientific evidence through the shared RAG pipeline.
- Separate reported observations from evidence-supported interpretation.
- Avoid unsupported ecological conclusions.
"""

from knowledge.rag_pipeline import generate_answer
from utils.prompt_builder import build_prompt, USE_LEGACY_PROMPTS


DEBUG = True


# ======================================================
# DEBUG
# ======================================================

def debug_print(*args):
    if DEBUG:
        print("[RAG-DATA]", *args)


# ======================================================
# DATA FORMATTING
# ======================================================

def _direction_note(indicator_name):
    """
    Return a conservative interpretation note for indicators whose labels
    are known to be ambiguous or explicitly directional.
    """
    name = str(indicator_name).strip().lower()

    # These indicators report that a change occurred, but not its direction.
    if (
        "imperviousness" in name
        and ("changed" in name or "change" in name)
        and ("area" in name or "percentage" in name or "%" in name)
    ):
        return (
            "DIRECTION UNSPECIFIED: this is the share of area where "
            "imperviousness changed; it does not say whether imperviousness "
            "increased or decreased."
        )

    if (
        "tree cover density" in name
        and ("change" in name or "changed" in name)
    ):
        return (
            "DIRECTION UNSPECIFIED: the indicator reports a change in tree "
            "cover density, but its label does not state whether it increased "
            "or decreased. Do not infer direction from an unsigned value."
        )

    # Loss and gain indicators must remain distinct.
    if "grassland" in name and ("lost" in name or "loss" in name):
        return (
            "DIRECTION EXPLICIT: this is a grassland-loss indicator. "
            "Report it as loss; do not treat it as net change in grassland."
        )

    if "grassland" in name and ("gained" in name or "gain" in name):
        return (
            "DIRECTION EXPLICIT: this is a grassland-gain indicator. "
            "Report it separately from grassland loss; do not treat it as "
            "net change in grassland."
        )

    # Current coverage is a level, not a trend.
    if (
        "covered by trees" in name
        or "tree cover" in name and "density" not in name
        and "change" not in name
    ):
        return (
            "CURRENT LEVEL ONLY: this value does not establish a trend "
            "or stability over time."
        )

    return None


def format_live_indicators(indicators):
    """
    Convert live indicators into a readable text block.

    Accepts pandas.Series, dict, or another object exposing items().
    Adds explicit notes only for known direction ambiguities.
    """

    if indicators is None:
        return "Current environmental indicators are unavailable."

    try:
        items = indicators.items()
    except AttributeError:
        return (
            "Current environmental indicators could not be formatted "
            "because the supplied data has an unsupported structure."
        )

    lines = []

    for name, value in items:
        if value is None:
            continue

        # Ignore NaN without requiring an additional dependency.
        try:
            if value != value:
                continue
        except (TypeError, ValueError):
            pass

        clean_name = str(name).strip()
        lines.append(f"- {clean_name}: {value}")
        note = _direction_note(clean_name)
        if note:
            lines.append(f"  Interpretation constraint: {note}")

    if not lines:
        return "No valid current environmental indicators are available."

    return "\n".join(lines)


# ======================================================
# RAG QUERY
# ======================================================

def build_data_query(question, indicators=None):
    """Build a broad query for ecosystem overviews or a focused query for one indicator."""

    if indicators is not None:
        try:
            names = [
                str(name).strip()
                for name, value in indicators.items()
                if value is not None
                and "reference year" not in str(name).lower()
                and "last year" not in str(name).lower()
            ]
        except AttributeError:
            names = []
    else:
        names = []

    # A focused live-data request should retrieve evidence about that indicator,
    # not a generic mixture of climate, biodiversity, land use and risk topics.
    if len(names) == 1:
        return (
            f"Massaciuccoli Lake {names[0]}. "
            "Scientific interpretation, reference period, units, and limitations "
            "of this environmental indicator. "
            f"User question: {question}"
        )

    return f"""
Massaciuccoli Lake ecosystem environmental status
current environmental indicators and ecosystem condition
ecosystem risk assessment and interpretation
land use and land cover changes
tree cover and grassland indicators
temperature precipitation and evaporation
biodiversity and species richness
human pressure and ecological vulnerability
scientific evidence and limitations of ecosystem indicators

User question:
{question}
""".strip()


# ======================================================
# LEGACY PROMPT
# ======================================================

def build_legacy_data_prompt(indicators_text):
    """
    Compatibility prompt used only when USE_LEGACY_PROMPTS is enabled.
    The modular task instructions live in prompts/tasks/data.txt.
    """

    return f"""
You are an environmental scientist assisting the Massaciuccoli Digital Twin.
Provide a concise, cautious interpretation of the current environmental
indicators and the scientific evidence retrieved by the RAG pipeline.

CURRENT LIVE INDICATORS
{indicators_text}

Treat these values as reported observations, not automatically as model
predictions, causes, or proof of ecological improvement or degradation.
Preserve the reported values, units, reference periods, and original meaning.
Do not invent trends, baselines, future projections, causal relationships,
or ecological classifications. Never treat missing data as zero.
Distinguish evidence specific to Lake Massaciuccoli from general scientific
knowledge about wetlands. If the evidence does not support a conclusion,
state that limitation.

Use these sections:
OBSERVED INDICATORS
SCIENTIFIC INTERPRETATION
LIMITATIONS AND UNCERTAINTIES
""".strip()


# ======================================================
# MAIN
# ======================================================

def generate_data_explanation(question, indicators):
    """
    Generate an evidence-grounded interpretation of current
    ecosystem indicators.

    Parameters
    ----------
    question : str
        Original user question.
    indicators : pandas.Series or dict
        Indicators supplied by the live-data loader.

    Returns
    -------
    str
        Scientific interpretation of the available indicators.
    """

    print("\n[RAG-DATA v3] START")

    indicators_text = format_live_indicators(indicators)
    rag_query = build_data_query(question, indicators)

    if USE_LEGACY_PROMPTS:
        extra_prompt = build_legacy_data_prompt(indicators_text)
    else:
        # Follow the modular architecture used by the other RAG tasks:
        # base + original question + model + style + tasks/data.txt.
        # Dynamic live values are appended separately and kept compact.
        extra_prompt = (
            build_prompt("data", question=question)
            + "\n\n"
            + "CURRENT LIVE INDICATORS\n"
            + "The following values are reported by the live-data source.\n"
            + indicators_text
        )

    debug_print("Retrieval query:")
    debug_print(rag_query)

    debug_print("Available indicator count:")
    debug_print(
        len(indicators)
        if hasattr(indicators, "__len__")
        else "unknown"
    )

    if DEBUG:
        print("\n========== RAG-DATA TASK PROMPT ==========")
        print(extra_prompt)
        print("========== END RAG-DATA TASK PROMPT ======")
        print("RAG-DATA task prompt length:", len(extra_prompt))

    try:
        answer = generate_answer(
            question=rag_query,
            features=None,
            extra_prompt=extra_prompt
        )

        if not isinstance(answer, str) or not answer.strip():
            return (
                "A scientific interpretation of the current ecosystem "
                "state is unavailable."
            )

        debug_print("Interpretation generated.")
        print("[RAG-DATA v3] END\n")
        return answer.strip()

    except Exception as exc:
        print("[RAG-DATA ERROR]", exc)
        return (
            "The current environmental indicators were available, "
            "but the scientific interpretation could not be generated "
            "because the RAG pipeline encountered an error."
        )
