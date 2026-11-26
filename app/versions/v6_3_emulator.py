"""
Massaciuccoli Digital Twin
SHAP Engine — PIPELINE SAFE VERSION (FIXED)
"""

import shap
import numpy as np


EXPLAINER = None


# ======================================================
# INIT (USE MODEL AFTER PREPROCESSING)
# ======================================================

def init_shap_explainer(model, background_df):

    global EXPLAINER

    if EXPLAINER is None:

        # separa pipeline
        preprocessor = model.named_steps["preprocessor"]
        estimator = model.named_steps["rf"]

        # trasforma dati
        background_transformed = preprocessor.transform(background_df)

        # crea explainer sul modello reale
        EXPLAINER = shap.TreeExplainer(estimator)

        # salva anche preprocessor
        EXPLAINER.preprocessor = preprocessor

    return EXPLAINER


# ======================================================
# COMPUTE SHAP
# ======================================================

def compute_shap_values(model, input_df, background_df):

    explainer = init_shap_explainer(model, background_df)

    preprocessor = explainer.preprocessor

    X = preprocessor.transform(input_df)

    shap_values = explainer.shap_values(X)

    return shap_values


# ======================================================
# MAP BACK TO ORIGINAL FEATURES (🔥 FIXED)
# ======================================================

def map_shap_to_original_features(model, shap_values, input_df):

    preprocessor = model.named_steps["preprocessor"]

    feature_names = preprocessor.get_feature_names_out()

    # 🔥 FIX: garantisce array 1D sempre
    values = np.array(shap_values)

    if values.ndim > 1:
        values = values[0]

    contributions = {}

    for name, val in zip(feature_names, values):

        # ricostruisce nome originale
        base_name = name.split("__")[-1]

        if base_name not in contributions:
            contributions[base_name] = 0

        contributions[base_name] += val

    return contributions