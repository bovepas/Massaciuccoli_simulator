"""
Spatial Analysis Tools
- Heatmap generation
- Hotspot detection
"""

import numpy as np
import matplotlib.pyplot as plt


# ======================================================
# HEATMAP
# ======================================================

def plot_risk_map(df, title="Risk Map"):

    # pivot su griglia
    grid = df.pivot(index="Latitude", columns="Longitude", values="risk_score")

    plt.figure()
    plt.imshow(grid.values, origin="lower")
    plt.colorbar(label="Risk score")
    plt.title(title)

    plt.xlabel("Longitude")
    plt.ylabel("Latitude")

    plt.tight_layout()
    plt.savefig("risk_map.png")
    plt.close()


# ======================================================
# DELTA MAP
# ======================================================

def plot_delta_map(df_base, df_future):

    delta = df_future["risk_score"].values - df_base["risk_score"].values

    df = df_base.copy()
    df["delta"] = delta

    grid = df.pivot(index="Latitude", columns="Longitude", values="delta")

    plt.figure()
    plt.imshow(grid.values, origin="lower")
    plt.colorbar(label="Δ Risk")

    plt.title("Risk Change Map")
    plt.tight_layout()
    plt.savefig("risk_delta_map.png")
    plt.close()


# ======================================================
# HOTSPOT DETECTION
# ======================================================

def detect_hotspots(df, top_percent=5):

    threshold = np.percentile(df["risk_score"], 100 - top_percent)

    hotspots = df[df["risk_score"] >= threshold]

    return {
        "threshold": threshold,
        "count": len(hotspots),
        "share": len(hotspots) / len(df)
    }