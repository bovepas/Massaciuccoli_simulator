"""
Feature importance analysis for Massaciuccoli emulator (v6.1)

This script:
- trains the emulator
- extracts feature importances from the Random Forest
- aggregates one-hot encoded features back to original variables
- prints a ranked importance table
"""

import importlib.util
import sys
from pathlib import Path

import pandas as pd
import numpy as np


# ======================================================
# Dynamic import of 6_1_emulator.py
# ======================================================

EMULATOR_PATH = Path("versions/6_1_emulator.py")

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
# Train model
# ======================================================

CSV_PATH = "data/massaciuccoli_data.csv"

print("🔧 Training emulator...")
model = load_and_train_emulator(CSV_PATH)
print("✅ Model trained.\n")


# ======================================================
# Extract feature names after preprocessing
# ======================================================

preprocessor = model.named_steps["preprocessor"]
rf = model.named_steps["rf"]

# numeric features
num_feature_names = NUM_FEATURES

# categorical features (expanded by one-hot)
cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
cat_feature_names = cat_encoder.get_feature_names_out(CAT_FEATURES)

all_feature_names = list(num_feature_names) + list(cat_feature_names)


# ======================================================
# Raw feature importances
# ======================================================

importances = rf.feature_importances_

importance_df = pd.DataFrame({
    "feature": all_feature_names,
    "importance": importances
}).sort_values("importance", ascending=False)


# ======================================================
# Aggregate back to original features
# ======================================================

def original_feature_name(feature_name: str) -> str:
    """
    Collapse one-hot encoded features back to original variable name.
    """
    for cat in CAT_FEATURES:
        if feature_name.startswith(cat + "_"):
            return cat
    return feature_name


importance_df["original_feature"] = importance_df["feature"].apply(
    original_feature_name
)

aggregated = (
    importance_df
    .groupby("original_feature", as_index=False)["importance"]
    .sum()
    .sort_values("importance", ascending=False)
)


# ======================================================
# Output
# ======================================================

print("🌱 FEATURE IMPORTANCE — aggregated by original variable\n")
print(aggregated.to_string(index=False))

print("\n📊 TOP 10 detailed (one-hot level)\n")
print(importance_df.head(10).to_string(index=False))

