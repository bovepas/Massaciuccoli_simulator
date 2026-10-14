# -\*- coding: utf-8 -\*-

"""

Drivers Task — v6 (clean + demo-ready + semantic fix)

✔ Removes noisy variables

✔ Filters weak correlations

✔ Improves output readability

✔ Adds scientific disclaimer

✔ 🔥 Aligns wording with "loss / increase"

"""

import pandas as pd

import os

from utils.feature_mapping import normalize_feature_name

from utils.drivers_parser import parse_drivers_target, parse_drivers_goal

from knowledge.rag_drivers import generate_drivers_explanation

DATA_PATH = "/app/data/massaciuccoli_data.csv"

EXCLUDED_FEATURES = [

    "Latitude",

    "Longitude"

]

MIN_CORRELATION = 0.1  # 🔥 threshold

# Local aliases for this task only. Keep the shared feature mapping unchanged.

DRIVERS_TARGET_ALIASES = {

    "ecosystem risk": (

        "Ecosystem risk classification according to a Variational Autoencoder "

        "with a later application of a Multi K-means process"

    ),

    "ecosystem_risk": (

        "Ecosystem risk classification according to a Variational Autoencoder "

        "with a later application of a Multi K-means process"

    ),

    "ecological risk": (

        "Ecosystem risk classification according to a Variational Autoencoder "

        "with a later application of a Multi K-means process"

    ),

}

# Q3: climate-related stress is not a measured dataset column. Analyze the

# three available climate indicators separately; do not combine them into an

# invented composite index.

CLIMATE_STRESS_TARGETS = {

    "climate-related stress",

    "climate related stress",

    "climate stress",

}

CLIMATE_INDICATORS = [

    "Change in average temperature compared to a recent past",

    "Cumulative change in precipitation compared to a recent past",

    "Relative change in the potential evapotranspiration compared to a recent past",

]

CLIMATE_INDICATOR_LABELS = {

    "Change in average temperature compared to a recent past": "temperature change",

    "Cumulative change in precipitation compared to a recent past": "precipitation change",

    "Relative change in the potential evapotranspiration compared to a recent past": "potential evapotranspiration change",

}

# Coded land-use classes are categorical; Pearson correlation would treat their

# numeric codes as quantities, so exclude them from this special analysis.

CLIMATE_ANALYSIS_EXCLUDED = {

    "Land use and cover",

    "Change in land use and cover in the past decade",

    "Latitude",

    "Longitude",

}

# Q8: hydrological change is not directly measured as a single variable. Analyze
# precipitation and potential evapotranspiration separately; do not create an index.
HYDROLOGICAL_CHANGE_TARGETS = {
    "hydrological change",
    "hydrologic change",
    "hydrological changes",
    "hydrologic changes",
    "hydrological dynamics",
}
HYDROLOGICAL_INDICATORS = [
    "Cumulative change in precipitation compared to a recent past",
    "Relative change in the potential evapotranspiration compared to a recent past",
]
HYDROLOGICAL_INDICATOR_LABELS = {
    "Cumulative change in precipitation compared to a recent past": "precipitation change",
    "Relative change in the potential evapotranspiration compared to a recent past": "potential evapotranspiration change",
}
HYDROLOGICAL_ANALYSIS_EXCLUDED = {
    "Land use and cover",
    "Change in land use and cover in the past decade",
    "Latitude",
    "Longitude",
}

# Q7: resilience is not directly measured. Analyze available indicators separately.
RESILIENCE_TARGETS = {
    "ecosystem resilience",
    "ecosystem resiliency",
    "resilience of the ecosystem",
}
RESILIENCE_INDICATORS = [
    "Density of tree cover",
    "Change in tree cover density in the past decade",
    "Index of total productivity by plant phenology",
    "Number of species potentially living in the cell",
]
RESILIENCE_ANALYSIS_EXCLUDED = {
    "Land use and cover",
    "Change in land use and cover in the past decade",
    "Latitude",
    "Longitude",
}


