"""
Massaciuccoli Digital Twin
ENM Engine — Stable + Safe Species Resolution (v14 FULL)
"""

import os
import subprocess
import pandas as pd
import shutil
import time
import numpy as np
import re
import requests

from tools.climate_loader import load_asc


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MAXENT_JAR = os.path.join(BASE_DIR, "maxent.jar")
PRESENCE_DIR = os.path.join(BASE_DIR, "presence")
ENV_LAYERS_DIR = os.path.join(BASE_DIR, "env_layers")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

DEBUG = True

STOPWORDS = {
    "the", "is", "of", "for", "where", "what",
    "about", "distribution", "habitat", "give", "can", "you"
}


# ======================================================
# DATASET INDEX
# ======================================================

def build_species_index():
    species_list = []

    for root, _, files in os.walk(PRESENCE_DIR):
        for file in files:
            if file.lower().endswith(".csv"):

                name = file.replace(".csv", "")
                name = name.replace("Presence_", "")
                name = name.replace("presence_", "")
                name = name.replace("_", " ").strip()

                species_list.append(name)

    return species_list


DATASET_SPECIES = build_species_index()


# ======================================================
# MATCHING
# ======================================================

def clean_tokens(text):
    return [
        t for t in re.findall(r"[a-z]+", text.lower())
        if t not in STOPWORDS and len(t) > 2
    ]


def match_exact(question):
    q = question.lower()

    for species in DATASET_SPECIES:
        if species.lower() in q:
            return species

    return None


def match_binomial(question):
    matches = re.findall(r"\b([A-Z][a-z]+ [a-z]+)\b", question)
    return matches[0] if matches else None


def match_fuzzy(question):

    tokens = clean_tokens(question)

    if DEBUG:
        print(f"[FUZZY] tokens: {tokens}")

    best_match = None
    best_score = 0

    for species in DATASET_SPECIES:

        name_tokens = species.lower().split()
        score = 0

        for t in tokens:
            if t in name_tokens:
                score += 3

        if tokens and name_tokens[0] in tokens:
            score += 5

        if score > best_score:
            best_score = score
            best_match = species

    if DEBUG:
        print(f"[FUZZY] best: {best_match} (score={best_score})")

    if best_score >= 3:
        return best_match

    return None


def match_gbif(question):

    try:
        url = "https://api.gbif.org/v1/species/search"
        params = {"q": question, "limit": 10}

        r = requests.get(url, params=params, timeout=5)
        data = r.json()

        for res in data.get("results", []):
            sci = res.get("canonicalName")
            rank = res.get("rank")

            if sci and rank == "SPECIES":
                for s in DATASET_SPECIES:
                    if sci.lower() == s.lower():
                        return sci

    except Exception:
        pass

    return None


# ======================================================
# RESOLUTION (FIXED)
# ======================================================

def resolve_species(question):

    print(f"\n[RESOLVE] {question}")

    # 1 exact
    s = match_exact(question)
    if s:
        return s, "exact"

    # 2 binomial (🔥 FIX)
    s = match_binomial(question)
    if s:
        if s in DATASET_SPECIES:
            print(f"[BINOMIAL] dataset match → {s}")
            return s, "binomial"
        else:
            print(f"[BINOMIAL] NOT in dataset → {s}")
            return None, None

    # 3 fuzzy
    s = match_fuzzy(question)
    if s:
        return s, "fuzzy"

    # 4 GBIF
    s = match_gbif(question)
    if s:
        return s, "gbif"

    return None, None


# ======================================================
# MAXENT
# ======================================================

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
        "nowarnings",
        "responsecurves=true",
        "jackknife=true"
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
            process.terminate()
            break

        time.sleep(2)

    return species_output_dir


# ======================================================
# RESULTS
# ======================================================

def extract_feature_contributions(df: pd.DataFrame):
    contributions = {}
    for col in df.columns:
        if "contribution" in col.lower():
            name = col.replace(" contribution", "")
            contributions[name] = float(df[col].iloc[0])
    return dict(sorted(contributions.items(), key=lambda x: -x[1]))


def read_results(species_output_dir: str):
    df = pd.read_csv(os.path.join(species_output_dir, "maxentResults.csv"))

    auc = float(df["Training AUC"].iloc[0]) if "Training AUC" in df.columns else None
    contributions = extract_feature_contributions(df)

    return {"training_auc": auc, "feature_contributions": contributions}


def load_suitability_map(species_output_dir: str):
    asc_file = next(
        (os.path.join(species_output_dir, f)
         for f in os.listdir(species_output_dir) if f.endswith(".asc")),
        None
    )
    data, header = load_asc(asc_file)
    return data, header


def detect_suitability_hotspots(data, top_percent=5):
    flat = data.flatten()
    flat = flat[~np.isnan(flat)]
    threshold = np.percentile(flat, 100 - top_percent)
    return {"threshold": float(threshold)}


# ======================================================
# PUBLIC API (🔥 QUESTA MANCAVA)
# ======================================================

def run_enm_analysis(question: str):

    species, method = resolve_species(question)

    if not species:
        raise ValueError("Could not resolve species name")

    if method == "fuzzy":
        print(f"⚠️ Using closest dataset match: {species}")

    if method == "gbif":
        print(f"⚠️ Using GBIF match: {species}")

    output_dir = run_maxent(species)

    metrics = read_results(output_dir)
    data, header = load_suitability_map(output_dir)
    hotspots = detect_suitability_hotspots(data)

    return {
        "species": species,
        "resolution_method": method,
        "metrics": metrics,
        "map": {"shape": data.shape},
        "hotspots": hotspots
    }