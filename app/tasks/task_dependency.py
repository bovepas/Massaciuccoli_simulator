# -*- coding: utf-8 -*-

"""
Dependency Task — v15 (hybrid dependency orchestration)

✔ Quantitative dependency evidence
✔ Abstract ecosystem targets
✔ Dependency aggregation
✔ KB-grounded interpretation
✔ Semantic interaction typing
✔ Preserves existing UX structure
"""

from utils.dependency_parser import parse_dependency

from utils.dependency_utils import (
    compute_dependency_strength
)

from knowledge.rag_dependency import (
    generate_dependency_explanation
)

from utils.dependency_utils import (
    compute_dependency_strength,
    classify_dependency
)

# ======================================================
# HUMAN READABLE FEATURE
# ======================================================

def humanize_feature(name: str):

    if not name:
        return ""

    name = name.lower()

    if "species" in name:
        return "Biodiversity"

    if "temperature" in name:
        return "Temperature"

    if "precipitation" in name:
        return "Precipitation"

    if "tree cover" in name:
        return "Vegetation (tree cover)"

    if "evapotranspiration" in name:
        return "Evapotranspiration"

    return name


# ======================================================
# ABSTRACT TARGET DETECTION
# ======================================================

ABSTRACT_KEYWORDS = {

    "water availability":
        "hydrological dynamics",

    "water":
        "hydrological dynamics",

    "water level":
        "hydrological dynamics",

    "nutrients":
        "nutrient loading",

    "productivity":
        "ecosystem productivity",

    "ecosystem":
        "ecosystem stability",

    "biodiversity":
        "biodiversity",

    "risk":
        "ecosystem risk"
}


# ======================================================
# ABSTRACT DEPENDENCY TARGETS
# ======================================================

ABSTRACT_DEPENDENCY_TARGETS = {

    "hydrological dynamics": [

        "Cumulative change in precipitation compared to a recent past",

        "Relative change in the potential evapotranspiration compared to a recent past"
    ],

    "ecosystem productivity": [

        "Index of total productivity by plant phenology"
    ],

    "biodiversity": [

        "Number of species potentially living in the cell"
    ],

    "ecosystem stability": [

        "Number of species potentially living in the cell",

        "Index of total productivity by plant phenology"
    ]
}


# ======================================================
# ABSTRACT TARGET EXTRACTION
# ======================================================

def extract_abstract_target(question: str):

    q = question.lower()

    for k, v in ABSTRACT_KEYWORDS.items():

        if k in q:
            return v

    return "ecosystem stability"


# ======================================================
# TARGET RESOLUTION
# ======================================================

def resolve_dependency_targets(target):

    if target in ABSTRACT_DEPENDENCY_TARGETS:

        return ABSTRACT_DEPENDENCY_TARGETS[target]

    return [target]


# ======================================================
# SOURCE FALLBACK
# ======================================================

def extract_source_from_question(question: str):

    q = question.lower()

    if "evapotranspiration" in q:

        return (
            "Relative change in the potential "
            "evapotranspiration compared to a recent past"
        )

    if "temperature" in q:

        return (
            "Change in average temperature "
            "compared to a recent past"
        )

    if "precipitation" in q:

        return (
            "Cumulative change in precipitation "
            "compared to a recent past"
        )

    if "biodiversity" in q or "species" in q:

        return (
            "Number of species potentially "
            "living in the cell"
        )

    if "tree cover" in q:

        return "Density of tree cover"

    return None


# ======================================================
# CLEAN HELPERS
# ======================================================

def simplify(name: str):

    if not name:
        return ""

    name = name.lower()

    if "temperature" in name:
        return "temperature"

    if "precipitation" in name:
        return "precipitation"

    if "evapotranspiration" in name:
        return "evapotranspiration"

    if "species" in name:
        return "biodiversity"

    if "tree cover" in name:
        return "tree cover"

    return name