# Q10: vulnerability is not directly measured. Analyze environmental pressure/sensitivity
# indicators separately; these are proxies, not a validated vulnerability score.
VULNERABILITY_TARGETS = {
    "ecosystem vulnerability",
    "ecological vulnerability",
    "vulnerability of the ecosystem",
    "vulnerability",
}
VULNERABILITY_INDICATORS = [
    "Density change in land imperviousness",
    "Change in tree cover density in the past decade",
    "Change in grassland presence in the past decade",
    "Change in average temperature compared to a recent past",
    "Cumulative change in precipitation compared to a recent past",
    "Relative change in the potential evapotranspiration compared to a recent past",
    "Change in land use and cover in the past decade",
    "Number of species potentially living in the cell",
]
VULNERABILITY_ANALYSIS_EXCLUDED = {
    "Land use and cover",
    "Latitude",
    "Longitude",
}

def resolve_drivers_target(target, columns):

    """Resolve Drivers targets against real dataset columns without changing global mappings."""

    if not target:

        return None

    cleaned = str(target).strip()

    # Exact match first.

    if cleaned in columns:

        return cleaned

    # Case-insensitive exact match for canonical column names.

    columns_by_lower = {str(column).strip().lower(): column for column in columns}

    if cleaned.lower() in columns_by_lower:

        return columns_by_lower[cleaned.lower()]

    # Drivers-specific aliases for concepts with a concrete target column.

    alias = DRIVERS_TARGET_ALIASES.get(cleaned.lower())

    if alias:

        if alias in columns:

            return alias

        return columns_by_lower.get(alias.lower())

    return cleaned

def load_data():

    if not os.path.exists(DATA_PATH):

        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # skip description row

    df = df.iloc[1:]

    return df

def classify_strength(corr):

    abs_corr = abs(corr)

    if abs_corr < 0.1:

        return "weak"

    elif abs_corr < 0.3:

        return "moderate"

    else:

        return "strong"

# ======================================================

# 🔥 UPDATED DRIVER FORMAT (SEMANTIC FIX)

# ======================================================

def format_driver(d, target, direction):

    feature = d["feature"]

    strength = d["strength"]

    correlation_direction = d["direction"]

    # Caso biodiversità → linguaggio naturale

    if "species" in target.lower() and direction == "decrease":

        return f"{feature} (associated with biodiversity decline, {strength})"

    if "species" in target.lower() and direction == "increase":

        return f"{feature} (associated with biodiversity increase, {strength})"

    # Fallback generico

    return f"{feature} ({correlation_direction}, {strength} influence)"

def analyze_climate_stress(df):

    """Analyze climate stress components separately, without a composite score."""

    available = [column for column in CLIMATE_INDICATORS if column in df.columns]

    if len(available) < 2:

        return {

            "summary": "Climate-related stress indicators not computable",

            "data": {"target": "climate-related stress", "drivers": []},

            "drivers": [],

            "interpretation": (

                "The dataset does not contain enough of the required climate indicators "

                "to analyze climate-related stress. No composite index was created."

            ),

        }

    rows = []

    driver_labels = []

    lines = []

    for target_column in available:

        y = pd.to_numeric(df[target_column], errors="coerce")

        component_results = []

        for column in df.columns:

            if column == target_column or column in available or column in CLIMATE_ANALYSIS_EXCLUDED:

                continue

            x = pd.to_numeric(df[column], errors="coerce")

            corr = x.corr(y)

            if pd.notna(corr) and abs(float(corr)) >= MIN_CORRELATION:

                component_results.append({

                    "feature": column,

                    "correlation": float(corr),

                    "abs_corr": abs(float(corr)),

                    "direction": "positive" if corr > 0 else "negative",

                    "strength": classify_strength(float(corr)),

                    "climate_indicator": target_column,

                })

        component_results.sort(key=lambda item: item["abs_corr"], reverse=True)

        top = component_results[:2]

        label = CLIMATE_INDICATOR_LABELS.get(target_column, target_column)

        if not top:

            lines.append(f"- {label}: no associations met the correlation threshold (|r| >= {MIN_CORRELATION:.1f}).")

            continue

        for item in top:

            rows.append(item)

            driver_labels.append(

                f"{label} — {item['feature']} ({item['direction']} association, "

                f"{item['strength']}, r={item['correlation']:.2f})"

            )

        component_text = "; ".join(

            f"{item['feature']} ({item['direction']}, r={item['correlation']:.2f})"

            for item in top

        )

        lines.append(f"- {label}: strongest observed associations are {component_text}.")

    interpretation = (

        "Climate-related stress is not a directly measured column in this dataset. "

        "The analysis therefore examines temperature, precipitation and potential "

        "evapotranspiration separately, reporting the strongest correlations with "

        "other available numeric environmental indicators. These are associations, "

        "not evidence of causation, and no composite climate-stress index was calculated.\n\n"

        + "\n".join(lines)

    )

    return {

        "summary": "Drivers associated with climate-related stress indicators",

        "data": {"target": "climate-related stress", "drivers": rows},

        "drivers": driver_labels,

        "interpretation": interpretation,

    }


