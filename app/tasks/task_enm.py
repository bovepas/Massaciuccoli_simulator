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
# TAXONOMIC GROUP LABEL
# ======================================================

def pretty_group(group: str):

    mapping = {

        "pesci_crostacei":
            "fish and crustaceans",

        "uccelli":
            "birds",

        "mammiferi":
            "mammals",

        "rettili_anfibi":
            "reptiles and amphibians",

        "insetti_molluschi":
            "invertebrates"
    }

    return mapping.get(group, group)

# ======================================================
# DISTRIBUTION DESCRIPTION
# ======================================================

def describe_distribution(
    pct_02,
    pct_05,
    pct_10,
    pct_12
):

    # ---------------------------------------------
    # Habitat extent
    # ---------------------------------------------

    if pct_02 >= 50:
        extent = "widespread"

    elif pct_02 >= 20:
        extent = "moderately distributed"

    else:
        extent = "restricted"

    # ---------------------------------------------
    # Core habitat
    # ---------------------------------------------

    if pct_12 >= 5:
        core = "extensive core habitat"

    elif pct_12 >= 1:
        core = "localized core habitat"

    else:
        core = "very limited core habitat"

    return (
        f"Suitable habitat appears {extent} across the "
        f"study area, while highly suitable areas form "
        f"{core}."
    )

def describe_driver_structure(
    driver_analysis
):

    structure = driver_analysis.get(
        "driver_structure"
    )

    dominant_driver = driver_analysis.get(
        "dominant_driver"
    )

    if (
        structure ==
        "single dominant driver"
    ):

        return (
            f"Habitat suitability is overwhelmingly "
            f"controlled by {clean_feature_name(dominant_driver)}."
        )

    elif (
        structure ==
        "dominant driver with secondary influences"
    ):

        return (
            f"{clean_feature_name(dominant_driver)} "
            f"is the primary environmental driver, "
            f"although other variables also contribute."
        )

    elif (
        structure ==
        "multiple co-dominant drivers"
    ):

        return (
            "Habitat suitability results from the "
            "interaction of multiple environmental "
            "drivers, with no single dominant factor."
        )

    return ""

def describe_fragmentation(
    fragmentation
):

    if fragmentation == "low":

        return (
            "Habitat connectivity is high and "
            "suitable areas remain largely connected."
        )

    elif fragmentation == "moderate":

        return (
            "Habitat connectivity is intermediate, "
            "with several partially separated areas."
        )

    elif fragmentation == "high":

        return (
            "Suitable habitat is strongly fragmented "
            "into isolated patches."
        )

    return ""

def describe_structure(
    structure
):

    if not structure:
        return ""

    return (
        f"Habitat structure is characterized by "
        f"{structure}."
    )


# ======================================================
# MAIN
# ======================================================