def simplify_text(text: str):

    if not text:
        return text

    replacements = {

        "Change in average temperature compared to a recent past":
            "temperature",

        "Cumulative change in precipitation compared to a recent past":
            "precipitation",

        "Relative change in the potential evapotranspiration compared to a recent past":
            "evapotranspiration",

        "Number of species potentially living in the cell":
            "biodiversity",

        "Density of tree cover":
            "tree cover"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


# ======================================================
# AGGREGATION
# ======================================================

def aggregate_dependency_results(results):

    if not results:

        return {

            "supported": False,

            "score": 0.0,

            "strength": "unsupported",

            "direction": "unknown",

            "interaction_type": "generic ecosystem interaction",

            "confidence": "low"
        }

    valid = [

        r for r in results
        if r.get("supported")
    ]

    if not valid:

        return {

            "supported": False,

            "score": 0.0,

            "strength": "unsupported",

            "direction": "unknown",

            "interaction_type": "generic ecosystem interaction",

            "confidence": "low"
        }

    avg_score = sum(
        r["score"] for r in valid
    ) / len(valid)

    # dominant interaction
    interaction_type = max(
        valid,
        key=lambda x: x["score"]
    )["interaction_type"]

    # dominant direction
    direction = max(
        valid,
        key=lambda x: x["score"]
    )["direction"]

    # confidence
    confidence_levels = {
        "low": 1,
        "moderate": 2,
        "high": 3
    }

    max_conf = max(
        valid,
        key=lambda x: confidence_levels.get(
            x["confidence"],
            0
        )
    )["confidence"]

    # calibrated strength
    strength = classify_dependency(
        avg_score
    )

    return {

        "supported": True,

        "score": round(avg_score, 3),

        "strength": strength,

        "direction": direction,

        "interaction_type": interaction_type,

        "confidence": max_conf
    }


# ======================================================
# MAIN
# ======================================================

def handle_dependency(question, route):

    print("\n========== DEPENDENCY TASK START ==========")
    print("# USING HYBRID DEPENDENCY TASK")

    # --------------------------------------------------
    # PARSE
    # --------------------------------------------------

    parsed = parse_dependency(question)

    source = parsed.get("source")
    target = parsed.get("target")
    target_raw = parsed.get("target_raw")
    delta = parsed.get("delta")

    # --------------------------------------------------
    # ABSTRACT TARGET
    # --------------------------------------------------

    if target is None:
        target = extract_abstract_target(question)

    # --------------------------------------------------
    # SOURCE FALLBACK
    # --------------------------------------------------

    if source is None:
        source = extract_source_from_question(question)

    print("[DEBUG] Source:", source)
    print("[DEBUG] Target:", target)
    print("[DEBUG] Target raw:", target_raw)
    print("[DEBUG] Delta:", delta)

    # --------------------------------------------------
    # TARGET RESOLUTION
    # --------------------------------------------------

    resolved_targets = resolve_dependency_targets(
        target
    )

    print("[DEBUG] Resolved targets:")
    print(resolved_targets)

    # --------------------------------------------------
    # DEPENDENCY COMPUTATION
    # --------------------------------------------------

    all_results = []

    for resolved_target in resolved_targets:

        result = compute_dependency_strength(

            source=source,

            target=resolved_target
        )

        all_results.append(result)

    dependency_info = aggregate_dependency_results(
        all_results
    )

    print("[DEBUG] Aggregated dependency info:")
    print(dependency_info)

    # --------------------------------------------------
    # RAG INTERPRETATION
    # --------------------------------------------------

    explanation = generate_dependency_explanation(

        question=question,

        source=source,

        target=target,

        dependency_info=dependency_info
    )

    # --------------------------------------------------
    # CLEAN TEXT
    # --------------------------------------------------

    explanation = simplify_text(explanation)

    # --------------------------------------------------
    # REMOVE LLM INTRO
    # --------------------------------------------------

    if explanation.startswith("Here is"):

        explanation = (
            explanation
            .split(":", 1)[-1]
            .strip()
        )

    # --------------------------------------------------
    # CAPITALIZE
    # --------------------------------------------------

    if explanation:

        explanation = (
            explanation[0].upper()
            + explanation[1:]
        )

    # --------------------------------------------------
    # VARIABLES
    # --------------------------------------------------

    variables = []

    if source:

        variables.append(
            humanize_feature(source)
        )

    # --------------------------------------------------
    # HUMAN TARGET
    # --------------------------------------------------

    human_target = (
        target_raw
        if target_raw
        else simplify(target)
    )

    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    if source:

        summary = (
            f"Effect of "
            f"{simplify(source).capitalize()} "
            f"on {human_target}"
        )

        summary = summary.replace(
            "on on",
            "on"
        )

    else:

        summary = (
            "Conceptual dependency analysis"
        )

    # --------------------------------------------------
    # STRUCTURED DATA
    # --------------------------------------------------

    data = {

        "dependency_strength":
            dependency_info.get("strength"),

        "dependency_score":
            dependency_info.get("score"),

        "interaction_type":
            dependency_info.get("interaction_type"),

        "confidence":
            dependency_info.get("confidence"),

        "direction":
            dependency_info.get("direction"),

        "resolved_targets":
            resolved_targets
    }

    print("\n========== DEPENDENCY TASK END ==========\n")

    return {

        "summary": summary,

        "data": data,

        "drivers": variables,

        "interpretation": explanation
    }