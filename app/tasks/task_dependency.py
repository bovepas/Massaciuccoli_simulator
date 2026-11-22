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
    compute_risk_perturbation_sensitivity,
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
    "ecosystem stability": "ecosystem stability",
    "ecosystem productivity": "ecosystem productivity",
    "ecosystem risk": "risk_score",
    "ecological risk": "risk_score",
    "risk score": "risk_score",
    "risk": "risk_score",
    "water availability": "hydrological dynamics",
    "water level": "hydrological dynamics",
    "water": "hydrological dynamics",
    "nutrients": "nutrient loading",
    "productivity": "ecosystem productivity",
    "biodiversity": "biodiversity",
    # Generic ecosystem references default to the CSV risk classification.
    "ecosystem": "risk_score",
    "lake": "risk_score",
    "environment": "risk_score",
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
    "risk_score"
    ],
}


# ======================================================
# ABSTRACT TARGET EXTRACTION
# ======================================================

def extract_abstract_target(question: str):

    q = question.lower()

    for k, v in ABSTRACT_KEYWORDS.items():

        if k in q:
            return v

    return None


# ======================================================
# TARGET RESOLUTION
# ======================================================

def resolve_dependency_targets(target):

    # Defensive compatibility: callers should pass an abstract concept string,
    # not the list returned by normalize_feature_name().
    if isinstance(target, list):
        return target

    target_aliases = {
        "water availability": "hydrological dynamics",
        "water": "hydrological dynamics",
        "water level": "hydrological dynamics",
        "hydrology": "hydrological dynamics",
    }
    raw_key = str(target).strip().lower().replace("_", " ")
    risk_aliases = {
        "risk", "risk score", "ecosystem risk", "ecological risk",
        "ecological conditions",
        "ecosystem risk classification according to a variational autoencoder with a later application of a multi k means process",
        "massaciuccoli lake ecosystem", "lake ecosystem", "ecosystem health",
        "environment of massaciuccoli",
    }
    explicit_nonrisk_abstract = any(term in raw_key for term in (
        "ecosystem stability", "ecosystem productivity", "biodiversity"
    ))
    if (raw_key in risk_aliases
            or "lake ecosystem" in raw_key
            or "ecosystem health" in raw_key
            or ("ecosystem" in raw_key and not explicit_nonrisk_abstract)
            or "environment of massaciuccoli" in raw_key):
        return ["risk_score"]

    abstract_target = target_aliases.get(raw_key, target)

    if abstract_target in ABSTRACT_DEPENDENCY_TARGETS:
        return ABSTRACT_DEPENDENCY_TARGETS[abstract_target]

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
# FILTER SELF-TARGETS
# ======================================================

def filter_self_targets(source, targets):
    """Esclude i target che coincidono con la sorgente."""

    if not source:
        return list(targets or [])

    source_key = str(source).strip().casefold()
    filtered_targets = []

    for target in targets or []:
        target_key = str(target).strip().casefold()

        if target_key == source_key:
            print(
                "[DEBUG] Excluding self-target from dependency aggregation:",
                target
            )
            continue

        filtered_targets.append(target)

    return filtered_targets

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

def handle_dependency(question, route, dependency_inputs=None, model=None, dataset=None):

    print("\n========== DEPENDENCY TASK START ==========")
    print("# USING HYBRID DEPENDENCY TASK")

    # --------------------------------------------------
    # PARSE
    # --------------------------------------------------

    if dependency_inputs is not None:

        source = dependency_inputs.get("driver")
        target = dependency_inputs.get("target")

        target_raw = target
        delta = None

    else:

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

    resolved_targets = filter_self_targets(
        source,
        resolved_targets
    )

    print("[DEBUG] Resolved targets after self-target filter:")
    print(resolved_targets)

    # --------------------------------------------------
    # DEPENDENCY COMPUTATION
    # --------------------------------------------------

    if "risk_score" in resolved_targets:
        # Infer whether the user explicitly asks about an increase/decrease.
        q = question.lower()
        if any(term in q for term in ("decreas", "reduc", "lower", "fall", "declin")):
            perturbation_direction = "decrease"
        else:
            # Increasing from Q25 to Q75 is the conventional direction for
            # qualitative dependency questions without a directional verb.
            perturbation_direction = "increase"

        try:
            dependency_info = compute_risk_perturbation_sensitivity(
                source=source,
                model=model,
                dataset=dataset,
                direction=perturbation_direction,
            )
        except Exception as exc:
            print("[DEPENDENCY RF PERTURBATION ERROR]", exc)
            dependency_info = {
                "supported": False,
                "method": "random_forest_q25_q75_perturbation",
                "target": "risk_score",
                "driver": source,
                "score": 0.0,
                "strength": "unsupported",
                "direction": "unknown",
                "interaction_type": "generic ecosystem risk dependency",
                "confidence": "low",
                "error": str(exc),
            }
        resolved_targets = ["risk_score"]
    else:
        # Preserve existing feature-to-feature behavior. It is an observed
        # Pearson association, not Random-Forest perturbation sensitivity.
        all_results = []
        for resolved_target in resolved_targets:
            result = compute_dependency_strength(
                source=source,
                target=resolved_target
            )
            all_results.append(result)
        dependency_info = aggregate_dependency_results(all_results)
        dependency_info["method"] = "pearson_feature_association"

    print("[DEBUG] Aggregated dependency info:")
    print(dependency_info)

    # --------------------------------------------------
    # SEMANTIC FEATURES
    # --------------------------------------------------

    semantic_features = []

    if source:
        semantic_features.append(source)

    semantic_features.extend(
        resolved_targets
    )

    print(
        "[DEBUG] semantic_features:"
    )

    print(
        semantic_features
    )

    # --------------------------------------------------
    # RAG INTERPRETATION
    # --------------------------------------------------

    explanation = generate_dependency_explanation(

        question=question,

        source=source,

        target=target,

        dependency_info=dependency_info,

        features=semantic_features

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
        "ecosystem risk"
        if "risk_score" in resolved_targets
        else (target_raw if target_raw else simplify(target))
    )
    #print("[DEBUG] target:", repr(target))
    #print("[DEBUG] target_raw:", repr(target_raw))
    #print("[DEBUG] human_target:", repr(human_target))
    # --------------------------------------------------
    # SUMMARY
    # --------------------------------------------------

    if source:
        source_label = simplify(source).capitalize()
        target_label = str(human_target).strip()

        summary = f"Effect of {source_label} on {target_label}"

    else:
        summary = "Conceptual dependency analysis"

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
            resolved_targets,

        "method": dependency_info.get("method"),

        "perturbation": dependency_info.get("perturbation"),

        "baseline_mean_risk": dependency_info.get("baseline_mean_risk"),

        "perturbed_mean_risk": dependency_info.get("perturbed_mean_risk"),

        "mean_delta_risk": dependency_info.get("mean_delta_risk"),

        "mean_absolute_delta_risk": dependency_info.get("mean_absolute_delta_risk"),

        "positive_response_fraction": dependency_info.get("positive_response_fraction"),

        "negative_response_fraction": dependency_info.get("negative_response_fraction"),

        "unchanged_fraction": dependency_info.get("unchanged_fraction"),

        "n_cells": dependency_info.get("n_cells")
    }

    print("\n========== DEPENDENCY TASK END ==========\n")

    return {

        "summary": summary,

        "data": data,

        "drivers": variables,

        "interpretation": explanation
    }