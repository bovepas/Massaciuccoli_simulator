"""
Massaciuccoli Digital Twin
Basin Scenario Engine — v6.2 module

This module:
- Loads full spatial dataset
- Applies stressor deltas
- Runs emulator on all cells
- Computes basin-level statistics
"""

import pandas as pd
from versions.v6_1_main import MODEL
from versions.v6_1_emulator import NUM_FEATURES, CAT_FEATURES


CSV_PATH = "data/massaciuccoli_data.csv"


# ======================================================
# Load dataset
# ======================================================

def load_dataset():
    df = pd.read_csv(CSV_PATH, skiprows=[1])
    return df


# ======================================================
# Apply stressor deltas
# ======================================================

def apply_scenario(df, scenario_dict):

    df_modified = df.copy()

    for variable, delta in scenario_dict.items():

        if variable not in df_modified.columns:
            continue

        # percentage modification
        if isinstance(delta, str) and "%" in delta:
            percent = float(delta.replace("%", ""))
            df_modified[variable] = df_modified[variable] * (1 + percent / 100)

        # additive modification
        else:
            df_modified[variable] = df_modified[variable] + delta

    return df_modified


# ======================================================
# Run emulator on full basin
# ======================================================

def predict_risk(df):

    X = df[NUM_FEATURES + CAT_FEATURES]

    predictions = MODEL.predict(X)

    df_result = df.copy()
    df_result["risk_score"] = predictions

    return df_result


# ======================================================
# Basin statistics
# ======================================================

def compute_basin_statistics(df):

    mean_risk = df["risk_score"].mean()

    low = (df["risk_score"] < 0.33).mean()
    medium = ((df["risk_score"] >= 0.33) & (df["risk_score"] < 0.66)).mean()
    high = (df["risk_score"] >= 0.66).mean()

    return {
        "mean_risk": round(mean_risk, 3),
        "low_share": round(low, 3),
        "medium_share": round(medium, 3),
        "high_share": round(high, 3)
    }


# ======================================================
# Full simulation pipeline
# ======================================================

def run_basin_simulation(scenario_dict):

    # Baseline
    df = load_dataset()
    baseline_pred = predict_risk(df)
    baseline_stats = compute_basin_statistics(baseline_pred)

    # Scenario
    df_scenario = apply_scenario(df, scenario_dict)
    scenario_pred = predict_risk(df_scenario)
    scenario_stats = compute_basin_statistics(scenario_pred)

    # Delta
    delta_mean = round(
        scenario_stats["mean_risk"] - baseline_stats["mean_risk"], 3
    )

    delta_high = round(
        scenario_stats["high_share"] - baseline_stats["high_share"], 3
    )

    return {
        "baseline": baseline_stats,
        "scenario": scenario_stats,
        "delta_mean_risk": delta_mean,
        "delta_high_risk_share": delta_high
    }
