#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Diagnostica della sensibilità RF alle feature numeriche.
Passo predefinito: 2% del range osservato per ciascuna feature.

Esempio dalla root del progetto:
python app/tests/rf_feature_sensitivity_test.py --csv app/data/massaciuccoli_data.csv
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import numpy as np
import pandas as pd


def configure_project_imports():
    app_dir = Path(__file__).resolve().parents[1]
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))


def main():
    configure_project_imports()
    from versions.v6_1_emulator import NUM_FEATURES, load_and_train_emulator
    from utils.model_input_builder import clean_dataset, compute_baseline, build_scenario

    parser = argparse.ArgumentParser(description="Test soglie di sensibilità della RF")
    parser.add_argument("--csv", required=True, help="Percorso a massaciuccoli_data.csv")
    parser.add_argument("--step", type=float, default=2.0,
                        help="Passo in percentuale del range osservato (default 2)")
    parser.add_argument("--tolerance", type=float, default=1e-12)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    if not 0 < args.step <= 100:
        parser.error("--step deve essere > 0 e <= 100")

    csv_path = Path(args.csv).expanduser().resolve()
    if not csv_path.is_file():
        parser.error(f"CSV non trovato: {csv_path}")

    app_dir = Path(__file__).resolve().parents[1]
    dataset = clean_dataset(pd.read_csv(csv_path, skiprows=[1]))
    print(f"Dataset: {csv_path}\nRighe utilizzabili: {len(dataset):,}")
    print("Addestramento RF tramite load_and_train_emulator()...")
    model = load_and_train_emulator(str(csv_path))

    baseline = compute_baseline(dataset)
    baseline_df, _ = build_scenario({}, dataset)
    baseline_score = float(model.predict(baseline_df)[0])
    print(f"Risk score baseline: {baseline_score:.12f}\n")

    details, summaries = [], []
    for feature in NUM_FEATURES:
        vals = pd.to_numeric(dataset[feature], errors="coerce").dropna()
        if vals.empty:
            print(f"[SKIP] {feature}: nessun valore valido")
            continue
        vmin, vmax = float(vals.min()), float(vals.max())
        span = vmax - vmin
        base = float(baseline[feature])
        if not np.isfinite(span) or span <= 0:
            print(f"[SKIP] {feature}: range nullo/non valido")
            continue
        increment = span * args.step / 100.0
        max_up = int(np.floor((vmax - base) / increment + 1e-12))
        max_down = int(np.floor((base - vmin) / increment + 1e-12))
        first_changes = {"increase": None, "decrease": None}

        for direction, sign, max_steps in (
            ("increase", 1.0, max_up), ("decrease", -1.0, max_down)
        ):
            for n in range(1, max_steps + 1):
                target = base + sign * increment * n
                _, scenario_df = build_scenario(
                    {feature: {"type": "absolute_target", "value": float(target)}},
                    dataset,
                )
                score = float(model.predict(scenario_df)[0])
                delta = score - baseline_score
                changed = abs(delta) > args.tolerance
                row = {
                    "feature": feature, "direction": direction, "step_number": n,
                    "step_percent_of_observed_range": n * args.step,
                    "baseline_value": base, "scenario_value": float(target),
                    "observed_min": vmin, "observed_max": vmax,
                    "observed_range": span, "baseline_score": baseline_score,
                    "scenario_score": score, "score_delta": delta,
                    "score_changed": changed,
                }
                details.append(row)
                if changed and first_changes[direction] is None:
                    first_changes[direction] = row.copy()

        for direction in ("increase", "decrease"):
            first = first_changes[direction]
            summaries.append({
                "feature": feature, "direction": direction,
                "baseline_value": base, "observed_min": vmin,
                "observed_max": vmax, "observed_range": span,
                "first_change_step_percent": first["step_percent_of_observed_range"] if first else None,
                "first_change_value": first["scenario_value"] if first else None,
                "baseline_score": baseline_score,
                "score_at_first_change": first["scenario_score"] if first else None,
                "score_delta_at_first_change": first["score_delta"] if first else None,
                "status": "changed" if first else "no_change_within_observed_range",
            })
        up, down = first_changes["increase"], first_changes["decrease"]
        print(feature)
        print("  ↑ Aumento:", f"{up['step_percent_of_observed_range']:g}% (score {up['scenario_score']:.6f})" if up else "nessun cambiamento")
        print("  ↓ Diminuzione:", f"{down['step_percent_of_observed_range']:g}% (score {down['scenario_score']:.6f})" if down else "nessun cambiamento")

    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else app_dir / "tests" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    details_path = output_dir / "rf_feature_sensitivity_details.csv"
    summary_path = output_dir / "rf_feature_sensitivity_summary.csv"
    pd.DataFrame(details).to_csv(details_path, index=False)
    pd.DataFrame(summaries).to_csv(summary_path, index=False)
    print("\nFile prodotti:")
    print(details_path)
    print(summary_path)
    print("\nNota: questo primo test copre le 7 feature numeriche sulla baseline sintetica. Le 5 categoriche/binare richiedono un test distinto per categorie.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
