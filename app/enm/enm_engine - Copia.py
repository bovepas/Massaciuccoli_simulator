"""
Massaciuccoli Digital Twin
ENM Engine — Stable + Safe Species Resolution (v15)
"""

import os
import subprocess
import pandas as pd
import shutil
import time
import numpy as np
import re
import requests
from scipy import ndimage

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

    matches = re.findall(
        r"\b([A-Z][a-z]+ [a-z]+)\b",
        question
    )

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
        print(
            f"[FUZZY] best: "
            f"{best_match} "
            f"(score={best_score})"
        )

    if best_score >= 3:
        return best_match

    return None


def match_gbif(question):

    try:

        url = "https://api.gbif.org/v1/species/search"

        params = {
            "q": question,
            "limit": 10
        }

        r = requests.get(
            url,
            params=params,
            timeout=5
        )

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
# RESOLUTION
# ======================================================

def resolve_species(question):

    print(f"\n[RESOLVE] {question}")

    # exact

    s = match_exact(question)

    if s:
        return s, "exact"

    # binomial

    s = match_binomial(question)

    if s:

        if s in DATASET_SPECIES:

            print(
                f"[BINOMIAL] dataset "
                f"match → {s}"
            )

            return s, "binomial"

        else:

            print(
                f"[BINOMIAL] NOT "
                f"in dataset → {s}"
            )

            return None, None

    # fuzzy

    s = match_fuzzy(question)

    if s:
        return s, "fuzzy"

    # GBIF

    s = match_gbif(question)

    if s:
        return s, "gbif"

    return None, None


# ======================================================
# MAXENT
# ======================================================

def ensure_directories():

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True
    )


def find_presence_file(species_name: str):

    target = (
        f"presence_"
        f"{species_name.replace(' ', '_')}"
    ).lower()

    for root, _, files in os.walk(PRESENCE_DIR):

        for file in files:

            if target in file.lower():

                taxonomic_group = os.path.basename(root)

                return (
                    os.path.join(
                        root,
                        file
                    ),
                    taxonomic_group
                )

    raise FileNotFoundError(
        f"Presence file not found "
        f"for species: {species_name}"
    )


def clean_output_dir(path: str):

    if os.path.exists(path):
        shutil.rmtree(path)

    os.makedirs(path)