def handle_enm(question: str):

    print("\n========== ENM TASK START ==========\n")
    print("[DEBUG] Question:", question)
    asc_file = None
    try:

        # --------------------------------------------------
        # RUN ENM
        # --------------------------------------------------

        print("[DEBUG] Running ENM analysis...")

        result = run_enm_analysis(question)

        artifacts = result.get(
            "artifacts",
            {}
        )

        asc_file = artifacts.get(
            "asc_file"
        )

        print("[DEBUG] ENM result:")
        print(result)

        # --------------------------------------------------
        # EXTRACT
        # --------------------------------------------------

        species = result.get("species")
        method = result.get("resolution_method")

        metrics = result.get("metrics", {})
        auc = metrics.get("training_auc")

        contributions = metrics.get(
            "feature_contributions",
            {}
        )

        hotspots = result.get(
            "hotspots",
            {}
        )

        group = result.get(
            "group"
        )

        num_hotspots = hotspots.get(
            "num_hotspots"
        )

        largest_fraction = hotspots.get(
            "largest_hotspot_fraction"
        )

        fragmentation = hotspots.get(
            "fragmentation"
        )

        dominance_ratio = hotspots.get(
            "dominance_ratio"
        )
        
        structure = hotspots.get(
            "structure"
        )
        suitability = result.get(
            "suitability",
            {}
        )

        driver_analysis = result.get(
            "driver_analysis",
            {}
        )

        # --------------------------------------------------
        # PRE-COMPUTED INTERPRETATIONS 
        # --------------------------------------------------

        driver_summary = (
            describe_driver_structure(
                driver_analysis
            )
        )

        fragmentation_summary = (
            describe_fragmentation(
                fragmentation
            )
        )

        structure_summary = (
            describe_structure(
                structure
            )
        )

        # --------------------------------------------------
        # SUITABILITY STATS
        # --------------------------------------------------

        mean_suitability = suitability.get(
            "mean_suitability"
        )

        max_suitability = suitability.get(
            "max_suitability"
        )

        pct_02 = suitability.get(
            "pct_above_0_2T"
        )

        pct_05 = suitability.get(
            "pct_above_0_5T"
        )

        pct_10 = suitability.get(
            "pct_above_1_0T"
        )

        pct_12 = suitability.get(
            "pct_above_1_2T"
        )

        # --------------------------------------------------
        # CLEAN DRIVERS
        # --------------------------------------------------

        drivers = []

        clean_drivers = []

        if contributions:

            top_items = list(
                contributions.items()
            )[:4]

            for name, val in top_items:

                clean_name = clean_feature_name(
                    name
                )

                drivers.append(
                    f"{clean_name} ({round(val, 3)})"
                )

                clean_drivers.append(
                    (
                        clean_name,
                        round(val, 3)
                    )
                )

        # --------------------------------------------------
        # BASE INTERPRETATION
        # --------------------------------------------------

        interpretation_parts = []

        if clean_drivers:

            main_vars = [
                d[0]
                for d in clean_drivers[:2]
            ]

            interpretation_parts.append(

                f"Habitat suitability for "
                f"{species} is mainly influenced by "
                f"{' and '.join(main_vars)}, "
                f"indicating sensitivity to key "
                f"environmental gradients."
            )

        else:

            interpretation_parts.append(

                f"Habitat suitability for "
                f"{species} is determined by "
                f"environmental conditions "
                f"captured in the model."
            )

        # --------------------------------------------------
        # MODEL QUALITY
        # --------------------------------------------------

        if auc:

            interpretation_parts.append(

                f"Model performance is strong "
                f"(AUC = {round(auc, 3)})."
            )

        # --------------------------------------------------
        # SPATIAL SUMMARY
        # --------------------------------------------------

        if pct_10 is not None:

            interpretation_parts.append(

                f"Approximately {pct_10}% of the "
                f"study area exceeds the hotspot "
                f"threshold, while {pct_12}% "
                f"represents highly suitable "
                f"core habitat."
            )

        # --------------------------------------------------
        # DISTRIBUTION DESCRIPTION
        # --------------------------------------------------

        if pct_02 is not None:

            interpretation_parts.append(

                describe_distribution(
                    pct_02,
                    pct_05,
                    pct_10,
                    pct_12
                )
            )

        # --------------------------------------------------
        # HOTSPOT STRUCTURE
        # --------------------------------------------------

        if num_hotspots is not None:

            interpretation_parts.append(

                f"Suitable habitat is organized into "
                f"{num_hotspots} major hotspot areas."
            )

        if largest_fraction is not None:

            interpretation_parts.append(

                f"The largest hotspot contains "
                f"{round(largest_fraction * 100, 1)}% "
                f"of all suitable habitat."
            )

        if fragmentation_summary:

            interpretation_parts.append(
                fragmentation_summary
            )

        if structure_summary:

            interpretation_parts.append(
                structure_summary
            )

        if group:

            interpretation_parts.append(

                f"The species belongs to the "
                f"{pretty_group(group)} taxonomic group."
            )


        # --------------------------------------------------
        # RAG ENRICHMENT
        # --------------------------------------------------



        print("[DEBUG] Calling RAG ENM...")

        model_summary = f"""
        AUC: {round(auc,3)}

        Suitable habitat:
        {pct_10}% of study area

        Core habitat:
        {pct_12}% of study area

        Hotspots:
        {num_hotspots}

        Largest hotspot:
        {round(largest_fraction * 100,1)}%

        Habitat structure:
        {structure_summary}

        Connectivity:
        {fragmentation_summary}

        Driver interpretation:
        {driver_summary}
        """

        rag_text = generate_enm_explanation(

            question=question,

            drivers=drivers,

            species=species,

            model_summary=model_summary,

            driver_analysis=driver_analysis

        )

        print("[DEBUG] RAG output:", rag_text)

        interpretation_parts.append(
            rag_text
        )

        interpretation = " ".join(
            interpretation_parts
        )

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        output = {

            "type": "enm",

            "summary":
                f"Species distribution model "
                f"for {species}",

            "data": {

                "species":
                    species,

                "resolution_method":
                    method,
                "group":
                    group,
                
                "num_hotspots":
                    num_hotspots,

                "largest_hotspot_fraction":
                    largest_fraction,

                "dominance_ratio":
                    dominance_ratio,
                
                "fragmentation":
                    fragmentation,

                "structure":
                    structure,

                "training_auc":
                    round(auc, 3)
                    if auc else None,

                "mean_suitability":
                    mean_suitability,

                "max_suitability":
                    max_suitability,

                "pct_above_0_2T":
                    pct_02,

                "pct_above_0_5T":
                    pct_05,

                "pct_above_1_0T":
                    pct_10,

                "pct_above_1_2T":
                    pct_12,

                "top_features":
                    clean_drivers,

                "hotspot_threshold":
                    hotspots.get("threshold")
            },

            "drivers":
                drivers,

            "interpretation":
                interpretation,

            "downloads": {
                "asc_file": asc_file
            },

            "meta": {
                "source":
                    "maxent_enm"
            }
        }

        print(
            "\n========== ENM TASK END ==========\n"
        )

        return output

    except Exception as e:

        print(
            "[ERROR] ENM failed:",
            str(e)
        )

        return {

            "type":
                "enm",

            "summary":
                "ENM analysis failed",

            "data":
                {},

            "drivers":
                [],

            "interpretation":
                str(e),

            "meta": {
                "source":
                    "enm_error"
            },

            "downloads": {
                "asc_file": asc_file
            }
            
        }