def analyze_hydrological_change(df):
    """Analyze precipitation and potential evapotranspiration separately."""
    available = [column for column in HYDROLOGICAL_INDICATORS if column in df.columns]
    if len(available) < 2:
        return {
            "summary": "Hydrological change indicators not fully computable",
            "data": {"target": "hydrological change", "indicators": available, "drivers": []},
            "drivers": [],
            "interpretation": (
                "Hydrological change is not directly measured as a single variable in this dataset. "
                "The analysis requires both precipitation-change and potential-evapotranspiration "
                "indicators; no composite hydrological index was created."
            ),
        }

    rows = []
    driver_labels = []
    lines = []
    for indicator in available:
        y = pd.to_numeric(df[indicator], errors="coerce")
        associations = []
        for column in df.columns:
            if column == indicator or column in available or column in HYDROLOGICAL_ANALYSIS_EXCLUDED:
                continue
            x = pd.to_numeric(df[column], errors="coerce")
            corr = x.corr(y)
            if pd.notna(corr) and abs(float(corr)) >= MIN_CORRELATION:
                associations.append({
                    "feature": column,
                    "correlation": float(corr),
                    "abs_corr": abs(float(corr)),
                    "direction": "positive" if corr > 0 else "negative",
                    "strength": classify_strength(float(corr)),
                    "hydrological_indicator": indicator,
                })
        associations.sort(key=lambda item: item["abs_corr"], reverse=True)
        top = associations[:2]
        label = HYDROLOGICAL_INDICATOR_LABELS.get(indicator, indicator)
        if not top:
            lines.append(
                f"- {label}: no associations met the correlation threshold "
                f"(|r| >= {MIN_CORRELATION:.1f})."
            )
            continue
        for item in top:
            rows.append(item)
            driver_labels.append(
                f"{label} — {item['feature']} ({item['direction']} association, "
                f"{item['strength']}, r={item['correlation']:.2f})"
            )
        items_text = "; ".join(
            f"{item['feature']} ({item['direction']}, r={item['correlation']:.2f})"
            for item in top
        )
        lines.append(f"- {label}: strongest observed associations are {items_text}.")

    interpretation = (
        "Hydrological change is not directly measured as a single variable in this dataset. "
        "The analysis examines cumulative precipitation change and relative potential "
        "evapotranspiration change separately, reporting their strongest correlations with "
        "other available numeric environmental indicators. These associations do not establish "
        "causation. No composite hydrological index was calculated.\n\n"
        + "\n".join(lines)
    )
    return {
        "summary": "Drivers associated with hydrological change indicators",
        "data": {"target": "hydrological change", "indicators": available, "drivers": rows},
        "drivers": driver_labels,
        "interpretation": interpretation,
    }


