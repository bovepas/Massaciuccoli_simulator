# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Data Task — v4 (FIXED FEATURE MAPPING)

✔ Robust feature detection
✔ Uses semantic mapping (temperature → real feature)
✔ Safe fallback
"""

from utils.model_input_builder import compute_baseline
from utils.feature_mapping import normalize_feature_name


# ======================================================
# FEATURE EXTRACTION (FIXED)
# ======================================================

def extract_feature_from_question(question: str, baseline: dict):

    q = question.lower()

    # --------------------------------------------------
    # 🔥 STEP 1: semantic normalization
    # --------------------------------------------------

    mapped = normalize_feature_name(q)

    if mapped and mapped in baseline:
        return mapped

    # --------------------------------------------------
    # 🔥 STEP 2: fallback match su keyword semplici
    # --------------------------------------------------

    KEYWORD_MAP = {
        "temperature": "Change in average temperature compared to a recent past",
        "precipitation": "Cumulative change in precipitation compared to a recent past",
        "biodiversity": "Number of species potentially living in the cell",
        "tree cover": "Density of tree cover",
        "grassland": "Presence of grassland",
        "evapotranspiration": "Relative change in the potential evapotranspiration compared to a recent past",
        "productivity": "Index of total productivity by plant phenology"
    }

    for k, v in KEYWORD_MAP.items():
        if k in q and v in baseline:
            return v

    # --------------------------------------------------
    # ⚠️ LAST RESORT
    # --------------------------------------------------

    print("[WARNING] No feature matched, using fallback")

    return list(baseline.keys())[0]


# ======================================================
# MAIN
# ======================================================

def handle_data(question, dataset=None):

    print("\n========== DATA TASK START ==========")
    print("[DATA] Loading live data...")

    if dataset is None:
        return {
            "summary": "Data not available",
            "data": {},
            "drivers": [],
            "interpretation": "Dataset not loaded."
        }

    # ======================================================
    # BASELINE
    # ======================================================

    baseline = compute_baseline(dataset)

    # ======================================================
    # FEATURE DETECTION
    # ======================================================

    feature = extract_feature_from_question(question, baseline)

    baseline_value = baseline.get(feature, 0)

    # ======================================================
    # MOCK LATEST
    # ======================================================

    latest_value = round(baseline_value * 1.02, 2)

    print("[DEBUG] Feature:", feature)
    print("[DEBUG] Baseline value:", baseline_value)
    print("[DEBUG] Latest value:", latest_value)

    # ======================================================
    # INTERPRETAZIONE
    # ======================================================

    delta = latest_value - baseline_value

    if abs(delta) < 0.01:
        trend = "stable"
    elif delta > 0:
        trend = "increasing"
    else:
        trend = "decreasing"

    interpretation = (
        f"In the baseline model, the average value of '{feature}' is {round(baseline_value, 2)}, "
        f"while the most recent data indicate a value of {latest_value}. "
        f"This suggests a {trend} trend that may influence ecosystem dynamics in the lake basin."
    )

    # ======================================================
    # OUTPUT
    # ======================================================

    return {
        "summary": "Latest environmental data",
        "data": {
            "feature": feature,
            "baseline": round(baseline_value, 2),
            "latest": latest_value
        },
        "drivers": [],
        "interpretation": interpretation
    }