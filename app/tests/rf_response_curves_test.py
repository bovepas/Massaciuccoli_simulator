#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Curve di risposta del Random Forest del Massaciuccoli Digital Twin.

Varia una sola feature alla volta sulla baseline sintetica; tutte le altre
restano fisse. Produce CSV e PNG. Non modifica il codice di produzione.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd

DEFAULT_FEATURES = [
    "Density of tree cover",
    "Change in average temperature compared to a recent past",
    "Number of species potentially living in the cell",
]

def configure_project_imports() -> Path:
    app_dir = Path(__file__).resolve().parents[1]
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))
    return app_dir

def make_grid(values, baseline, n_points, integer_feature):
    numeric = pd.to_numeric(values, errors="coerce").dropna()
    if numeric.empty:
        raise ValueError("Nessun valore numerico valido.")
    low, high = float(numeric.quantile(.01)), float(numeric.quantile(.99))
    if not np.isfinite(low) or not np.isfinite(high) or high <= low:
        low, high = float(numeric.min()), float(numeric.max())
    if high <= low:
        raise ValueError("Range osservato nullo o non valido.")
    if integer_feature:
        grid = np.arange(int(np.ceil(low)), int(np.floor(high)) + 1, dtype=float)
        if grid.size == 0:
            grid = np.array([float(round(baseline))])
        grid = np.unique(np.append(grid, float(baseline)))
    else:
        grid = np.unique(np.append(
            np.linspace(low, high, n_points, dtype=float), float(baseline)
        ))
    return grid, low, high

def main():
    app_dir = configure_project_imports()
    from versions.v6_1_emulator import NUM_FEATURES, load_and_train_emulator
    from utils.model_input_builder import clean_dataset, compute_baseline, build_scenario

    parser = argparse.ArgumentParser(
        description="Curve di risposta RF su baseline sintetica"
    )
    parser.add_argument("--csv", required=True, help="Percorso a massaciuccoli_data.csv")
    parser.add_argument("--features", nargs="*", default=None,
                        help="Feature da testare; default: tree cover, temperatura, species richness")
    parser.add_argument("--points", type=int, default=101,
                        help="Punti per feature continue (default 101)")
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    if args.points < 3:
        parser.error("--points deve essere almeno 3")
    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.is_file():
        parser.error(f"CSV non trovato: {csv_path}")
    features = args.features or DEFAULT_FEATURES
    unknown = [f for f in features if f not in NUM_FEATURES]
    if unknown:
        parser.error("Feature sconosciute o non numeriche: " + "; ".join(unknown))

    output_dir = (Path(args.output_dir).expanduser().resolve()
                  if args.output_dir else app_dir / "tests" / "results")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Dataset: {csv_path}")
    dataset = clean_dataset(pd.read_csv(csv_path, skiprows=[1]))
    print(f"Righe utilizzabili: {len(dataset):,}")
    print("Addestramento RF tramite load_and_train_emulator()...")
    model = load_and_train_emulator(str(csv_path))
    baseline = compute_baseline(dataset)
    baseline_df, _ = build_scenario({}, dataset)
    baseline_score = float(model.predict(baseline_df)[0])
    print(f"Risk score baseline: {baseline_score:.12f}\n")

    all_rows = []
    for feature in features:
        values = pd.to_numeric(dataset[feature], errors="coerce")
        base_value = float(baseline[feature])
        is_integer = feature == "Number of species potentially living in the cell"
        grid, q01, q99 = make_grid(values, base_value, args.points, is_integer)
        rows = []
        for target in grid:
            _, scenario_df = build_scenario({
                feature: {"type": "absolute_target",
                          "value": int(target) if is_integer and float(target).is_integer() else float(target)}
            }, dataset)
            score = float(model.predict(scenario_df)[0])
            row = {
                "feature": feature, "feature_value": float(target),
                "baseline_feature_value": base_value,
                "baseline_risk_score": baseline_score,
                "scenario_risk_score": score,
                "risk_score_delta": score - baseline_score,
                "is_baseline_point": bool(np.isclose(target, base_value)),
                "grid_q01": q01, "grid_q99": q99,
                "observed_min": float(values.min()),
                "observed_max": float(values.max()),
                "n_dataset_rows": int(len(dataset)),
            }
            rows.append(row)
            all_rows.append(row)

        curve = pd.DataFrame(rows).sort_values("feature_value")
        safe = feature.lower().replace(" ", "_").replace(",", "").replace("/", "_")
        csv_out = output_dir / f"response_curve_{safe}.csv"
        png_out = output_dir / f"response_curve_{safe}.png"
        curve.to_csv(csv_out, index=False)
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(9, 5))
            ax.plot(curve["feature_value"], curve["scenario_risk_score"],
                    marker="o" if is_integer else None, markersize=3, linewidth=1.8)
            ax.axhline(baseline_score, linestyle="--", linewidth=1,
                       label=f"Baseline risk = {baseline_score:.4f}")
            ax.axvline(base_value, linestyle=":", linewidth=1,
                       label=f"Baseline feature = {base_value:.4g}")
            ax.set_xlabel(feature)
            ax.set_ylabel("Predicted risk_score")
            ax.set_title("RF response curve — " + feature)
            ax.grid(True, alpha=.25)
            ax.legend()
            fig.tight_layout()
            fig.savefig(png_out, dpi=160)
            plt.close(fig)
        except ImportError:
            print("[WARN] matplotlib non disponibile: grafico non generato.")

        changed = curve[np.abs(curve["risk_score_delta"]) > 1e-12]
        print(f"[{feature}]")
        print(f"  baseline feature: {base_value:.8g}")
        print(f"  intervallo testato (1°–99° percentile): {q01:.8g} – {q99:.8g}")
        print(f"  punti testati: {len(curve)}; risk score distinti: "
              f"{curve['scenario_risk_score'].nunique()}")
        print(f"  punti diversi dal baseline: {len(changed)}/{len(curve)}")
        print(f"  risk min/max: {curve['scenario_risk_score'].min():.8f} / "
              f"{curve['scenario_risk_score'].max():.8f}")
        print(f"  CSV: {csv_out}")
        if png_out.is_file():
            print(f"  PNG: {png_out}")
        print()

    combined = output_dir / "rf_response_curves_all_features.csv"
    pd.DataFrame(all_rows).to_csv(combined, index=False)
    print("Test completato.")
    print(f"CSV complessivo: {combined}")
    print(f"Output directory: {output_dir}")
    print("Nota: le curve descrivono il comportamento del surrogato RF, non causalità ecologica.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
