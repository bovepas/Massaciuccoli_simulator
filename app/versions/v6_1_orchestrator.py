"""
Massaciuccoli Digital Twin
Orchestrator v29 — ENM Spatial Final Fix
"""

import re
import numpy as np

from versions.v6_main import route_question
from versions.v7_dynamic_model import run_temporal_simulation
from knowledge.rag_pipeline import call_llm, generate_answer
from enm.enm_engine import run_enm_analysis, load_suitability_map


# ======================================================
# CLEAN INPUT
# ======================================================

def clean_question(q: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s°%.,-]", "", q)


# ======================================================
# SPECIES EXTRACTION
# ======================================================

def extract_species_name(question: str) -> str:

    words = question.split()

    for i in range(len(words) - 1):
        if words[i][0].isupper() and words[i+1][0].isupper():
            return words[i] + " " + words[i+1]

    return "Alcedo atthis"


# ======================================================
# SPATIAL ANALYSIS
# ======================================================

def analyze_spatial_pattern(result):

    species_name = result["species"].replace(" ", "_")
    path = f"enm/output/{species_name}"

    data, _ = load_suitability_map(path)
    threshold = result["hotspots"]["threshold"]

    high_mask = data >= threshold
    coords = np.argwhere(high_mask)

    if len(coords) == 0:
        return {
            "zone": "unknown",
            "dispersion": "none",
            "gradient": "none"
        }

    rows, cols = data.shape

    centroid = coords.mean(axis=0)

    y_norm = centroid[0] / rows
    x_norm = centroid[1] / cols

    # =========================
    # LAT
    # =========================
    if y_norm < 0.4:
        lat = "southern"
    elif y_norm < 0.6:
        lat = "central"
    else:
        lat = "northern"

    # =========================
    # LON
    # =========================
    if x_norm < 0.4:
        lon = "western"
    elif x_norm < 0.6:
        lon = "central"
    else:
        lon = "eastern"

    # =========================
    # FIX: evitare "central central"
    # =========================
    if lat == "central" and lon == "central":
        zone = "central"
    else:
        zone = f"{lat} {lon}"

    # =========================
    # DISPERSION
    # =========================
    spread = coords.std(axis=0).mean()

    if spread < 15:
        dispersion = "highly localized"
    elif spread < 40:
        dispersion = "clustered"
    else:
        dispersion = "broadly distributed"

    # =========================
    # GRADIENT
    # =========================
    y_std = coords[:, 0].std()
    x_std = coords[:, 1].std()

    if y_std > x_std * 1.2:
        gradient = "north–south"
    elif x_std > y_std * 1.2:
        gradient = "east–west"
    else:
        gradient = "no clear directional pattern"

    return {
        "zone": zone,
        "dispersion": dispersion,
        "gradient": gradient
    }


# ======================================================
# DETERMINISTIC DESCRIPTION
# ======================================================

def build_spatial_description(species, spatial):

    sentence1 = f"Habitat suitability for {species} is {spatial['dispersion']} across the {spatial['zone']} portion of the basin."

    if spatial["gradient"] == "no clear directional pattern":
        sentence2 = "No dominant spatial gradient is observed."
    else:
        sentence2 = f"The spatial pattern follows a {spatial['gradient']} gradient."

    return sentence1 + " " + sentence2


# ======================================================
# SCIENTIFIC SUMMARY
# ======================================================

def build_enm_summary(metrics, hotspots):

    contributions = metrics["feature_contributions"]
    top_drivers = list(contributions.items())[:3]

    drivers_text = ", ".join(
        [f"{name} ({value:.1f}%)" for name, value in top_drivers]
    )

    return (
        f"Model performance is high (AUC = {metrics['training_auc']:.3f}). "
        f"The main environmental drivers are {drivers_text}. "
        f"High suitability areas are defined by a threshold of {hotspots['threshold']:.3f}."
    )


# ======================================================
# MAIN
# ======================================================

def handle_question(question: str):

    print(f"\n❓ Question: {question}")

    question = clean_question(question)

    decision = route_question(question)
    route = decision["route"]

    print(f"➡️ ROUTE: {route}")

    # ======================================================
    # CLIMATE
    # ======================================================

    if route == "dynamic_model":

        rcp = "rcp45"
        year = "2050"

        base, future, hotspots = run_temporal_simulation(rcp, year)

        delta = round(future["mean_risk"] - base["mean_risk"], 3)

        return f"""
📈 Climate-driven Simulation

Initial risk: {base["mean_risk"]}
Final risk: {future["mean_risk"]}
Δ Risk: {delta}

Hotspots: {hotspots["share"]*100:.1f}%
"""

    # ======================================================
    # ENM
    # ======================================================

    if route == "enm":

        species = extract_species_name(question)

        print(f"🧬 Running ENM for: {species}")

        result = run_enm_analysis(species)

        metrics = result["metrics"]
        hotspots = result["hotspots"]

        spatial = analyze_spatial_pattern(result)

        summary = build_enm_summary(metrics, hotspots)

        spatial_text = build_spatial_description(
            species,
            spatial
        )

        return f"""
🧬 Species Distribution Model

Species: {species}

📊 Model Performance
AUC: {metrics['training_auc']:.3f}

🌿 Main Drivers
{metrics['feature_contributions']}

🔥 Habitat Hotspots
Top suitability threshold: {hotspots['threshold']:.3f}

📊 Scientific summary
{summary}

🧭 Spatial distribution
{spatial_text}
"""

    # ======================================================
    # RAG
    # ======================================================

    if route == "llm_only":
        return generate_answer(question)

    return "Route not handled."


# ======================================================
# CLI
# ======================================================

def run_cli():

    print("\n=== Digital Twin v29 — ENM Spatial Final ===\n")

    while True:
        q = input("Ask a question: ")

        if q.lower() in ["exit", "quit"]:
            break

        print("\nProcessing...\n")
        ans = handle_question(q)

        print("\n=== Final Answer ===\n")
        print(ans)
        print("\n---------------------------\n")


if __name__ == "__main__":
    run_cli()