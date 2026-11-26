# -*- coding: utf-8 -*-
"""
Massaciuccoli Digital Twin
Data Task — v13 (DATA SNAPSHOT, ALL 12 FEATURES)

- Reports dataset baseline/current snapshot only.
- Includes all numeric and categorical features.
- Does NOT fabricate a "latest" value or a +2% trend.
- Categorical codes are interpreted using the dataset documentation.
"""

from numbers import Real

from utils.model_input_builder import compute_baseline
from utils.feature_mapping import normalize_feature_name


# ======================================================
# HUMAN LABELS
# ======================================================

FEATURE_LABELS = {
    "Density change in land imperviousness": "Land imperviousness change",
    "Density of tree cover": "Tree cover density",
    "Index of total productivity by plant phenology": "Ecosystem productivity index",
    "Change in average temperature compared to a recent past": "Average temperature change",
    "Relative change in the potential evapotranspiration compared to a recent past": "Evapotranspiration change",
    "Cumulative change in precipitation compared to a recent past": "Precipitation change",
    "Number of species potentially living in the cell": "Biodiversity (species richness)",
    "Change in tree cover density in the past decade": "Tree cover change (decade)",
    "Presence of grassland": "Grassland presence",
    "Change in grassland presence  in the past decade": "Grassland change (decade)",
    "Change in grassland presence in the past decade": "Grassland change (decade)",
    "Land use and cover": "Land use and cover",
    "Change in land use and cover in the past decade": "Land use change (decade)",
}


def humanize_feature(name: str):
    if not name:
        return ""

    # Exact mappings first, including the dataset's occasional double-space spelling.
    if name in FEATURE_LABELS:
        return FEATURE_LABELS[name]

    normalized = " ".join(str(name).split())
    if normalized in FEATURE_LABELS:
        return FEATURE_LABELS[normalized]

    name_lower = normalized.lower()

    if "temperature" in name_lower:
        return "Average temperature change"
    if "precipitation" in name_lower:
        return "Precipitation change"
    if "evapotranspiration" in name_lower:
        return "Evapotranspiration change"
    if "tree cover density in the past decade" in name_lower:
        return "Tree cover change (decade)"
    if "tree cover" in name_lower:
        return "Tree cover density"
    if "species" in name_lower:
        return "Biodiversity (species richness)"
    if "impervious" in name_lower:
        return "Land imperviousness change"
    if "productivity" in name_lower:
        return "Ecosystem productivity index"
    if "grassland" in name_lower and "change" in name_lower:
        return "Grassland change (decade)"
    if "grassland" in name_lower:
        return "Grassland presence"
    if "land use and cover in the past decade" in name_lower:
        return "Land use change (decade)"
    if "land use and cover" in name_lower:
        return "Land use and cover"

    return normalized


# ======================================================
# CATEGORICAL INTERPRETATION
# ======================================================

def _code(value):
    """Normalize categorical values to a comparable code, preserving NA-like values."""
    if value is None:
        return None
    text = str(value).strip()
    if text.lower() in {"na", "nan", "none", ""}:
        return None
    try:
        # Avoid treating values such as 1.0 differently from 1.
        numeric = float(text)
        if numeric.is_integer():
            return int(numeric)
    except (ValueError, TypeError):
        pass
    return text


def interpret_categorical_feature(feature: str, value):
    code = _code(value)
    normalized_feature = " ".join(str(feature).split()).lower()

    if code is None:
        return "No data (NA)."

    if normalized_feature == "presence of grassland":
        if code == 1:
            return "Grassland is present (code 1)."
        if code == 0:
            return "Grassland is absent (code 0)."
        return f"Unrecognized grassland-presence code ({code})."

    if "change in grassland presence" in normalized_feature:
        if code in (0, 10):
            return f"Grassland cover is unchanged (code {code})."
        if code in (1, 11):
            return f"Grassland cover has increased (code {code})."
        if code in (2, 22):
            return f"Grassland cover has decreased (code {code})."
        return f"Unrecognized grassland-change code ({code})."

    if "change in tree cover density" in normalized_feature:
        if code == 0:
            return "Unchanged condition, according to code 0."
        if code == 1:
            return "New tree cover (code 1)."
        if code == 2:
            return "Tree-cover loss (code 2)."
        if code == 10:
            return "Unchanged area with tree cover (code 10)."
        return f"Unrecognized tree-cover-change code ({code})."

    if normalized_feature == "land use and cover":
        if code == 1120:
            return "Corine code 1120: industrial, commercial and military units."
        if code == 1310:
            return "Corine code 1310: mineral extraction, dump and construction sites."
        if code == 8120:
            return "Corine code 8120: highly modified water courses and canals."
        return (
            f"Land-use/cover code {code}. The dataset description classifies "
            "other codes as rural or naturalistic areas."
        )

    if "change in land use and cover" in normalized_feature:
        if code == 1:
            return "Territory modelled as artificial (code 1)."
        if code == 2:
            return "Area used for agriculture (code 2)."
        if code == 0:
            return "Code 0: no change or another land-use type, as specified by the dataset."
        return (
            f"Land-use-change code {code}. The dataset description identifies "
            "NA and 0 as no change or other land-use types."
        )

    return f"Categorical value: {code}."


# ======================================================
# FEATURE EXTRACTION
# ======================================================