def analyze_ecosystem_resilience(df):
    """Analyze resilience-related indicators separately; do not invent a resilience score."""
    available = [column for column in RESILIENCE_INDICATORS if column in df.columns]
    if not available:
        return {
            "summary": "Ecosystem resilience proxies not computable",
            "data": {"target": "ecosystem resilience", "indicators": []},
            "drivers": [],
            "interpretation": (
                "Ecosystem resilience is not directly measured in this dataset, and none "
                "of the selected proxy indicators is available. No resilience score was created."
            ),
        }

    rows = []
    driver_labels = []
    lines = []
    for indicator in available:
        y = pd.to_numeric(df[indicator], errors="coerce")
        associations = []
        for column in df.columns:
            if column == indicator or column in available or column in RESILIENCE_ANALYSIS_EXCLUDED:
                continue
            x = pd.to_numeric(df[column], errors="coerce")
            corr = x.corr(y)
            if pd.notna(corr) and abs(float(corr)) >= MIN_CORRELATION:
                associations.append({
                    "feature": column,
                    "correlation": float(corr),
                    "abs_corr": abs(float(corr)),
                    "direction": "positive" if corr > 0 else "negative",
                    "strength": classify_strength(float(corr)),
                    "resilience_indicator": indicator,
                })

        associations.sort(key=lambda item: item["abs_corr"], reverse=True)
        top = associations[:2]
        if not top:
            lines.append(
                f"- {indicator}: no associations met the correlation threshold "
                f"(|r| >= {MIN_CORRELATION:.1f})."
            )
            continue

        summary_items = []
        for item in top:
            rows.append(item)
            driver_labels.append(
                f"{indicator} — {item['feature']} ({item['direction']} association, "
                f"{item['strength']}, r={item['correlation']:.2f})"
            )
            summary_items.append(
                f"{item['feature']} ({item['direction']}, r={item['correlation']:.2f})"
            )
        lines.append(
            f"- {indicator}: strongest observed associations are "
            + "; ".join(summary_items) + "."
        )

    interpretation = (
        "Ecosystem resilience is not a directly measured variable in this dataset. "
        "This analysis therefore examines tree-cover density, change in tree-cover "
        "density, plant-phenology productivity and potential species richness as "
        "separate indicators that may be relevant to resilience; they are proxies, "
        "not a validated resilience measure. Associations are correlations, not "
        "evidence of causation. No composite index or resilience score was calculated.\n\n"
        + "\n".join(lines)
    )
    return {
        "summary": "Associations with ecosystem resilience proxy indicators",
        "data": {"target": "ecosystem resilience", "indicators": available, "drivers": rows},
        "drivers": driver_labels,
        "interpretation": interpretation,
    }



def analyze_ecosystem_vulnerability(df):
    """Analyze candidate vulnerability proxies separately, without a vulnerability score."""
    available = [column for column in VULNERABILITY_INDICATORS if column in df.columns]
    if not available:
        return {
            "summary": "Ecosystem vulnerability proxies not computable",
            "data": {"target": "ecosystem vulnerability", "indicators": [], "drivers": []},
            "drivers": [],
            "interpretation": (
                "Ecosystem vulnerability is not directly measured in this dataset, and none "
                "of the selected environmental proxy indicators is available. No vulnerability "
                "score was created."
            ),
        }

    rows = []
    driver_labels = []
    lines = []
    for indicator in available:
        y = pd.to_numeric(df[indicator], errors="coerce")
        associations = []
        for column in df.columns:
            if column == indicator or column in available or column in VULNERABILITY_ANALYSIS_EXCLUDED:
                continue
            x = pd.to_numeric(df[column], errors="coerce")
            corr = x.corr(y)
            if pd.notna(corr) and abs(float(corr)) >= MIN_CORRELATION:
                associations.append({
                    "feature": column,
                    "correlation": float(corr),
                    "abs_corr": abs(float(corr)),
                    "direction": "positive" if corr > 0 else "negative",
                    "strength": classify_strength(float(corr)),
                    "vulnerability_indicator": indicator,
                })
        associations.sort(key=lambda item: item["abs_corr"], reverse=True)
        top = associations[:2]
        if not top:
            lines.append(
                f"- {indicator}: no associations met the correlation threshold "
                f"(|r| >= {MIN_CORRELATION:.1f})."
            )
            continue
        for item in top:
            rows.append(item)
            driver_labels.append(
                f"{indicator} — {item['feature']} ({item['direction']} association, "
                f"{item['strength']}, r={item['correlation']:.2f})"
            )
        items_text = "; ".join(
            f"{item['feature']} ({item['direction']}, r={item['correlation']:.2f})"
            for item in top
        )
        lines.append(f"- {indicator}: strongest observed associations are {items_text}.")

    interpretation = (
        "Ecosystem vulnerability is not directly measured as a single variable in this dataset. "
        "This analysis examines available environmental pressure and sensitivity indicators "
        "separately as candidate proxies; they are not a validated vulnerability measure and "
        "their correlations do not establish causation. The analysis does not equate vulnerability "
        "with ecosystem risk and does not calculate a composite vulnerability score.\n\n"
        + "\n".join(lines)
    )
    return {
        "summary": "Associations with ecosystem vulnerability proxy indicators",
        "data": {"target": "ecosystem vulnerability", "indicators": available, "drivers": rows},
        "drivers": driver_labels,
        "interpretation": interpretation,
    }

