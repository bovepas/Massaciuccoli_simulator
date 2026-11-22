#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Spatial sensitivity test for all numeric RF emulator features.

For each numeric feature, perturbs one feature at a time across all valid
dataset cells, in both directions. The perturbation is based on a fixed
fraction of the observed feature range and is clipped to the observed bounds.

For the discrete species-count feature, the perturbation is rounded to an
integer and is forced to at least one unit wherever movement in that
direction is possible.

This measures sensitivity of the fitted RF surrogate, not ecological
causality. It does not modify or retrain the model logic.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


SPECIES_FEATURE = "Number of species potentially living in the cell"


def configure_project_imports() -> Path:
    # Intended location: app/tests/rf_spatial_sensitivity_test.py
    app_dir = Path(__file__).resolve().parents[1]
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    return app_dir


def predict_in_batches(model, frame: pd.DataFrame, batch_size: int) -> np.ndarray:
    predictions = []
    for start in range(0, len(frame), batch_size):
        batch = frame.iloc[start:start + batch_size]
        predictions.append(np.asarray(model.predict(batch), dtype=float))
    if not predictions:
        return np.array([], dtype=float)
    return np.concatenate(predictions)


def perturb_feature(
    original_values: np.ndarray,
    vmin: float,
    vmax: float,
    step_size: float,
    sign: float,
    feature: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return perturbed values, actual perturbation mask, and clipping mask."""
    proposed = original_values + sign * step_size

    if feature == SPECIES_FEATURE:
        # Species count is discrete. Ensure a one-individual step when a
        # 2%-of-range step would otherwise round to zero.
        integer_step = max(1, int(round(step_size)))
        proposed = original_values + sign * integer_step
        perturbed = np.clip(np.rint(proposed), np.ceil(vmin), np.floor(vmax))
    else:
        perturbed = np.clip(proposed, vmin, vmax)

    # Preserve missing values for the model's own preprocessing/imputer.
    finite = np.isfinite(original_values)
    perturbed[~finite] = np.nan

    actually_perturbed = finite & (np.abs(perturbed - original_values) > 1e-12)
    clipped = (
        finite
        & np.isfinite(proposed)
        & (np.abs(perturbed - proposed) > 1e-12)
    )
    return perturbed, actually_perturbed, clipped


def main() -> int:
    app_dir = configure_project_imports()

    from versions.v6_1_emulator import (
        NUM_FEATURES,
        CAT_FEATURES,
        TARGET,
        RISK_MAP,
        load_and_train_emulator,
        preprocess_semantic_features,
    )
    from utils.model_input_builder import clean_dataset

    parser = argparse.ArgumentParser(
        description="Test di sensibilità spaziale di tutte le feature numeriche RF"
    )
    parser.add_argument("--csv", required=True, help="Percorso a massaciuccoli_data.csv")
    parser.add_argument(
        "--step",
        type=float,
        default=2.0,
        help="Passo come percentuale del range osservato (default: 2)",
    )
    parser.add_argument("--tolerance", type=float, default=1e-12)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--output-dir", default=None)
    parser.add_argument(
        "--features",
        nargs="*",
        default=None,
        help="Sottoinsieme opzionale di feature numeriche; senza opzione testa tutte",
    )
    args = parser.parse_args()

    if not 0 < args.step <= 100:
        parser.error("--step deve essere > 0 e <= 100")
    if args.batch_size <= 0:
        parser.error("--batch-size deve essere > 0")

    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.is_file():
        parser.error(f"CSV non trovato: {csv_path}")

    features = list(args.features) if args.features else list(NUM_FEATURES)
    unknown = [feature for feature in features if feature not in NUM_FEATURES]
    if unknown:
        parser.error(f"Feature non numeriche o sconosciute: {unknown}")

    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else Path(__file__).resolve().parent / "results"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dataset: {csv_path}")
    raw = pd.read_csv(csv_path, skiprows=[1])
    raw = raw[raw[TARGET].isin(RISK_MAP.keys())].copy()
    raw = clean_dataset(raw)
    raw["_source_row_index"] = raw.index
    raw = raw.reset_index(drop=True)

    feature_columns = list(NUM_FEATURES) + list(CAT_FEATURES)
    missing = [col for col in feature_columns if col not in raw.columns]
    if missing:
        raise ValueError(f"Colonne mancanti nel CSV: {missing}")

    print(f"Celle utilizzabili: {len(raw):,}")
    print(f"Feature numeriche da testare: {len(features)}")
    for feature in features:
        print(f"  - {feature}")

    print("\nAddestramento RF con load_and_train_emulator()...")
    model = load_and_train_emulator(str(csv_path))

    X_raw = raw[feature_columns].copy()
    X_base = preprocess_semantic_features(X_raw)
    baseline_scores = predict_in_batches(model, X_base, args.batch_size)

    print(
        f"\nScore baseline medio: {baseline_scores.mean():.12f}\n"
        f"Passo nominale: {args.step:g}% del range osservato "
        "di ciascuna feature"
    )

    summaries: list[dict] = []
    detail_frames: list[pd.DataFrame] = []

    for feature in features:
        original_values = pd.to_numeric(
            X_raw[feature], errors="coerce"
        ).to_numpy(dtype=float)
        finite = np.isfinite(original_values)
        if not finite.any():
            print(f"\n[SKIP] {feature}: nessun valore numerico valido")
            continue

        vmin = float(np.nanmin(original_values))
        vmax = float(np.nanmax(original_values))
        span = vmax - vmin
        if not np.isfinite(span) or span <= 0:
            print(f"\n[SKIP] {feature}: range nullo/non valido")
            continue

        step_size = span * args.step / 100.0
        if feature == SPECIES_FEATURE:
            effective_step = max(1, int(round(step_size)))
        else:
            effective_step = step_size

        print(
            f"\n[FEATURE] {feature}\n"
            f"  min={vmin:.8g} max={vmax:.8g} "
            f"passo_nominale={step_size:.8g} "
            f"passo_effettivo={effective_step}"
        )

        for direction, sign in (("increase", 1.0), ("decrease", -1.0)):
            perturbed_values, perturbed_mask, clipped = perturb_feature(
                original_values=original_values.copy(),
                vmin=vmin,
                vmax=vmax,
                step_size=step_size,
                sign=sign,
                feature=feature,
            )

            modified = X_raw.copy()
            modified[feature] = perturbed_values
            X_perturbed = preprocess_semantic_features(modified[feature_columns])
            perturbed_scores = predict_in_batches(
                model, X_perturbed, args.batch_size
            )

            delta_feature = perturbed_values - original_values
            delta_scores = perturbed_scores - baseline_scores
            score_changed = np.isfinite(delta_scores) & (
                np.abs(delta_scores) > args.tolerance
            )

            n_cells = len(raw)
            n_perturbed = int(perturbed_mask.sum())
            n_score_changed = int(score_changed.sum())
            n_changed_among_perturbed = int(
                (score_changed & perturbed_mask).sum()
            )

            summary = {
                "feature": feature,
                "direction": direction,
                "n_cells": n_cells,
                "n_cells_with_valid_feature": int(finite.sum()),
                "n_cells_feature_perturbed": n_perturbed,
                "pct_cells_feature_perturbed": (
                    float(n_perturbed / finite.sum() * 100) if finite.any() else 0.0
                ),
                # Kept for comparability with the previous spatial test:
                # denominator = all dataset cells.
                "n_cells_score_changed": n_score_changed,
                "pct_cells_score_changed_all": float(
                    n_score_changed / n_cells * 100
                ) if n_cells else 0.0,
                # More informative sensitivity rate: only cells whose input
                # feature actually changed are included in the denominator.
                "n_cells_score_changed_among_perturbed": n_changed_among_perturbed,
                "pct_cells_score_changed_among_perturbed": (
                    float(n_changed_among_perturbed / n_perturbed * 100)
                    if n_perturbed else None
                ),
                "n_score_increased": int(
                    ((delta_scores > args.tolerance) & perturbed_mask).sum()
                ),
                "n_score_decreased": int(
                    ((delta_scores < -args.tolerance) & perturbed_mask).sum()
                ),
                "n_score_unchanged_among_perturbed": int(
                    ((np.abs(delta_scores) <= args.tolerance) & perturbed_mask).sum()
                ),
                "mean_baseline_score": float(np.mean(baseline_scores)),
                "mean_perturbed_score": float(np.mean(perturbed_scores)),
                "mean_delta_score_all_cells": float(np.mean(delta_scores)),
                "mean_delta_score_among_perturbed": (
                    float(np.mean(delta_scores[perturbed_mask]))
                    if n_perturbed else None
                ),
                "median_delta_score_among_perturbed": (
                    float(np.median(delta_scores[perturbed_mask]))
                    if n_perturbed else None
                ),
                "n_feature_values_clipped": int(clipped.sum()),
                "pct_feature_values_clipped_all": float(
                    clipped.sum() / n_cells * 100
                ) if n_cells else 0.0,
                "pct_feature_values_clipped_among_valid": (
                    float(clipped.sum() / finite.sum() * 100)
                    if finite.any() else 0.0
                ),
                "feature_min": vmin,
                "feature_max": vmax,
                "step_native_units_nominal": step_size,
                "step_pct_of_range_nominal": args.step,
                "step_native_units_effective": effective_step,
                "tolerance": args.tolerance,
            }
            summaries.append(summary)

            detail_frames.append(pd.DataFrame({
                "row_index": np.arange(n_cells, dtype=int),
                "source_row_index": raw["_source_row_index"].to_numpy(),
                "feature": feature,
                "direction": direction,
                "original_feature_value": original_values,
                "perturbed_feature_value": perturbed_values,
                "feature_was_perturbed": perturbed_mask,
                "feature_value_was_clipped": clipped,
                "feature_delta": delta_feature,
                "baseline_risk_score": baseline_scores,
                "perturbed_risk_score": perturbed_scores,
                "risk_score_delta": delta_scores,
                "risk_score_changed": score_changed,
            }))

            pct_all = n_score_changed / n_cells * 100 if n_cells else 0.0
            pct_eligible = (
                n_changed_among_perturbed / n_perturbed * 100
                if n_perturbed else 0.0
            )
            print(
                f"  {direction:8s}: "
                f"feature modificata in {n_perturbed:,}/{int(finite.sum()):,} "
                f"celle ({(n_perturbed / finite.sum() * 100):.2f}%), "
                f"score cambiato in {n_changed_among_perturbed:,} celle "
                f"({pct_eligible:.2f}% delle celle effettivamente perturbate; "
                f"{pct_all:.2f}% di tutte le celle), "
                f"clipping={clipped.sum() / finite.sum() * 100:.2f}%"
            )

    summary_path = output_dir / "rf_spatial_sensitivity_summary.csv"
    details_path = output_dir / "rf_spatial_sensitivity_details.csv"

    pd.DataFrame(summaries).to_csv(summary_path, index=False)
    if detail_frames:
        pd.concat(detail_frames, ignore_index=True).to_csv(details_path, index=False)

    print("\nTest completato.")
    print(f"Summary: {summary_path}")
    print(f"Details: {details_path}")
    print(
        "\nNota: il test copre tutte le feature numeriche (NUM_FEATURES). "
        "Le feature categoriche in CAT_FEATURES non hanno una direzione "
        "aumento/diminuzione e richiedono un test separato per transizioni "
        "tra categorie."
    )
    print(
        "Interpretazione: misura la sensibilità del surrogato RF nelle "
        "celle del dataset; non dimostra causalità ecologica."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
