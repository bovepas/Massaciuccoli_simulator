"""
Massaciuccoli Digital Twin
ENM Engine — Stable + Safe Species Resolution (v16)
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
# SCENARIO PARSING
# ======================================================

def parse_scenario(question):

    q = question.lower()

    future_keywords = [
        "future",
        "futuro",

        "2050",
        "2100",

        "climate change",
        "cambiamento climatico",
        "warming",
        "global warming",
        "climatico",
        "climate",
        "scenario",

        "rcp"
    ]

    future = any(
        k in q
        for k in future_keywords
    )

    if not future:

        return {

            "future": False,

            "year": None,

            "rcp": None,

            "env_layers":
                ENV_LAYERS_DIR,

            "default_used": False
        }

    # ----------------------------------
    # YEAR
    # ----------------------------------

    if "2100" in q:

        year = 2100

    else:

        year = 2050

    # ----------------------------------
    # RCP
    # ----------------------------------

    if (
        "4.5" in q
        or "rcp45" in q
        or "rcp 4.5" in q
    ):

        rcp = "4.5"

    else:

        rcp = "8.5"

    # ----------------------------------
    # DEFAULT?
    # ----------------------------------

    default_used = (
        "2050" not in q
        and
        "2100" not in q
        and
        "8.5" not in q
        and
        "4.5" not in q
    )

    env_layers = os.path.join(

        BASE_DIR,

        f"env_layers_{year}_rcp"
        f"{rcp.replace('.', '')}"
    )

    return {

        "future": True,

        "year": year,

        "rcp": rcp,

        "env_layers":
            env_layers,

        "default_used":
            default_used
    }

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


def run_maxent(species_name: str,env_layers_dir: str):

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

        f"environmentallayers={env_layers_dir}",

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

    return data, header, asc_file


# ======================================================
# SUITABILITY STATISTICS
# ======================================================

def compute_suitability_stats(
    data,
    threshold
):
    #print("RAW NAN:", np.isnan(data).sum())


    flat = data.flatten()
    flat = flat[flat != -9999]
    flat = flat[~np.isnan(flat)]

    #print("VALID PIXELS:", len(flat))
    #print("FILTERED NAN:", np.isnan(flat).sum())

    #print("MIN VALID:", np.min(flat))
    #print("MAX VALID:", np.max(flat))


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

        mean_hotspot = float(
            np.mean(hotspot_sizes)
        )

        total_hotspot_pixels = sum(
            hotspot_sizes
        )

        largest_fraction = (
            largest_hotspot /
            total_hotspot_pixels
        )

        # ------------------------------------------
        # DOMINANCE RATIO
        # ------------------------------------------

        sorted_sizes = sorted(
            hotspot_sizes,
            reverse=True
        )

        if len(sorted_sizes) >= 2:

            dominance_ratio = (
                sorted_sizes[0] /
                sorted_sizes[1]
            )

        elif len(sorted_sizes) == 1:

            dominance_ratio = float("inf")

        else:

            dominance_ratio = 0

    else:

        largest_hotspot = 0

        mean_hotspot = 0

        largest_fraction = 0

        dominance_ratio = 0

    # --------------------------------------------------
    # FRAGMENTATION
    # --------------------------------------------------

    if largest_fraction >= 0.70:

        fragmentation = "low"

    elif largest_fraction >= 0.40:

        fragmentation = "moderate"

    else:

        fragmentation = "high"

    # --------------------------------------------------
    # HABITAT STRUCTURE
    # --------------------------------------------------

    if num_hotspots == 0:

        structure = "no major hotspots"

    elif largest_fraction >= 0.90:

        structure = "single dominant hotspot"

    elif largest_fraction >= 0.70:

        structure = (
            "dominant hotspot with "
            "secondary habitat nuclei"
        )

    elif largest_fraction >= 0.40:

        structure = (
            "multiple major hotspots"
        )

    else:

        structure = (
            "highly fragmented habitat"
        )

    return {

        "threshold":
            float(threshold),

        "num_hotspots":
            num_hotspots,

        "largest_hotspot_pixels":
            largest_hotspot,

        "mean_hotspot_pixels":
            round(mean_hotspot, 1),

        "largest_hotspot_fraction":
            round(largest_fraction, 3),

        "dominance_ratio":
            round(dominance_ratio, 2)
            if dominance_ratio != float("inf")
            else 999,

        "fragmentation":
            fragmentation,

        "structure":
            structure
    }

# ======================================================
# DRIVER ANALYSIS
# ======================================================

def classify_driver_structure(
    contributions
):

    if not contributions:

        return {

            "dominant_driver": None,

            "driver_ratio": 0,

            "driver_structure":
                "unknown"
        }

    sorted_drivers = sorted(
        contributions.items(),
        key=lambda x: x[1],
        reverse=True
    )

    dominant_driver = sorted_drivers[0][0]
    dominant_value = sorted_drivers[0][1]

    if len(sorted_drivers) >= 2:

        second_value = sorted_drivers[1][1]

        if second_value > 0:

            driver_ratio = (
                dominant_value /
                second_value
            )

        else:

            driver_ratio = 999

    else:

        driver_ratio = 999

    if driver_ratio >= 5:

        driver_structure = (
            "single dominant driver"
        )

    elif driver_ratio >= 2:

        driver_structure = (
            "dominant driver with "
            "secondary influences"
        )

    else:

        driver_structure = (
            "multiple co-dominant drivers"
        )

    return {

        "dominant_driver":
            dominant_driver,

        "driver_ratio":
            round(driver_ratio, 2),

        "driver_structure":
            driver_structure
    }

def run_single_enm(
    species,
    method,
    env_layers_dir
):

    output_dir, taxonomic_group = (
        run_maxent(
            species,
            env_layers_dir
        )
    )

    metrics = read_results(output_dir)

    driver_analysis = (
        classify_driver_structure(
            metrics.get(
                "feature_contributions",
                {}
            )
        )
    )

    data, header, asc_path = (
        load_suitability_map(
            output_dir
        )
    )

    fixed_threshold = (
        metrics.get(
            "fixed_threshold"
        )
    )

    hotspots = (
        detect_suitability_hotspots(
            data,
            fixed_threshold
        )
    )

    suitability = (
        compute_suitability_stats(
            data,
            fixed_threshold
        )
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

        "hotspots":
            hotspots,

        "driver_analysis":
            driver_analysis,

        "suitability":
            suitability,

        "map": {
            "shape":
                data.shape
        },

        "artifacts": {
            "asc_file":
                asc_path
        }
    }


def compare_scenarios(
    baseline,
    future
):

    habitat_delta = round(

        future["suitability"]["pct_above_1_0T"]

        -

        baseline["suitability"]["pct_above_1_0T"],

        2
    )

    core_delta = round(

        future["suitability"]["pct_above_1_2T"]

        -

        baseline["suitability"]["pct_above_1_2T"],

        2
    )

    hotspot_delta = (

        future["hotspots"]["num_hotspots"]

        -

        baseline["hotspots"]["num_hotspots"]
    )

    return {

        "habitat_delta":
            habitat_delta,

        "core_delta":
            core_delta,

        "hotspot_delta":
            hotspot_delta
    }


# ======================================================
# PUBLIC API
# ======================================================

def run_enm_analysis(question: str):

    species, method = resolve_species(
        question
    )

    scenario = parse_scenario(question)

    comparison = None

    print("\n[SCENARIO]")
    print(scenario)

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

    # --------------------------------------------------
    # CURRENT CONDITIONS
    # --------------------------------------------------

    if not scenario["future"]:

        result = run_single_enm(
            species,
            method,
            ENV_LAYERS_DIR
        )

    # --------------------------------------------------
    # FUTURE SCENARIO
    # --------------------------------------------------

    else:

        print(
            "\n[ENM] Running baseline "
            "scenario..."
        )

        baseline_result = run_single_enm(
            species,
            method,
            ENV_LAYERS_DIR
        )

        print(
            "\n[ENM] Running future "
            "scenario..."
        )

        future_result = run_single_enm(
            species,
            method,
            scenario["env_layers"]
        )

        comparison = compare_scenarios(
            baseline_result,
            future_result
        )

        print(
            "\n[COMPARISON]"
        )

        print(comparison)

        result = future_result

    # --------------------------------------------------
    # ADD METADATA
    # --------------------------------------------------

    result["scenario"] = scenario

    result["comparison"] = comparison

    return result