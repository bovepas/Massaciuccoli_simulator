import importlib.util
import sys
import numpy as np
import pandas as pd
from pathlib import Path

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

# ======================================================
# Sanity check
# ======================================================

CSV_PATH = "data/massaciuccoli_data.csv"

print("🔧 Training emulator...")
model = load_and_train_emulator(CSV_PATH)
print("✅ Model trained.\n")

df = pd.read_csv(CSV_PATH)

sample = df.sample(5, random_state=42)

TARGET_COL = (
    "Ecosystem risk classification according to a Variational Autoencoder "
    "with a later application of a Multi K-means process"
)

X_sample = sample.drop(columns=[TARGET_COL])

preds = model.predict(X_sample)

print("Predictions:", preds)
print("Min:", preds.min())
print("Max:", preds.max())
print("Any NaN:", np.isnan(preds).any())
