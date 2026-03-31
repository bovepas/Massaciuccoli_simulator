"""
Massaciuccoli Digital Twin
Fase 6.1 — Emulator + Explanation Layer
"""

import importlib.util
import sys
from pathlib import Path
import pandas as pd


# ======================================================
# Dynamic import of emulator
# ======================================================

EMULATOR_PATH = Path("versions/v6_1_emulator.py")

spec = importlib.util.spec_from_file_location(
    "emulator_6_1",
    EMULATOR_PATH
)
emulator = importlib.util.module_from_spec(spec)
sys.modules["emulator_6_1"] = emulator
spec.loader.exec_module(emulator)

load_and_train_emulator = emulator.load_and_train_emulator
NUM_FEATURES = emulator.NUM_FEATURES
CAT_FEATURES = emulator.CAT_FEATURES


# ======================================================
# Load model once
# ======================================================

CSV_PATH = "data/massaciuccoli_data.csv"

print("🔧 Loading ecosystem risk emulator...")
MODEL = load_and_train_emulator(CSV_PATH)
print("✅ Emulator ready.\n")


# ======================================================
# Risk score → label
# ======================================================

def risk_level_from_score(score: float) -> str:
    if score < 0.33:
        return "Low Risk"
    elif score < 0.66:
        return "Medium Risk"
    else:
        return "High Risk"


# ======================================================
# Explanation layer
# ======================================================

FEATURE_EXPLANATIONS = {
    "Number of species potentially living in the cell":
        "high biodiversity increases ecosystem fragility",
    "Index of total productivity by plant phenology":
        "high vegetation productivity indicates valuable but vulnerable ecosystems",
    "Density of tree cover":
        "tree cover represents structural ecosystem stability",
    "Change in average temperature compared to a recent past":
        "temperature increase acts as a direct climatic stressor",
    "Presence of grassland":
        "grasslands are fragile green areas to be preserved",
    "Cumulative change in precipitation compared to a recent past":
        "reduced precipitation increases aridity stress",
    "Relative change in the potential evapotranspiration compared to a recent past":
        "changes in evapotranspiration affect water availability",
}


def explain_prediction(input_df: pd.DataFrame, top_k: int = 3) -> list:
    rf = MODEL.named_steps["rf"]
    preprocessor = MODEL.named_steps["preprocessor"]

    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_names = cat_encoder.get_feature_names_out(CAT_FEATURES)
    all_names = NUM_FEATURES + list(cat_names)

    importances = rf.feature_importances_

    importance_df = pd.DataFrame({
        "feature": all_names,
        "importance": importances
    })

    def collapse(name):
        for c in CAT_FEATURES:
            if name.startswith(c + "_"):
                return c
        return name

    importance_df["original"] = importance_df["feature"].apply(collapse)

    aggregated = (
        importance_df
        .groupby("original")["importance"]
        .sum()
        .sort_values(ascending=False)
    )

    explanations = []
    for feature in aggregated.head(top_k).index:
        if feature in FEATURE_EXPLANATIONS:
            explanations.append(FEATURE_EXPLANATIONS[feature])

    return explanations


# ======================================================
# Public API
# ======================================================

def run_emulator_and_explain(stressor_dict: dict) -> dict:
    df = pd.DataFrame([stressor_dict])
    score = float(MODEL.predict(df)[0])
    level = risk_level_from_score(score)
    explanation = explain_prediction(df)

    return {
        "risk_score": round(score, 3),
        "risk_level": level,
        "explanation": explanation
    }


# ======================================================
# Standalone test
# ======================================================

if __name__ == "__main__":
    print("=== Emulator test mode ===\n")

    example = {
        "Density change in land imperviousness": 180,
        "Density of tree cover": 80,
        "Change in tree cover density in the past decade": 2,
        "Presence of grassland": 1,
        "Change in grassland presence  in the past decade": 2,
        "Land use and cover": 1120,
        "Index of total productivity by plant phenology": 300,
        "Change in average temperature compared to a recent past": 2.5,
        "Relative change in the potential evapotranspiration compared to a recent past": -5,
        "Cumulative change in precipitation compared to a recent past": -25,
        "Number of species potentially living in the cell": 250,
        "Change in land use and cover in the past decade": 1
    }

    result = run_emulator_and_explain(example)
    print(result)
