"""
Massaciuccoli Digital Twin
v10 — Dynamic Model with Live Data Support
"""

import pandas as pd
import numpy as np

from versions.v6_1_main import MODEL, NUM_FEATURES, CAT_FEATURES
from versions.v6_2_basin_engine import load_dataset, compute_basin_statistics
from tools.climate_loader import load_asc, extract_values_for_dataframe
from tools.spatial_analysis import detect_hotspots

# NEW
from tools.live_data_loader import build_live_dataframe


# ======================================================
# SCENARIO CONFIG
# ======================================================

SCENARIOS = {
    ("rcp45", "2050"): {
        "temp": "data/climate/rcp45/2050/Temperature.asc",
        "prec": "data/climate/rcp45/2050/Precipitation.asc"
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

def run_temporal_simulation(rcp="rcp45", year="2050", use_live_data=False):

    print(f"🌍 Scenario: {rcp.upper()} — {year}")

    # ======================================================
    # BASE DATA
    # ======================================================

    if use_live_data:
        print("📡 Using LIVE data as baseline")
        df = build_live_dataframe()
    else:
        df = load_dataset()

    # ======================================================
    # CLIMATE
    # ======================================================

    layers = load_climate_layers(rcp, year)
    delta_temp, delta_prec = compute_climate_delta(df, layers)

    # ======================================================
    # BASELINE
    # ======================================================

    df_base = predict(df)
    base_stats = compute_basin_statistics(df_base)

    # ======================================================
    # FUTURE
    # ======================================================

    df_future_input = apply_delta(df, delta_temp, delta_prec)
    df_future = predict(df_future_input)
    future_stats = compute_basin_statistics(df_future)

    # ======================================================
    # HOTSPOTS
    # ======================================================

    hotspots = detect_hotspots(df_future)

    return base_stats, future_stats, hotspots