def extract_feature_from_question(question: str, baseline: dict):
    q = question.lower()
    mapped = normalize_feature_name(q)

    if mapped and mapped in baseline:
        return mapped

    KEYWORD_MAP = {
        "temperature": "Change in average temperature compared to a recent past",
        "precipitation": "Cumulative change in precipitation compared to a recent past",
        "biodiversity": "Number of species potentially living in the cell",
        "tree cover": "Density of tree cover",
        "grassland": "Presence of grassland",
        "evapotranspiration": "Relative change in the potential evapotranspiration compared to a recent past",
        "productivity": "Index of total productivity by plant phenology",
        "imperviousness": "Density change in land imperviousness",
        "land use change": "Change in land use and cover in the past decade",
        "land use and cover": "Land use and cover",
    }

    # Prioritize the more specific "land use change" phrase.
    if "land use change" in q or "change in land use" in q:
        specific = "Change in land use and cover in the past decade"
        if specific in baseline:
            return specific

    for keyword, feature_name in KEYWORD_MAP.items():
        if keyword in q and feature_name in baseline:
            return feature_name

    return None


# ======================================================
# SYSTEM REQUEST DETECTION
# ======================================================

def is_system_request(question: str):
    q = question.lower()
    return any([
        "environmental conditions" in q,
        "system conditions" in q,
        "system status" in q,
        "latest data" in q,
        "all variables" in q,
        "variables available" in q,
        "variables represented" in q,
        "dataset" in q,
    ])

CATEGORICAL_FEATURES = {
    "Change in tree cover density in the past decade",
    "Presence of grassland",
    "Change in grassland presence  in the past decade",
    "Land use and cover",
    "Change in land use and cover in the past decade",
}

# ======================================================
# SNAPSHOT BUILDING
# ======================================================

def _is_numeric(value):
    return isinstance(value, Real) and not isinstance(value, bool)


def build_system_narrative(baseline):
    data = {}
    numeric_lines = []
    categorical_lines = []

    PRIORITY = [
        "Average temperature change",
        "Precipitation change",
        "Evapotranspiration change",
        "Biodiversity (species richness)",
        "Tree cover density",
        "Tree cover change (decade)",
        "Ecosystem productivity index",
        "Grassland presence",
        "Grassland change (decade)",
        "Land use and cover",
        "Land use change (decade)",
        "Land imperviousness change",
    ]

    for feature, value in baseline.items():
        label = humanize_feature(feature)

        if feature not in CATEGORICAL_FEATURES and _is_numeric(value):
            numeric_value = round(float(value), 2)
            data[label] = {"value": numeric_value}
            numeric_lines.append(
                (label, f"{label}: dataset snapshot value = {numeric_value}.")
            )
        else:
            raw_value = str(value).strip()
            description = interpret_categorical_feature(feature, value)
            data[label] = {
                "value": raw_value,
                "interpretation": description,
            }
            categorical_lines.append(
                (label, f"{label}: code/value = {raw_value}; {description}")
            )

    def sort_key(item):
        name = item[0]
        return PRIORITY.index(name) if name in PRIORITY else 999

    numeric_lines.sort(key=sort_key)
    categorical_lines.sort(key=sort_key)

    interpretation_parts = []

    if numeric_lines:
        interpretation_parts.append(
            "Numeric variables are reported as dataset snapshot values; "
            "no synthetic latest values or trends are calculated."
        )
        interpretation_parts.extend(line for _, line in numeric_lines)

    if categorical_lines:
        interpretation_parts.append(
            "Categorical variables are reported using their dataset codes "
            "and documented interpretations."
        )
        interpretation_parts.extend(line for _, line in categorical_lines)

    interpretation = "\n- " + "\n- ".join(interpretation_parts)

    return data, interpretation


# ======================================================
# MAIN
# ======================================================

def handle_data(question, dataset=None):
    print("\n========== DATA TASK START ==========")
    print("[DATA] Loading dataset snapshot...")

    if dataset is None:
        return {
            "summary": "Data not available",
            "data": {},
            "drivers": [],
            "interpretation": "Dataset not loaded.",
        }

    baseline = compute_baseline(dataset)
    feature = extract_feature_from_question(question, baseline)

    # Full snapshot / dataset request
    if is_system_request(question):
        print("[INFO] Explicit dataset/snapshot request detected")
        data, interpretation = build_system_narrative(baseline)
        return {
            "summary": "Dataset environmental variables snapshot",
            "data": data,
            "drivers": [],
            "interpretation": interpretation,
        }

    # Single feature request
    if feature:
        value = baseline.get(feature)
        label = humanize_feature(feature)

        if feature not in CATEGORICAL_FEATURES and _is_numeric(value):
            numeric_value = round(float(value), 2)
            return {
                "summary": f"Dataset snapshot: {label}",
                "data": {
                    "feature": label,
                    "value": numeric_value,
                },
                "drivers": [],
                "interpretation": (
                    f"The dataset snapshot value for {label} is "
                    f"{numeric_value}. No latest value or trend is inferred."
                ),
            }

        categorical_value = str(value).strip()
        description = interpret_categorical_feature(feature, value)
        return {
            "summary": f"Dataset snapshot: {label}",
            "data": {
                "feature": label,
                "value": categorical_value,
                "interpretation": description,
            },
            "drivers": [],
            "interpretation": (
                f"The dataset snapshot records {label} with code/value "
                f"{categorical_value}. {description}"
            ),
        }

    # Fallback: full snapshot
    print("[INFO] Fallback -> returning full dataset snapshot")
    data, interpretation = build_system_narrative(baseline)
    return {
        "summary": "Dataset environmental variables snapshot",
        "data": data,
        "drivers": [],
        "interpretation": interpretation,
    }
