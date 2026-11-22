#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test isolato per simulare la perdita percentuale di celle con grassland.

Il test:
1. carica e addestra la RF usando il model builder già esistente;
2. calcola il risk score di tutte le celle del lago;
3. trasforma in 0 una quota delle celle che hanno Presence of grassland = 1;
4. ricalcola il risk score sulle stesse celle;
5. confronta rischio medio, mediano e distribuzione delle predizioni.

Non modifica task_delta.py, il dataset originale o il modello di training.
Eseguire dalla root del progetto, dove sono disponibili:
    versions/v6_1_emulator.py

Esempio:
    python test_grassland_spatial_delta.py
    python test_grassland_spatial_delta.py --csv data/massaciuccoli_data.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


GRASSLAND_FEATURE = "Presence of grassland"
DEFAULT_LOSS_RATES = (10, 30, 50, 100)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Test indipendente della perdita percentuale di grassland."
    )
    parser.add_argument(
        "--csv",
        default="data/massaciuccoli_data.csv",
        help="Percorso del CSV originale (default: data/massaciuccoli_data.csv).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed per selezionare in modo riproducibile le celle trasformate.",
    )
    parser.add_argument(
        "--loss-rates",
        type=float,
        nargs="+",
        default=list(DEFAULT_LOSS_RATES),
        help="Percentuali di celle con grassland=1 da trasformare in 0.",
    )
    parser.add_argument(
        "--output",
        default="grassland_delta_test_results.csv",
        help="CSV di riepilogo dei risultati (default: grassland_delta_test_results.csv).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Import dal model builder effettivo del progetto: nessuna copia del modello.
    try:
        from versions.v6_1_emulator import (
            CAT_FEATURES,
            NUM_FEATURES,
            TARGET,
            load_and_train_emulator,
            preprocess_semantic_features,
        )
    except ImportError as exc:
        raise SystemExit(
            "Impossibile importare versions.v6_1_emulator. "
            "Esegui lo script dalla root del progetto e verifica che "
            "versions/v6_1_emulator.py sia presente.\n"
            f"Dettaglio: {exc}"
        )

    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.is_file():
        raise SystemExit(f"Dataset non trovato: {csv_path}")

    if any(rate < 0 or rate > 100 for rate in args.loss_rates):
        raise SystemExit("Le percentuali di perdita devono essere comprese tra 0 e 100.")

    required_columns = NUM_FEATURES + CAT_FEATURES + [TARGET]
    raw = pd.read_csv(csv_path, skiprows=[1])

    missing = [col for col in required_columns if col not in raw.columns]
    if missing:
        raise SystemExit(f"Nel dataset mancano queste colonne richieste: {missing}")

    # Il dataset completo rappresenta le celle del lago. Il target serve al training,
    # ma non viene usato per filtrare le celle sulle quali calcoliamo le predizioni.
    grassland = pd.to_numeric(raw[GRASSLAND_FEATURE], errors="coerce")
    valid_grassland = grassland.isin([0, 1])
    if not valid_grassland.all():
        invalid_count = int((~valid_grassland).sum())
        raise SystemExit(
            f"{invalid_count} righe hanno un valore di grassland diverso da 0/1 "
            "o mancante. Il test si ferma per non alterare implicitamente il dataset."
        )

    n_cells = len(raw)
    positive_indices = np.flatnonzero(grassland.to_numpy() == 1)
    n_positive = len(positive_indices)
    n_zero = n_cells - n_positive

    if n_cells == 0 or n_positive == 0:
        raise SystemExit("Dataset vuoto oppure nessuna cella con grassland=1.")

    print("\n=== DATASET ===")
    print(f"File: {csv_path}")
    print(f"Celle totali: {n_cells:,}")
    print(f"Grassland = 1: {n_positive:,} ({n_positive / n_cells:.2%})")
    print(f"Grassland = 0: {n_zero:,} ({n_zero / n_cells:.2%})")

    print("\n=== TRAINING MODELLO ===")
    print("Addestramento con load_and_train_emulator() del progetto...")
    model = load_and_train_emulator(str(csv_path))
    print("Modello addestrato.")

    feature_columns = NUM_FEATURES + CAT_FEATURES

    # Predizioni baseline su tutte le celle del lago.
    X_base = raw[feature_columns].copy()
    X_base[GRASSLAND_FEATURE] = grassland
    X_base = preprocess_semantic_features(X_base)
    baseline_predictions = np.asarray(model.predict(X_base), dtype=float)

    baseline_mean = float(np.mean(baseline_predictions))
    baseline_median = float(np.median(baseline_predictions))

    print("\n=== BASELINE RF SU TUTTO IL LAGO ===")
    print(f"Risk score medio:   {baseline_mean:.6f}")
    print(f"Risk score mediano: {baseline_median:.6f}")
    print(
        "Predizioni (min / max): "
        f"{baseline_predictions.min():.6f} / {baseline_predictions.max():.6f}"
    )

    # Una sola permutazione rende annidati gli scenari:
    # il 10% è contenuto nel 30%, il 30% nel 50%, ecc.
    rng = np.random.default_rng(args.seed)
    shuffled_positive = rng.permutation(positive_indices)

    rows = []
    for loss_rate in args.loss_rates:
        n_to_remove = int(round(n_positive * loss_rate / 100.0))
        selected_indices = shuffled_positive[:n_to_remove]

        X_scenario = X_base.copy()
        if n_to_remove:
            # Cambia esclusivamente la feature grassland nelle celle selezionate.
            X_scenario.loc[
                X_scenario.index[selected_indices], GRASSLAND_FEATURE
            ] = 0

        # Applica lo stesso preprocessing semantico usato nel training.
        X_scenario = preprocess_semantic_features(X_scenario)
        scenario_predictions = np.asarray(model.predict(X_scenario), dtype=float)

        differences = scenario_predictions - baseline_predictions
        changed_mask = np.abs(differences) > 1e-12

        scenario_mean = float(np.mean(scenario_predictions))
        scenario_median = float(np.median(scenario_predictions))
        mean_delta = scenario_mean - baseline_mean

        # Conteggi dopo la trasformazione.
        remaining_ones = n_positive - n_to_remove
        new_zeros = n_zero + n_to_remove

        row = {
            "grassland_loss_percent": loss_rate,
            "cells_total": n_cells,
            "grassland_ones_baseline": n_positive,
            "grassland_ones_removed": n_to_remove,
            "grassland_ones_remaining": remaining_ones,
            "grassland_zeros_after": new_zeros,
            "grassland_presence_percent_after": 100 * remaining_ones / n_cells,
            "baseline_mean_risk": baseline_mean,
            "scenario_mean_risk": scenario_mean,
            "mean_risk_delta": mean_delta,
            "baseline_median_risk": baseline_median,
            "scenario_median_risk": scenario_median,
            "cells_with_changed_prediction": int(changed_mask.sum()),
            "percent_cells_with_changed_prediction": 100 * float(changed_mask.mean()),
            "mean_delta_on_changed_cells": (
                float(differences[changed_mask].mean()) if changed_mask.any() else 0.0
            ),
            "min_scenario_risk": float(scenario_predictions.min()),
            "max_scenario_risk": float(scenario_predictions.max()),
        }
        rows.append(row)

        print(f"\n=== PERDITA GRASSLAND {loss_rate:g}% ===")
        print(f"Celle trasformate 1 -> 0: {n_to_remove:,}")
        print(f"Celle con grassland=1 rimaste: {remaining_ones:,}")
        print(f"Nuova presenza globale: {row['grassland_presence_percent_after']:.2f}%")
        print(f"Risk score medio: {scenario_mean:.6f}")
        print(f"Delta rispetto alla baseline: {mean_delta:+.6f}")
        print(f"Celle con predizione modificata: {changed_mask.sum():,} "
              f"({changed_mask.mean():.2%})")

    results = pd.DataFrame(rows)
    output_path = Path(args.output).expanduser().resolve()
    results.to_csv(output_path, index=False)

    print("\n=== RIEPILOGO ===")
    display_columns = [
        "grassland_loss_percent",
        "grassland_ones_remaining",
        "grassland_presence_percent_after",
        "scenario_mean_risk",
        "mean_risk_delta",
        "cells_with_changed_prediction",
        "percent_cells_with_changed_prediction",
    ]
    print(results[display_columns].to_string(index=False))
    print(f"\nRisultati salvati in: {output_path}")
    print("\nNota: il test usa una selezione casuale riproducibile delle celle.")
    print("Non rappresenta ancora un modello di perdita spazialmente mirata.")


if __name__ == "__main__":
    main()
