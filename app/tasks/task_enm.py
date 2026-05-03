"""
Massaciuccoli Digital Twin
Task: ENM (WITH RAG)
"""

from enm.enm_engine import run_enm_analysis
from knowledge.rag_enm import generate_enm_explanation


# ======================================================
# FEATURE NAME CLEANING
# ======================================================

def clean_feature_name(name: str) -> str:

    name = name.lower()

    if "temperature" in name:
        return "temperature"

    if "precipitation" in name:
        return "precipitation"

    if "conductivity" in name:
        return "water conductivity"

    return name.replace("_", " ")


# ======================================================
# MAIN
# ======================================================

def handle_enm(question: str):

    print("\n========== ENM TASK START ==========\n")
    print("[DEBUG] Question:", question)

    try:
        # --------------------------------------------------
        # RUN ENM
        # --------------------------------------------------
        print("[DEBUG] Running ENM analysis...")

        result = run_enm_analysis(question)

        print("[DEBUG] ENM result:")
        print(result)

        # --------------------------------------------------
        # EXTRACT
        # --------------------------------------------------

        species = result.get("species")
        method = result.get("resolution_method")

        metrics = result.get("metrics", {})
        auc = metrics.get("training_auc")

        contributions = metrics.get("feature_contributions", {})
        hotspots = result.get("hotspots", {})

        # --------------------------------------------------
        # CLEAN DRIVERS
        # --------------------------------------------------

        drivers = []
        clean_drivers = []

        if contributions:
            top_items = list(contributions.items())[:4]

            for name, val in top_items:
                clean_name = clean_feature_name(name)

                drivers.append(f"{clean_name} ({round(val, 3)})")
                clean_drivers.append((clean_name, round(val, 3)))

        # --------------------------------------------------
        # BASE INTERPRETATION
        # --------------------------------------------------

        if clean_drivers:
            main_vars = [d[0] for d in clean_drivers[:2]]
            interpretation = (
                f"Habitat suitability for {species} is mainly influenced by {' and '.join(main_vars)}, indicating sensitivity to key environmental gradients."
            )
        else:
            interpretation = f"Habitat suitability for {species} is determined by environmental conditions captured in the model."

        if auc:
            interpretation += f" Model performance is strong (AUC = {round(auc, 3)})."

        # --------------------------------------------------
        # 🔥 RAG ENRICHMENT
        # --------------------------------------------------

        print("[DEBUG] Calling RAG ENM...")

        rag_text = generate_enm_explanation(
            question=question,
            drivers=drivers,
            species=species
        )

        print("[DEBUG] RAG output:", rag_text)

        interpretation += " " + rag_text

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        output = {
            "type": "enm",

            "summary": f"Species distribution model for {species}",

            "data": {
                "species": species,
                "resolution_method": method,
                "training_auc": round(auc, 3) if auc else None,
                "top_features": clean_drivers,
                "hotspot_threshold": hotspots.get("threshold")
            },

            "drivers": drivers,

            "interpretation": interpretation,

            "meta": {"source": "maxent_enm"}
        }

        print("\n========== ENM TASK END ==========\n")

        return output

    except Exception as e:

        print("[ERROR] ENM failed:", str(e))

        return {
            "type": "enm",
            "summary": "ENM analysis failed",
            "data": {},
            "drivers": [],
            "interpretation": str(e),
            "meta": {"source": "enm_error"}
        }