def handle_drivers(question: str, drivers_inputs=None):

    print("\n========== DRIVERS TASK START ==========")

    df = load_data()

    if drivers_inputs is not None:

        target = drivers_inputs.get("target")

        direction = drivers_inputs.get("direction")

    else:

        target_raw = parse_drivers_target(question)

        target = normalize_feature_name(target_raw) if target_raw else None

        direction = parse_drivers_goal(question)

    target = resolve_drivers_target(target, df.columns)

    print("[DEBUG] Target:", target)

    normalized_target = str(target).strip().lower().replace("_", " ") if target is not None else ""

    if normalized_target in CLIMATE_STRESS_TARGETS:

        result = analyze_climate_stress(df)

        print("========== DRIVERS TASK END (CLIMATE STRESS) ==========\n")

        return result

    if normalized_target in HYDROLOGICAL_CHANGE_TARGETS:
        result = analyze_hydrological_change(df)
        print("========== DRIVERS TASK END (HYDROLOGICAL CHANGE INDICATORS) ==========\n")
        return result

    if normalized_target in RESILIENCE_TARGETS:
        result = analyze_ecosystem_resilience(df)
        print("========== DRIVERS TASK END (ECOSYSTEM RESILIENCE PROXIES) ==========\\n")
        return result

    if normalized_target in VULNERABILITY_TARGETS:
        result = analyze_ecosystem_vulnerability(df)
        print("========== DRIVERS TASK END (ECOSYSTEM VULNERABILITY PROXIES) ==========\n")
        return result

    if target is None or target not in df.columns:

        return {

            "summary": "Drivers not computable",

            "data": {},

            "drivers": [],

            "interpretation": "Target variable not found in dataset."

        }

    print("[DEBUG] Direction:", direction)

    results = []

    for col in df.columns:

        if col == target or col in EXCLUDED_FEATURES:

            continue

        try:

            x = pd.to_numeric(df[col], errors="coerce")

            y = pd.to_numeric(df[target], errors="coerce")

            corr = x.corr(y)

            if pd.notna(corr) and abs(corr) >= MIN_CORRELATION:

                results.append({

                    "feature": col,

                    "correlation": float(corr),

                    "abs_corr": abs(float(corr)),

                    "direction": "positive" if corr > 0 else "negative",

                    "strength": classify_strength(corr)

                })

        except Exception:

            continue

    # 🔥 GOAL FILTER

    # 🔥 DIRECTION

    # La direction descrive la richiesta dell'utente,

    # non il segno della correlazione.

    # Le correlazioni vengono mantenute entrambe.

    # 🔥 SORT

    results = sorted(results, key=lambda x: x["abs_corr"], reverse=True)

    top = results[:5]

    print("[DEBUG] Top drivers:", [d["feature"] for d in top])

    # 🔥 UPDATED DRIVER OUTPUT

    drivers = [format_driver(d, target, direction) for d in top]

    # 🔥 SUMMARY

    # 🔥 SUMMARY

    if direction == "decrease" and "species" in target.lower():

        summary = "Drivers of biodiversity degradation"

    elif direction == "increase" and "species" in target.lower():

        summary = "Drivers of biodiversity increase"

    else:

        summary = f"Drivers of {target}"

    data = {

        "target": target,

        "drivers": top

    }

    # ======================================================

    # SEMANTIC FEATURES

    # ======================================================

    semantic_features = [

        target

    ] + [

        d["feature"]

        for d in top

    ]

    print(

        "[DEBUG] semantic_features:"

    )

    print(

        semantic_features

    )

    # 🔥 RAG

    explanation = generate_drivers_explanation(

        target,

        top,

        features=semantic_features

    )

    # ======================================================

    # 🔥 POST-PROCESS FIX (GRAMMAR SAFE)

    # ======================================================

    if "species" in target.lower():

        explanation = explanation.replace(

            "shows a negative relationship with",

            "is negatively affected by"

        )

        explanation = explanation.replace(

            "exhibits negative associations with",

            "is further negatively influenced by"

        )

        explanation = explanation.replace(

            "linked to a decrease in the potential for species to live in the cell",

            "acting as drivers of biodiversity loss in the system"

        )

    # 🔥 DISCLAIMER

    explanation += (

        "\n\nThese associations highlight environmental pressures "

        "observed in the lake ecosystem and may reflect interacting "

        "ecological processes."

    )

    print("========== DRIVERS TASK END ==========\n")

    return {

        "summary": summary,

        "data": data,

        "drivers": drivers,

        "interpretation": explanation

    }
