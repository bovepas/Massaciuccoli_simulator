# -*- coding: utf-8 -*-

"""
Model Input Builder — Single Source of Truth

Garantisce:
- colonne corrette (NUM + CAT)
- preprocessing semantico coerente con training
- baseline robusto (mean + mode)
"""

import pandas as pd

from versions.v6_1_emulator import (
    NUM_FEATURES,
    CAT_FEATURES,
    preprocess_semantic_features
)


# ======================================================
# CLEAN DATASET
# ======================================================

def clean_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    df = dataset.copy()

    test_col = NUM_FEATURES[0]
    df[test_col] = pd.to_numeric(df[test_col], errors="coerce")

    df = df[df[test_col].notna()]

    return df


# ======================================================
# BASELINE
# ======================================================

def compute_baseline(dataset: pd.DataFrame) -> dict:

    dataset = clean_dataset(dataset)

    baseline = {}

    # NUMERIC → mean
    for col in NUM_FEATURES:
        baseline[col] = float(pd.to_numeric(dataset[col], errors="coerce").mean())

    # CATEGORICAL → mode
    for col in CAT_FEATURES:
        baseline[col] = dataset[col].mode().iloc[0]

    return baseline


# ======================================================
# BUILD INPUT DF
# ======================================================

def build_input_df(values: dict, dataset: pd.DataFrame) -> pd.DataFrame:

    baseline = compute_baseline(dataset)

    baseline.update(values)

    df = pd.DataFrame([baseline])

    df = df[NUM_FEATURES + CAT_FEATURES]

    df = preprocess_semantic_features(df)

    return df


# ======================================================
# BUILD BASELINE + SCENARIO (🔥 FIX SCALING)
# ======================================================

def build_baseline_and_scenario(delta_values: dict, dataset: pd.DataFrame):

    baseline = compute_baseline(dataset)

    scenario = baseline.copy()

    for k, v in delta_values.items():

        if k in baseline and isinstance(baseline[k], (int, float)):

            base_val = baseline[k]

            # 🔥 piccoli valori → delta assoluto (es temperatura)
            if abs(v) <= 5:
                scenario[k] = base_val + v

            # 🔥 grandi valori → percentuale
            else:
                scenario[k] = base_val * (1 + v / 100)

        else:
            scenario[k] = v

    df_base = pd.DataFrame([baseline])[NUM_FEATURES + CAT_FEATURES]
    df_scen = pd.DataFrame([scenario])[NUM_FEATURES + CAT_FEATURES]

    df_base = preprocess_semantic_features(df_base)
    df_scen = preprocess_semantic_features(df_scen)

    return df_base, df_scen