def run_maxent(species_name: str):

    ensure_directories()

    presence_file, taxonomic_group = find_presence_file(
        species_name
    )

    species_output_dir = os.path.join(
        OUTPUT_DIR,
        species_name.replace(" ", "_")
    )

    clean_output_dir(species_output_dir)

    command = [

        "xvfb-run",
        "-a",

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

    return species_output_dir, taxonomic_group


# ======================================================
# RESULTS
# ======================================================

def extract_feature_contributions(df):

    contributions = {}

    for col in df.columns:

        if "contribution" in col.lower():

            name = col.replace(
                " contribution",
                ""
            )

            contributions[name] = float(
                df[col].iloc[0]
            )

    return dict(
        sorted(
            contributions.items(),
            key=lambda x: -x[1]
        )
    )


def read_results(species_output_dir: str):

    csv_file = os.path.join(
        species_output_dir,
        "maxentResults.csv"
    )

    df = pd.read_csv(csv_file)

    # --------------------------------------------------
    # AUC
    # --------------------------------------------------

    auc = (

        float(df["Training AUC"].iloc[0])

        if "Training AUC" in df.columns

        else None
    )

    # --------------------------------------------------
    # CONTRIBUTIONS
    # --------------------------------------------------

    contributions = extract_feature_contributions(
        df
    )

    # --------------------------------------------------
    # FIXED CUMULATIVE VALUE 10
    # --------------------------------------------------

    threshold_col = (
        "Fixed cumulative value 10 "
        "Cloglog threshold"
    )

    area_col = (
        "Fixed cumulative value 10 area"
    )

    omission_col = (
        "Fixed cumulative value 10 "
        "training omission"
    )

    fixed_threshold = (

        float(df[threshold_col].iloc[0])

        if threshold_col in df.columns

        else None
    )

    fixed_area = (

        float(df[area_col].iloc[0])

        if area_col in df.columns

        else None
    )

    fixed_omission = (

        float(df[omission_col].iloc[0])

        if omission_col in df.columns

        else None
    )

    return {

        "training_auc":
            auc,

        "feature_contributions":
            contributions,

        "fixed_threshold":
            fixed_threshold,

        "fixed_area":
            fixed_area,

        "fixed_training_omission":
            fixed_omission
    }


def load_suitability_map(species_output_dir: str):

    asc_file = next(

        (
            os.path.join(
                species_output_dir,
                f
            )

            for f in os.listdir(
                species_output_dir
            )

            if f.endswith(".asc")
        ),

        None
    )

    data, header = load_asc(asc_file)

    return data, header


# ======================================================
# SUITABILITY STATISTICS
# ======================================================

def compute_suitability_stats(
    data,
    threshold
):

    flat = data[data != -9999].flatten()

    total = len(flat)

    mean_suitability = float(
        np.mean(flat)
    )

    max_suitability = float(
        np.max(flat)
    )

    pct_above_02 = (

        np.sum(flat >= threshold * 0.2)

        / total

        * 100
    )

    pct_above_05 = (

        np.sum(flat >= threshold * 0.5)

        / total

        * 100
    )

    pct_above_10 = (

        np.sum(flat >= threshold)

        / total

        * 100
    )

    pct_above_12 = (

        np.sum(flat >= threshold * 1.2)

        / total

        * 100
    )

    return {

        "mean_suitability":
            round(mean_suitability, 4),

        "max_suitability":
            round(max_suitability, 4),

        "pct_above_0_2T":
            round(pct_above_02, 2),

        "pct_above_0_5T":
            round(pct_above_05, 2),

        "pct_above_1_0T":
            round(pct_above_10, 2),

        "pct_above_1_2T":
            round(pct_above_12, 2)
    }


# ======================================================
# HOTSPOTS
# ======================================================

def detect_suitability_hotspots(
    data,
    threshold
):

    MIN_HOTSPOT_PIXELS = 25

    valid_mask = data != -9999
    binary = (data >= threshold) & valid_mask

    labels, num_labels = ndimage.label(binary)

    hotspot_sizes = []

    for hotspot_id in range(1, num_labels + 1):

        size = int(np.sum(labels == hotspot_id))

        if size >= MIN_HOTSPOT_PIXELS:
            hotspot_sizes.append(size)

    num_hotspots = len(hotspot_sizes)

    if hotspot_sizes:

        largest_hotspot = max(hotspot_sizes)
        mean_hotspot = float(np.mean(hotspot_sizes))
        total_hotspot_pixels = sum(hotspot_sizes)

        largest_fraction = (
            largest_hotspot / total_hotspot_pixels
        )

    else:

        largest_hotspot = 0
        mean_hotspot = 0
        largest_fraction = 0

    if largest_fraction >= 0.70:
        fragmentation = "low"
    elif largest_fraction >= 0.40:
        fragmentation = "moderate"
    else:
        fragmentation = "high"

    return {
        "threshold": float(threshold),
        "num_hotspots": num_hotspots,
        "largest_hotspot_pixels": largest_hotspot,
        "mean_hotspot_pixels": round(mean_hotspot,1),
        "largest_hotspot_fraction": round(largest_fraction,3),
        "fragmentation": fragmentation
    }


# ======================================================
# PUBLIC API
# ======================================================

def run_enm_analysis(question: str):

    species, method = resolve_species(
        question
    )

    if not species:
        raise ValueError(
            "Could not resolve species name"
        )

    if method == "fuzzy":

        print(
            f"⚠️ Using closest "
            f"dataset match: {species}"
        )

    if method == "gbif":

        print(
            f"⚠️ Using GBIF "
            f"match: {species}"
        )

    output_dir, taxonomic_group = run_maxent(species)

    metrics = read_results(output_dir)

    data, header = load_suitability_map(
        output_dir
    )

    fixed_threshold = metrics.get(
        "fixed_threshold"
    )

    hotspots = detect_suitability_hotspots(
        data,
        fixed_threshold
    )

    suitability = compute_suitability_stats(
        data,
        fixed_threshold
    )

    return {

        "species":
            species,

        "group":
            taxonomic_group,

        "resolution_method":
            method,

        "metrics":
            metrics,

        "map": {
            "shape":
                data.shape
        },

        "hotspots":
            hotspots,

        "suitability":
            suitability
    }