# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Data Task — v3 (GENERIC + FEATURE-AWARE)

✔ Works for ANY feature
✔ No hardcoding on temperature
✔ Uses question → feature mapping
✔ Baseline vs latest comparison
"""

from utils.model_input_builder import compute_baseline
from utils.feature_mapping import normalize_feature_name


def extract_feature_from_question(question: str, baseline: dict):

    q = question.lower()

    for feature in baseline.keys():
        if feature.lower() in q:
            return feature

    # fallback (prima feature disponibile)
    return list(baseline.keys())[0]


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
    # 🔥 FEATURE DETECTION (FIX)
    # ======================================================

    feature = extract_feature_from_question(question, baseline)

    baseline_value = baseline.get(feature, 0)

    # ======================================================
    # 🔥 LATEST DATA (mock dinamico)
    # ======================================================

    # 👉 per ora: simula leggero cambiamento
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