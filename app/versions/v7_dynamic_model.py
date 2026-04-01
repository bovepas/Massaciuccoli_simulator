"""
Massaciuccoli Digital Twin
v9 — Climate + Maps + Hotspots
"""

import pandas as pd
import numpy as np

from versions.v6_1_main import MODEL, NUM_FEATURES, CAT_FEATURES
from versions.v6_2_basin_engine import load_dataset, compute_basin_statistics
from tools.climate_loader import load_asc, extract_values_for_dataframe
from tools.spatial_analysis import (
    plot_risk_map,
    plot_delta_map,
    detect_hotspots
)


# ======================================================
# SCENARIO CONFIG
# ======================================================

SCENARIOS = {
    ("rcp45", "2050"): {
        "temp": "data/climate/rcp45/2050/Temperature.asc",
        "prec": "data/climate/rcp45/2050/Precipitation.asc"
    },
    ("rcp85", "2100"): {
        "temp": "data/climate/rcp85/2100/Temperature.asc",
        "prec": "data/climate/rcp85/2100/Precipitation.asc"
    }
}

BASELINE = {
    "temp": "data/climate/baseline/Temperature.asc",
    "prec": "data/climate/baseline/Precipitation.asc"
}


# ======================================================
# LOAD CLIMATE
# ======================================================

def load_climate_layers(rcp, year):

    scenario = SCENARIOS[(rcp, year)]

    temp_base, h1 = load_asc(BASELINE["temp"])
    temp_fut, h2 = load_asc(scenario["temp"])

    prec_base, h3 = load_asc(BASELINE["prec"])
    prec_fut, h4 = load_asc(scenario["prec"])

    return {
        "temp_base": (temp_base, h1),
        "temp_fut": (temp_fut, h2),
        "prec_base": (prec_base, h3),
        "prec_fut": (prec_fut, h4),
    }


# ======================================================
# DELTA
# ======================================================

def compute_climate_delta(df, layers):

    temp_base, h1 = layers["temp_base"]
    temp_fut, h2 = layers["temp_fut"]

    prec_base, h3 = layers["prec_base"]
    prec_fut, h4 = layers["prec_fut"]

    temp_base_vals = extract_values_for_dataframe(df, temp_base, h1)
    temp_fut_vals = extract_values_for_dataframe(df, temp_fut, h2)

    prec_base_vals = extract_values_for_dataframe(df, prec_base, h3)
    prec_fut_vals = extract_values_for_dataframe(df, prec_fut, h4)

    delta_temp = temp_fut_vals - temp_base_vals
    delta_prec = prec_fut_vals - prec_base_vals

    return delta_temp, delta_prec


# ======================================================
# APPLY DELTA
# ======================================================

def apply_delta(df, delta_temp, delta_prec):

    df = df.copy()

    df["Change in average temperature compared to a recent past"] += delta_temp
    df["Cumulative change in precipitation compared to a recent past"] += delta_prec

    return df


# ======================================================
# PREDICT
# ======================================================

def predict(df):

    X = df[NUM_FEATURES + CAT_FEATURES]

    df_out = df.copy()
    df_out["risk_score"] = MODEL.predict(X)

    return df_out


# ======================================================
# MAIN
# ======================================================

def run_temporal_simulation(rcp="rcp45", year="2050"):

    print(f"🌍 Scenario: {rcp.upper()} — {year}")

    df = load_dataset()

    layers = load_climate_layers(rcp, year)
    delta_temp, delta_prec = compute_climate_delta(df, layers)

    # baseline
    df_base = predict(df)
    base_stats = compute_basin_statistics(df_base)

    # future
    df_future_input = apply_delta(df, delta_temp, delta_prec)
    df_future = predict(df_future_input)
    future_stats = compute_basin_statistics(df_future)

    # ======================================================
    # MAPS
    # ======================================================

    print("🗺️ Generating maps...")
    plot_risk_map(df_base, "Baseline Risk")
    plot_risk_map(df_future, "Future Risk")
    plot_delta_map(df_base, df_future)

    # ======================================================
    # HOTSPOTS
    # ======================================================

    hotspots = detect_hotspots(df_future)

    return base_stats, future_stats, hotspots


# ======================================================
# SUMMARY
# ======================================================

def summarize_trajectory(base, future, hotspots, rcp, year):

    delta = round(future["mean_risk"] - base["mean_risk"], 3)
    trend = "increase" if delta > 0 else "decrease"

    return f"""
📈 Climate-driven Simulation

Scenario:
- RCP: {rcp.upper()}
- Year: {year}

Initial mean risk: {base["mean_risk"]}
Final mean risk: {future["mean_risk"]}

Δ Risk: {delta}
Trend: {trend}

📍 Spatial Insight

High-risk areas: {future["high_share"]*100:.1f}%

🔥 Hotspots:
Top 5% threshold: {hotspots["threshold"]:.3f}
Cells: {hotspots["count"]}
Share: {hotspots["share"]*100:.1f}%
"""