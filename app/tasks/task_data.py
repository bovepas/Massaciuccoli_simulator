# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Data Task — v13

- Current ecosystem overview uses Live_update.csv + RAG.
- Single-feature requests retain the existing baseline pathway.
- No synthetic 2% changes.
- Missing features are never silently converted to zero.
"""

from utils.model_input_builder import compute_baseline
from utils.feature_mapping import normalize_feature_name
from tools.live_data_loader import load_live_data
from knowledge.rag_data import generate_data_explanation
from semantic_variable_catalog import (
    DATA_INTENT_TAGS,
    classify_data_query_intent,
    get_variables_for_intent,
)
import re


# ======================================================
# HUMAN LABELS
# ======================================================

def humanize_feature(name: str):

    if not name:
        return ""

    name = name.lower()

    if "temperature" in name:
        return "Average temperature change"

    if "precipitation" in name:
        return "Precipitation change"

    if "evapotranspiration" in name:
        return "Evapotranspiration change"

    if "tree cover density in the past decade" in name:
        return "Tree cover change (decade)"

    if "tree cover" in name:
        return "Tree cover density"

    if "species" in name:
        return "Biodiversity (species richness)"

    if "impervious" in name:
        return "Land imperviousness"

    if "productivity" in name:
        return "Ecosystem productivity index"

    if "land use and cover in the past decade" in name:
        return "Land use change (decade)"

    if "land use and cover" in name:
        return "Land use and cover"

    return name


# ======================================================
# FEATURE EXTRACTION
# ======================================================

def extract_feature_from_question(question: str, baseline: dict):

    q = question.lower()

    mapped = normalize_feature_name(q)

    if mapped and mapped in baseline:
        return mapped

    keyword_map = {
        "temperature": (
            "Change in average temperature compared to a recent past"
        ),
        "precipitation": (
            "Cumulative change in precipitation compared to a recent past"
        ),
        "biodiversity": (
            "Number of species potentially living in the cell"
        ),
        "tree cover": "Density of tree cover",
        "grassland": "Presence of grassland",
        "evapotranspiration": (
            "Relative change in the potential evapotranspiration "
            "compared to a recent past"
        ),
        "productivity": (
            "Index of total productivity by plant phenology"
        ),
    }

    for keyword, feature in keyword_map.items():
        if keyword in q and feature in baseline:
            return feature

    return None


# ======================================================
# DATASET CATALOG REQUEST DETECTION
# ======================================================

def is_dataset_catalog_request(question: str):
    """
    Detect broad requests asking which variables/data are represented
    in the dataset. These must not be interpreted as requests for the
    value of a single feature.
    """
    q = re.sub(r"[^a-z0-9%+ ]+", " ", (question or "").lower())
    q = " ".join(q.split())

    # Preserve the existing live/current ecosystem overview pathway.
    live_overview_phrases = (
        "latest data",
        "live data",
        "current state of the ecosystem",
        "state of the ecosystem",
        "current ecosystem state",
        "state of the lake",
        "current state of the lake",
        "current condition of the lake",
        "ecosystem status",
        "system status",
        "environmental conditions",
        "system conditions",
        "overall state",
    )
    if any(phrase in q for phrase in live_overview_phrases):
        return False

    catalog_phrases = (
        "environmental variables",
        "ecological variables",
        "environmental stressors",
        "aspects of ecosystem functioning",
        "all available variables",
        "available variables",
        "variables available",
        "variables included",
        "variables explicitly included",
        "variables explicitly measured",
        "variables represented",
        "variables in the dataset",
        "data available in the dataset",
        "what data are in the dataset",
        "what data is in the dataset",
        "what data does the dataset contain",
        "which data are available",
        "which variables are available",
        "which variables are included",
        "which variables are represented",
    )
    if "all variables" in q and "dataset" in q:
        return True

    return any(phrase in q for phrase in catalog_phrases)


def handle_dataset_catalog_request(question: str, dataset):
    """Return the actual model-baseline variable catalog."""
    print("[DATA] Dataset catalog request detected")

    if dataset is None:
        return {
            "summary": "Dataset variables unavailable",
            "data": {},
            "drivers": [],
            "interpretation": (
                "The dataset is not loaded, so its available variables "
                "cannot be listed."
            ),
        }

    baseline = compute_baseline(dataset)
    variables = list(baseline.keys())

    return {
        "summary": "Available dataset variables",
        "data": {"variables": variables},
        "drivers": [],
        "interpretation": (
            f"The model baseline contains {len(variables)} variables. "
            "The list reports the variables available to the model; "
            "it does not imply that every variable is an environmental "
            "stressor or a direct measure of ecosystem functioning."
        ),
    }



# ======================================================
# SEMANTIC CATEGORY CATALOG REQUESTS
# ======================================================

_CATALOG_RELATION_MARKERS = (
    "effect of", "effects of", "impact of", "impact on", "influence",
    "affect", "affects", "correlation", "correlate", "drivers of",
    "contributes", "cause", "causes", "increase risk", "reduce risk",
    "risk under a scenario", "how does", "how do", "what happens if",
)

_CATALOG_TITLES = {
    "stressor_variables": "Stressor variables in the dataset",
    "harmful_forces": "Harmful forces in the dataset",
    "fragile_conditions": "Fragile conditions in the ecological risk assessment",
    "anthropogenic_pressures": "Anthropogenic pressures in the dataset",
    "climate_drivers": "Climate-related variables in the dataset",
    "ecological_indicators": "Ecological indicators in the dataset",
    "ecosystem_functioning": "Variables related to ecosystem functioning",
    "ecological_dynamics": "Variables relevant to ecological dynamics",
}


def _catalog_intent_for_question(question: str):
    """Return a category intent only for a catalog/listing request."""
    intent = classify_data_query_intent(question)
    if not intent or intent == "dataset_inventory":
        return None

    q = " ".join((question or "").lower().split())
    if any(marker in q for marker in _CATALOG_RELATION_MARKERS):
        return None

    return intent


def handle_semantic_catalog_request(question: str, dataset, intent: str):
    """Select a catalog-defined category and attach baseline values when available."""
    if intent not in DATA_INTENT_TAGS or intent == "dataset_inventory":
        return {
            "summary": "Catalog request not resolved",
            "data": {},
            "drivers": [],
            "interpretation": "The requested catalog category is not supported.",
        }

    records = get_variables_for_intent(intent)
    try:
        baseline = compute_baseline(dataset) if dataset is not None else {}
    except Exception as exc:
        print("[DATA] Baseline unavailable for semantic catalog response:", exc)
        baseline = {}

    selected = []
    for record in records:
        feature = record["canonical_name"]
        item = {
            "variable": feature,
            "display_name": record["display_name"],
            "ecological_role": record["role"],
            "description": (
                record.get("application_csv_description")
                or record.get("description", "")
            ),
            "data_type": record.get("data_type"),
            "unit": (
                record.get("application_csv_unit")
                or record.get("unit")
            ),
            "mapping_status": record.get("mapping_status"),
        }

        # Preserve the current baseline-value behaviour: category answers list
        # the selected variables and include their baseline values where present.
        baseline_key = feature if feature in baseline else normalize_feature_name(feature)
        if baseline_key in baseline:
            try:
                item["baseline"] = round(float(baseline[baseline_key]), 2)
            except (TypeError, ValueError):
                item["baseline"] = baseline[baseline_key]

        selected.append(item)

    # Build a readable list for the text answer as well as retaining the
    # structured `data.variables` payload used by the orchestrator.
    listing_lines = ["", "Variables selected from the semantic catalog:"]
    for index, item in enumerate(selected, start=1):
        display_name = item.get("display_name") or item["variable"]
        canonical_name = item["variable"]
        baseline_value = item.get("baseline")
        unit = item.get("unit")
        role = item.get("ecological_role")

        line = f"{index}. {display_name} ({canonical_name})"
        if baseline_value is not None:
            value_text = f"baseline = {baseline_value}"
            if unit:
                value_text += f" {unit}"
            line += f" — {value_text}"
        else:
            line += " — baseline value unavailable"
        if role:
            line += f"; role: {role}"
        if item.get("data_type") == "categorical" and baseline_value is not None:
            line += " [categorical feature: do not interpret this baseline as a continuous measurement]"
        listing_lines.append(line)

    listing_text = "\n".join(listing_lines)

    if intent == "harmful_forces":
        interpretation = (
            f"The scientific catalog classifies {len(selected)} variables as harmful forces. "
            "Under the article's framework, these are potential negative drivers; this "
            "classification does not prove a causal effect in every grid cell. The list below "
            "includes baseline values where available. For categorical features, numeric baseline "
            "summaries may reflect category codes rather than a physical quantity."
            f"{listing_text}"
        )
    elif intent == "fragile_conditions":
        interpretation = (
            f"The scientific catalog classifies {len(selected)} variables as fragile conditions. "
            "They describe ecosystem states or conditions relevant to sensitivity and resilience; "
            "they should not be treated as harmful pressures in themselves. The list below includes "
            "baseline values where available. For categorical features, numeric baseline summaries "
            "may reflect category codes rather than a physical quantity."
            f"{listing_text}"
        )
    elif intent == "stressor_variables":
        interpretation = (
            f"Under the application's definition, environmental stressors are the {len(selected)} "
            "variables classified by the semantic catalog as harmful_force. Fragile-condition "
            "indicators are excluded from this list. This role classification identifies potential "
            "harmful drivers; it does not prove a causal effect in every grid cell. Baseline values "
            f"are included where available.{listing_text}"
        )
    else:
        category_explanations = {
            "anthropogenic_pressures": (
                "These variables are tagged as anthropogenic pressures in the semantic catalog. "
                "Some Atlas-to-CSV mappings remain provisional, so their encoding should be checked "
                "before interpreting individual values."
            ),
            "climate_drivers": (
                "These variables describe climate-related drivers or indicators. Their units, "
                "reference periods and sign conventions should be considered when interpreting values."
            ),
            "ecological_indicators": (
                "These variables describe ecosystem state or ecological conditions; they should "
                "not automatically be interpreted as external drivers or measured outcomes."
            ),
            "ecosystem_functioning": (
                "The catalog includes a productivity-related indicator, not a comprehensive "
                "measurement of every ecosystem function."
            ),
            "ecological_dynamics": (
                "These variables cover several aspects of ecological dynamics, including climate, "
                "land and habitat change, vegetation, productivity and biodiversity. Their inclusion "
                "does not by itself establish causal mechanisms."
            ),
        }
        explanation = category_explanations.get(
            intent,
            "The variables were selected using the semantic catalog's category tags."
        )
        interpretation = (
            f"The semantic catalog selected {len(selected)} variables for this category. "
            f"{explanation} Baseline values are included where available."
            f"{listing_text}"
        )

    print(f"[DATA] Semantic catalog request detected: {intent} ({len(selected)} variables)")
    return {
        "summary": _CATALOG_TITLES.get(intent, f"Catalog category: {intent}"),
        "data": {
            "catalog_intent": intent,
            "variable_count": len(selected),
            "variables": selected,
        },
        "drivers": [],
        "interpretation": interpretation,
    }


# ======================================================
# SYSTEM REQUEST DETECTION
# ======================================================

def is_system_request(question: str):

    q = question.lower()

    phrases = [
        "environmental conditions",
        "system conditions",
        "system status",
        "latest data",
        "all variables",
        "current state of the ecosystem",
        "state of the ecosystem",
        "current state of the ecosystem",
        "current ecosystem state",
        "state of the lake",
        "current state of the lake",
        "current condition of the lake",
        "ecosystem status",
        "overall ecosystem",
        "overall state",
    ]

    return any(phrase in q for phrase in phrases)


# ======================================================
# LIVE DATA OVERVIEW + RAG
# ======================================================

def handle_system_request(question: str):

    print("[DATA] System-wide request detected")
    print("[DATA] Loading current indicators from Live_update.csv")

    try:
        live_data = load_live_data()

    except Exception as exc:
        print("[DATA] Live data loading failed:", exc)

        return {
            "summary": "Current ecosystem state unavailable",
            "data": {},
            "drivers": [],
            "interpretation": (
                "The current ecosystem assessment cannot be generated "
                "because Live_update.csv could not be loaded. "
                "No environmental values have been inferred."
            ),
        }

    # Preserve the actual values and column names returned by the loader.
    indicators = live_data.to_dict()

    print("[DATA] Indicators loaded:", len(indicators))

    interpretation = generate_data_explanation(
        question=question,
        indicators=live_data,
    )

    return {
        "summary": "Current ecosystem state",
        "data": indicators,
        "drivers": [],
        "interpretation": interpretation,
    }



# ======================================================
# FOCUSED LIVE-DATA REQUESTS
# ======================================================

def _requested_live_feature(question: str, data_inputs=None):
    """Return a feature for a focused live-data question, if identifiable."""

    variables = (data_inputs or {}).get("variables", [])
    if len(variables) == 1:
        return variables[0]

    q = question.lower()
    keyword_map = [
        ("temperature", "Change in average temperature compared to a recent past"),
        ("precipitation", "Cumulative change in precipitation compared to a recent past"),
        ("rainfall", "Cumulative change in precipitation compared to a recent past"),
        ("evapotranspiration", "Relative change in the potential evapotranspiration compared to a recent past"),
        ("evaporation", "Relative change in the potential evapotranspiration compared to a recent past"),
        ("biodiversity", "Number of species potentially living in the cell"),
        ("species richness", "Number of species potentially living in the cell"),
        ("tree cover", "Density of tree cover"),
        ("grassland", "Presence of grassland"),
        ("productivity", "Index of total productivity by plant phenology"),
        ("imperviousness", "Density change in land imperviousness"),
    ]
    for keyword, feature in keyword_map:
        if keyword in q:
            return feature
    return None


def _live_indicator_matches(feature: str, live_data):
    """Select live-data fields matching one requested model feature."""

    feature_l = (feature or "").lower()
    names = list(live_data.index) if hasattr(live_data, "index") else list(live_data.keys())

    if "temperature" in feature_l:
        keywords = ("temperature",)
    elif "precipitation" in feature_l or "rain" in feature_l:
        keywords = ("rain", "precipitation")
    elif "evapotranspiration" in feature_l or "evaporation" in feature_l:
        keywords = ("evaporation", "evapotranspiration")
    elif "species" in feature_l or "biodiversity" in feature_l:
        keywords = ("species richness",)
    elif "tree cover density in the past decade" in feature_l or (
        "change in tree cover density" in feature_l
    ):
        keywords = ("change", "tree cover density")
    elif "tree cover" in feature_l:
        keywords = ("area covered by trees",)
    elif "grassland" in feature_l:
        keywords = ("grassland",)
    elif "productivity" in feature_l:
        keywords = ("vegetation growth", "productivity", "phenology")
    elif "impervious" in feature_l:
        keywords = ("imperviousness",)
    elif "land use and cover in the past decade" in feature_l:
        keywords = ("land use", "past decade")
    elif "land use and cover" in feature_l:
        keywords = ("land use", "cover")
    else:
        return {}

    matches = {}
    for name in names:
        label = str(name).strip().lower()
        if keywords == ("change", "tree cover density"):
            matched = all(token in label for token in keywords)
        else:
            matched = any(token in label for token in keywords)
        if matched:
            matches[name] = live_data[name]

    # Include the live-data reference year so "latest" is anchored to a date.
    for name in names:
        if "reference year" in str(name).lower() or "last year" in str(name).lower():
            matches[name] = live_data[name]
            break

    return matches


def handle_live_feature_request(question: str, feature: str):
    """Answer a focused 'latest data on X' request from live indicators."""

    print("[DATA] Focused live-data request:", feature)
    print("[DATA] Loading requested indicator from Live_update.csv")

    try:
        live_data = load_live_data()
    except Exception as exc:
        print("[DATA] Live data loading failed:", exc)
        return {
            "summary": "Requested live indicator unavailable",
            "data": {},
            "drivers": [],
            "interpretation": (
                "The requested current indicator cannot be retrieved because "
                "Live_update.csv could not be loaded. No value has been inferred."
            ),
        }

    selected = _live_indicator_matches(feature, live_data)
    selected_indicator_names = [
        name for name in selected
        if "reference year" not in str(name).lower()
        and "last year" not in str(name).lower()
    ]

    if not selected_indicator_names:
        return {
            "summary": "Requested live indicator unavailable",
            "data": {},
            "drivers": [],
            "interpretation": (
                f"No current live-data field could be matched to '{feature}'. "
                "No baseline value has been substituted for a current observation."
            ),
        }

    print("[DATA] Matched live indicators:", selected_indicator_names)

    interpretation = generate_data_explanation(
        question=question,
        indicators=selected,
    )

    return {
        "summary": f"Latest available {humanize_feature(feature).lower()}",
        "data": selected,
        "drivers": [],
        "interpretation": interpretation,
    }


# ======================================================
# MAIN
# ======================================================

def handle_data(question, dataset=None, data_inputs=None):

    print("\n========== DATA TASK START ==========")

    # Category requests are resolved from the semantic catalog before the
    # generic parser variables are treated as a single feature. The existing
    # inventory and single-feature/baseline paths are intentionally preserved.
    catalog_intent = (data_inputs or {}).get("catalog_intent")
    if not catalog_intent:
        catalog_intent = _catalog_intent_for_question(question)

    if catalog_intent and catalog_intent != "dataset_inventory":
        return handle_semantic_catalog_request(question, dataset, catalog_intent)

    # Preserve the established full-inventory behavior for Q1.
    if catalog_intent == "dataset_inventory" or is_dataset_catalog_request(question):
        return handle_dataset_catalog_request(question, dataset)

    # A request can contain "latest data" and still concern only one
    # indicator. Use the parser result to distinguish it from a true overview.
    if is_system_request(question):
        feature = _requested_live_feature(question, data_inputs)

        explicit_overview_phrases = (
            "all variables",
            "current state of the ecosystem",
            "state of the ecosystem",
            "current ecosystem state",
            "overall ecosystem",
            "overall state",
            "state of the lake",
            "current state of the lake",
            "current condition of the lake",
            "ecosystem status",
            "environmental conditions",
            "system conditions",
            "system status",
        )
        is_explicit_overview = any(
            phrase in question.lower() for phrase in explicit_overview_phrases
        )

        if feature and not is_explicit_overview:
            return handle_live_feature_request(question, feature)

        return handle_system_request(question)

    print("[DATA] Processing single-feature request")

    if dataset is None:
        return {
            "summary": "Data not available",
            "data": {},
            "drivers": [],
            "interpretation": "Dataset not loaded.",
        }

    baseline = compute_baseline(dataset)

    # --------------------------------------------------
    # EXTRACTION PATH
    # --------------------------------------------------

    if data_inputs is not None:

        variables = data_inputs.get("variables", [])
        feature = variables[0] if variables else None

        if feature:
            print("[DATA] Extracted feature:", feature)

    else:
        feature = extract_feature_from_question(
            question,
            baseline,
        )

    # --------------------------------------------------
    # SINGLE FEATURE
    # --------------------------------------------------

    if feature:

        if feature not in baseline:
            return {
                "summary": "Feature not available",
                "data": {},
                "drivers": [],
                "interpretation": (
                    f"The requested feature '{feature}' is not "
                    "available in the model baseline. No value "
                    "has been substituted."
                ),
            }

        baseline_value = baseline[feature]

        # This is a baseline value, not a current observation.
        human_feature = humanize_feature(feature)

        return {
            "summary": f"Baseline {human_feature.lower()}",
            "data": {
                "feature": human_feature,
                "baseline": round(float(baseline_value), 2),
            },
            "drivers": [],
            "interpretation": (
                f"The baseline value of {human_feature.lower()} "
                f"is {round(float(baseline_value), 2)}. "
                "A current value or temporal trend cannot be "
                "derived from this baseline alone."
            ),
        }

    # --------------------------------------------------
    # UNKNOWN REQUEST
    # --------------------------------------------------

    return {
        "summary": "Data query not resolved",
        "data": {},
        "drivers": [],
        "interpretation": (
            "The request could not be mapped to a supported "
            "environmental indicator. Please specify a variable "
            "or ask for the current state of the ecosystem."
        ),
    }