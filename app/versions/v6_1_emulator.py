"""
Massaciuccoli Digital Twin
Fase 6.1 — Emulator ML (Random Forest)

Questo modulo:
- definisce le feature dell’emulatore
- applica preprocessing semantico coerente con il VAE originale
- costruisce e allena un Random Forest Regressor
- restituisce un modello pronto a stimare un risk_score ∈ [0,1]

NOTA:
Il CSV contiene una seconda riga descrittiva delle variabili,
che viene correttamente saltata in fase di lettura.
"""

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestRegressor


# ======================================================
# Feature definitions
# ======================================================

NUM_FEATURES = [
    "Density change in land imperviousness",
    "Density of tree cover",
    "Index of total productivity by plant phenology",
    "Change in average temperature compared to a recent past",
    "Relative change in the potential evapotranspiration compared to a recent past",
    "Cumulative change in precipitation compared to a recent past",
    "Number of species potentially living in the cell",
]

CAT_FEATURES = [
    "Change in tree cover density in the past decade",
    "Presence of grassland",
    "Change in grassland presence  in the past decade",
    "Land use and cover",
    "Change in land use and cover in the past decade",
]

TARGET = (
    "Ecosystem risk classification according to a Variational Autoencoder "
    "with a later application of a Multi K-means process"
)


# ======================================================
# Target mapping
# ======================================================

RISK_MAP = {
    "Low Risk": 0.0,
    "Medium Risk": 0.5,
    "High Risk": 1.0,
}


# ======================================================
# Semantic preprocessing
# ======================================================

def preprocess_semantic_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["Change in tree cover density in the past decade"] = (
        df["Change in tree cover density in the past decade"]
        .fillna("no_tree_cover")
        .replace({
            0: "unchanged_no_tree",
            1: "gain_tree",
            2: "loss_tree",
            10: "unchanged_with_tree",
        })
    )

    df["Change in grassland presence  in the past decade"] = (
        df["Change in grassland presence  in the past decade"]
        .replace({
            0: "unchanged",
            10: "unchanged",
            1: "gain",
            11: "gain",
            2: "loss",
            22: "loss",
        })
    )

    df["Land use and cover"] = (
        df["Land use and cover"]
        .fillna("uncovered_or_unused")
        .replace({
            1120: "industrial_military",
            1310: "extraction_construction",
            8120: "modified_watercourses",
        })
    )

    df["Land use and cover"] = df["Land use and cover"].where(
        df["Land use and cover"].isin([
            "industrial_military",
            "extraction_construction",
            "modified_watercourses",
            "uncovered_or_unused",
        ]),
        "rural_natural"
    )

    df["Change in land use and cover in the past decade"] = (
        df["Change in land use and cover in the past decade"]
        .fillna(0)
        .replace({
            0: "no_change_or_natural",
            1: "anthropogenic_change",
            2: "agriculture",
        })
    )

    return df


# ======================================================
# Model builder
# ======================================================

def build_emulator() -> Pipeline:
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median"))
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUM_FEATURES),
            ("cat", categorical_transformer, CAT_FEATURES),
        ]
    )

    rf_model = RandomForestRegressor(
        n_estimators=300,
        max_depth=None,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )

    return Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("rf", rf_model),
    ])


# ======================================================
# Training utility
# ======================================================

def load_and_train_emulator(csv_path: str) -> Pipeline:
    # Skip second descriptive row
    df = pd.read_csv(csv_path, skiprows=[1])

    # Keep only valid target rows
    df = df[df[TARGET].isin(RISK_MAP.keys())]

    # Map target to numeric
    df[TARGET] = df[TARGET].map(RISK_MAP)

    # Semantic preprocessing
    df = preprocess_semantic_features(df)

    X = df[NUM_FEATURES + CAT_FEATURES]
    y = df[TARGET]

    model = build_emulator()
    model.fit(X, y)

    return model
