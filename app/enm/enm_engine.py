"""
Massaciuccoli Digital Twin
ENM Engine — MaxEnt FINAL (CLEAN + TIMEOUT SAFE)
"""

import os
import subprocess
import pandas as pd
import shutil
import time


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MAXENT_JAR = os.path.join(BASE_DIR, "maxent.jar")
PRESENCE_DIR = os.path.join(BASE_DIR, "presence")
ENV_LAYERS_DIR = os.path.join(BASE_DIR, "env_layers")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def ensure_directories():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def find_presence_file(species_name: str) -> str:
    target = f"presence_{species_name.replace(' ', '_')}".lower()

    for root, _, files in os.walk(PRESENCE_DIR):
        for file in files:
            if target in file.lower():
                return os.path.join(root, file)

    raise FileNotFoundError(f"Presence file not found for species: {species_name}")


def clean_output_dir(path: str):
    if os.path.exists(path):
        shutil.rmtree(path)
    os.makedirs(path)


def run_maxent(species_name: str):

    ensure_directories()

    presence_file = find_presence_file(species_name)

    species_output_dir = os.path.join(OUTPUT_DIR, species_name.replace(" ", "_"))

    # 🔥 FIX: pulizia completa
    clean_output_dir(species_output_dir)

    command = [
        "xvfb-run", "-a",
        "java",
        "-Xmx1024m",
        "-jar",
        MAXENT_JAR,
        f"environmentallayers={ENV_LAYERS_DIR}",
        f"samplesfile={presence_file}",
        f"outputdirectory={species_output_dir}",
        "autorun",
        "nowarnings"
    ]

    print("\n=== RUNNING MAXENT ===\n")
    print(" ".join(command), "\n")

    process = subprocess.Popen(command)

    timeout = 120
    start = time.time()

    while True:
        if process.poll() is not None:
            break

        if time.time() - start > timeout:
            print("⚠️ Timeout reached → terminating MaxEnt")
            process.terminate()
            break

        time.sleep(2)

    return species_output_dir


def read_results(species_output_dir: str):

    results_file = os.path.join(species_output_dir, "maxentResults.csv")

    if not os.path.exists(results_file):
        raise FileNotFoundError("MaxEnt results not produced")

    df = pd.read_csv(results_file)

    return {
        "training_auc": float(df["Training AUC"].iloc[0])
        if "Training AUC" in df.columns else None
    }


def run_enm_analysis(species_name: str):

    output_dir = run_maxent(species_name)

    metrics = read_results(output_dir)

    return {
        "species": species_name,
        "metrics": metrics
    }


if __name__ == "__main__":
    print(run_enm_analysis("Alcedo atthis"))