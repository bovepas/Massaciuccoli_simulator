# -*- coding: utf-8 -*-

import re
import os
import glob

from utils.logger import (
    log_section,
    log_question,
    log_route
)

from utils.feature_parser import parse_features


# ======================================================
# NORMALIZATION
# ======================================================

def normalize(q: str) -> str:
    return q.lower().strip()


# ======================================================
# DATA DETECTION
# ======================================================

DATA_KEYWORDS = [
    "data",
    "dataset",
    "value",
    "values",
    "numbers",
    "measurements",
    "records",
    "time series",
    "latest",
    "current value",
    "retrieve",
    "get data",
    "show data"
]


def is_data_query(q: str):

    return any(k in q for k in DATA_KEYWORDS)


# ======================================================
# TARGET DETECTION
# ======================================================

ECOSYSTEM_STATE_TERMS = [

    "ecosystem risk",
    "ecosystem health",
    "ecosystem condition",
    "ecosystem functioning",
    "ecosystem resilience",
    "ecosystem vulnerability"

]

def detect_target(q: str):

    risk_patterns = [
        "risk level",
        "risk score",
        "risk"
    ]

    if (
        any(p in q for p in risk_patterns)
        or any(p in q for p in ECOSYSTEM_STATE_TERMS)
    ):
        return "risk"
    
    # NEW
    if any(
        p in q
        for p in [
            "which intervention",
            "risk mitigation",
            "mitigation strategy",
            "mitigation strategies"
        ]
    ):
        return "risk"

    if "ecosystem" in q:
        return "ecosystem"

    if "ecosystem" in q:
        return "ecosystem"

    variable_patterns = [
        "temperature",
        "precipitation",
        "biodiversity",
        "species richness",
        "tree cover",
        "grassland",
        "evapotranspiration",
        "land use",
        "land cover",
        "productivity"
    ]

    for v in variable_patterns:

        if v in q:
            return "variable"

    return "unknown"


# ======================================================
# DRIVER ANALYSIS
# ======================================================

def asks_driver_analysis(q: str):

    patterns = [
        "drivers",
        "drive",
        "driving",
        "important",
        "importance",
        "influential",
        "influence",
        "influences",
        "main factors",
        "top factors",
        "top variables",
        "which factors",
        "which variables",
        "what drives",
        "associated with",
        "strongest impact",
        "greatest impact",
        "largest impact",
        "highest impact",
        "priority",
        "priorities",
        "prioritize",
        "prioritized",
        "should be prioritized",
        "explains most",
        "best explains",
        "most important for",
        "contributes most",
        "contribute most"
    ]

    if any(p in q for p in patterns):
        return True

    return False

    # --------------------------------------------------
    # SEMANTIC RANKING STRUCTURE
    # --------------------------------------------------

    ranking_patterns = [
        "most",
        "top",
        "main",

        "strongest",
        "greatest",
        "highest",
        "largest"
    ]

    variable_patterns = [
        "variables",
        "factors",
        "drivers"
    ]

    if (
        any(r in q for r in ranking_patterns)
        and any(v in q for v in variable_patterns)
    ):
        return True

    return False


# ======================================================
# RISK ESTIMATION
# ======================================================

def asks_risk_estimation(q: str):

    patterns = [
        "risk level",
        "ecosystem risk",
        "ecosystem health",
        "ecosystem condition",
        "ecosystem functioning",
        "ecosystem resilience",
        "ecosystem vulnerability",
        "estimate risk",
        "estimate the ecosystem risk",
        "assess ecosystem risk",
        "predict ecosystem risk",
        "what is the risk",
        "risk score",
        "environmental conditions",
        "state of the ecosystem",
        "current ecosystem state"
    ]

    return any(p in q for p in patterns)




# ======================================================
# COMPARISON DETECTION
# ======================================================

def has_comparison(q: str):

    patterns = [
        " vs ",
        " versus ",
        "compare",
        "comparison",
        "which is worse",
        "which is better",
        "which contributes more",
        "which contributes most",
        "which has greater impact",
        "which has the greater impact",
        "which has stronger impact",
        "which has a stronger effect",
        "which is more effective",
        "more effective",
        "greater ecological impact"
    ]

    if any(p in q for p in patterns):
        return True

    if re.search(r"\bor\b.*[\+\-]?\d", q):
        return True

    return False


# ======================================================
# DEPENDENCY DETECTION
# ======================================================

def asks_dependency(q: str):

    # --------------------------------------------------
    # EXCLUDE RANKING / IMPORTANCE QUESTIONS
    # --------------------------------------------------

    ranking_patterns = [

        "which variables",
        "which environmental variables",
        "which factors",
        "top variables",
        "top factors",
        "main factors",
        "most important",
        "most influence",
        "contributes most",
        "contribute most",
        "strongest impact",
        "greatest impact",
        "largest impact",
        "highest impact",
        "three environmental variables"

    ]

    if any(p in q for p in ranking_patterns):
        return False

    # --------------------------------------------------
    # RELATIONSHIP KEYWORDS
    # --------------------------------------------------

    dependency_patterns = [

        "affect",
        "influence",
        "impact",
        "effect",
        "cause",
        "causes",
        "determine",
        "determines",
        "control",
        "controls"

    ]

    # --------------------------------------------------
    # EXPLICIT RELATIONSHIP STRUCTURES
    # --------------------------------------------------

    relationship_patterns = [

        r"how is .* associated with .*",
        r"how are .* associated with .*",

        r"how is .* related to .*",
        r"how are .* related to .*",

        r"how is .* linked to .*",
        r"how are .* linked to .*",

        r"how is .* correlated with .*",
        r"how are .* correlated with .*",

        r"what is the relationship between .* and .*",

        r"how does .* affect .*",
        r"how does .* influence .*",
        r"how does .* impact .*",

        r"how do .* affect .*",
        r"how do .* influence .*",
        r"how do .* impact .*",

        r"how could .* affect .*",
        r"how could .* influence .*",
        r"how could .* impact .*"

    ]

    if any(
        re.search(pattern, q)
        for pattern in relationship_patterns
    ):
        return True

    # --------------------------------------------------
    # FALLBACK:
    # SINGLE RELATIONSHIP VERBS
    # --------------------------------------------------

    if any(
        p in q
        for p in dependency_patterns
    ):
        return True

    if re.search(
        r"how does .* change",
        q
    ):
        return True

    return False


# ======================================================
# DELTA DETECTION
# ======================================================

def asks_delta_reasoning(q: str):

    patterns = [
        "change from",
        "goes from",
        "from",
        "to"
    ]

    return any(p in q for p in patterns)


# ======================================================
# BASELINE REFERENCES
# ======================================================

def references_baseline(q: str):

    baseline_patterns = [
        "baseline",
        "current",
        "present",
        "today"
    ]

    return any(p in q for p in baseline_patterns)

# ======================================================
# KNOWN ENM SPECIES
# ======================================================

def load_enm_species():

    species = set()

    for file in glob.glob(
        "enm/presence/**/*Presence_*.csv",
        recursive=True
    ):

        name = (
            os.path.basename(file)
            .replace("Presence_", "")
            .replace(".csv", "")
            .replace("_", " ")
            .lower()
        )

        species.add(name)

    return species


KNOWN_ENM_SPECIES = load_enm_species()


def contains_taxonomic_group(q: str):

    for group in KNOWN_TAXONOMIC_GROUPS:

        pattern = rf"\b{re.escape(group)}\b"

        if re.search(pattern, q):

            return group

    return None

# ======================================================
# KNOWN TAXONOMIC GROUPS
# ======================================================

KNOWN_TAXONOMIC_GROUPS = {
    "fish",
    "fishes",
    "pesce",
    "pesci",

    "bird",
    "birds",
    "uccello",
    "uccelli",

    "crustacean",
    "crustaceans",
    "crostaceo",
    "crostacei",

    "amphibian",
    "amphibians",
    "anfibio",
    "anfibi",

    "reptile",
    "reptiles",
    "rettile",
    "rettili",

    "mammal",
    "mammals",
    "mammifero",
    "mammiferi"
}

# ======================================================
# SPECIES DETECTION
# ======================================================

def contains_known_species(q: str):

    for species in KNOWN_ENM_SPECIES:

        pattern = rf"\b{re.escape(species)}\b"

        if re.search(pattern, q):

            return species

    return None


print(
    f"[ROUTER] Loaded "
    f"{len(KNOWN_ENM_SPECIES)} "
    f"ENM species"
)

# ======================================================
# ENM DETECTION
# ======================================================

def asks_enm(q: str):

    patterns = [
        "habitat suitability",
        "suitable habitat",
        "species distribution",
        "ecological niche"
    ]

    return any(p in q for p in patterns)


# ======================================================
# ROUTER
# ======================================================

def route_question(question: str):

    q = normalize(question)

    log_section("ROUTER V35 (RISK TARGET FIX)")
    log_question(question)

    # ==================================================
    # ENM SPECIES SHORTCUT
    # ==================================================

    species_match = contains_known_species(q)

    if species_match:

        print(
            f"[ROUTER] ENM species detected: "
            f"{species_match}"
        )

        log_route(
            f"ENM (species={species_match})"
        )

        return {
            "type": "enm"
        }

    # ==================================================
    # HARD RULES
    # ==================================================

    if is_data_query(q):

        log_route("DATA (hard rule)")

        return {"type": "data"}

    # ==================================================
    # PARSER
    # ==================================================

    parsed = parse_features(
        question,
        return_metadata=True
    )

    modifications = parsed.get(
        "modifications",
        []
    )

    scenario_detected = parsed["scenario_detected"]

    num_modified = parsed["num_modified_features"]

    range_detected = parsed["range_detected"]

    # ==================================================
    # SEMANTICS
    # ==================================================

    target = detect_target(q)

    comparison_detected = has_comparison(q)

    dependency_detected = asks_dependency(q)

    driver_analysis = asks_driver_analysis(q)

    importance_compare_detected = (

        comparison_detected

        and not scenario_detected

        and target == "risk"
    )

    delta_reasoning = asks_delta_reasoning(q)

    risk_estimation = asks_risk_estimation(q)

    baseline_reference = references_baseline(q)

    enm_detected = asks_enm(q)

    # ==================================================
    # SCORES
    # ==================================================

    scores = {
        "assessment": 0,
        "dependency": 0,
        "delta": 0,
        "comparison": 0,
        "importance": 0,
        "importance_compare": 0,
        "drivers": 0,
        "enm": 0
    }

    # ==================================================
    # LEVEL 1 — DOMINANT STRUCTURES
    # ==================================================

    # --------------------------------------------------
    # IMPORTANCE COMPARE
    # --------------------------------------------------

    if importance_compare_detected:

        scores["importance_compare"] += 450

    # --------------------------------------------------
    # COMPARISON
    # --------------------------------------------------

    if (comparison_detected and not importance_compare_detected):

        scores["comparison"] += 400

    # --------------------------------------------------
    # DELTA
    # --------------------------------------------------

    if (
        scenario_detected
        and num_modified == 1
        and target == "risk"
        and not comparison_detected
    ):

        scores["delta"] += 350

    # --------------------------------------------------
    # ASSESSMENT
    # --------------------------------------------------

    if (
        scenario_detected
        and risk_estimation
        and num_modified > 1

    ):

        scores["assessment"] += 300

    # --------------------------------------------------
    # ENM
    # --------------------------------------------------

    if enm_detected:

        scores["enm"] += 300

    # ==================================================
    # LEVEL 2 — CONTEXTUAL SEMANTICS
    # ==================================================

    # --------------------------------------------------
    # DEPENDENCY
    # --------------------------------------------------

    if dependency_detected:
        scores["dependency"] += 180

    # --------------------------------------------------
    # DRIVER FAMILY
    # --------------------------------------------------

    if driver_analysis and not dependency_detected:

        if target == "risk":

            scores["importance"] += 240

        elif target in ["variable", "ecosystem"]:

            scores["drivers"] += 240

    # --------------------------------------------------
    # ASSESSMENT CONTEXT
    # --------------------------------------------------

    if target == "risk":

        scores["assessment"] += 60

    if scenario_detected and num_modified > 1:

        scores["assessment"] += 40

    # ==================================================
    # LEVEL 3 — DELTA TRAJECTORY
    # ==================================================

    if (
        delta_reasoning
        and scenario_detected
        and num_modified == 1
        and target == "risk"
    ):

        scores["delta"] += 120

    # ==================================================
    # LEVEL 4 — CONFLICT RESOLUTION
    # ==================================================

    # --------------------------------------------------
    # COMPARISON DOMINATES
    # --------------------------------------------------

    if (comparison_detected and not importance_compare_detected):

        scores["comparison"] += 100

    # --------------------------------------------------
    # DRIVER ANALYSIS REDUCES ASSESSMENT
    # --------------------------------------------------

    if driver_analysis:

        scores["assessment"] -= 60

    # --------------------------------------------------
    # TRUE DELTA SHOULD REDUCE ASSESSMENT
    # --------------------------------------------------

    if (
        range_detected
        and not baseline_reference
        and target == "risk"
    ):

        scores["assessment"] -= 120

    # ==================================================
    # DEBUG
    # ==================================================

    print("---- ROUTER SEMANTICS ----")

    print("scenario_detected:", scenario_detected)
    print("num_modified:", num_modified)
    print("range_detected:", range_detected)
    print("baseline_reference:", baseline_reference)

    print("target:", target)

    print("comparison_detected:", comparison_detected)
    print("dependency_detected:", dependency_detected)

    print(
        "importance_compare_detected:",
        importance_compare_detected
    )

    print("driver_analysis:", driver_analysis)
    print("risk_estimation:", risk_estimation)

    print("--------------------------")

    # --------------------------------------------------
    # IMPORTANCE DEBUG
    # --------------------------------------------------

    if (
        driver_analysis
        or importance_compare_detected
    ):

        print("\n===== IMPORTANCE DEBUG =====")

        print(
            "dependency_detected =",
            dependency_detected
        )

        print(
            "comparison_detected =",
            comparison_detected
        )

        print(
            "importance_compare_detected =",
            importance_compare_detected
        )

        print(
            "driver_analysis =",
            driver_analysis
        )

        print(
            "target =",
            target
        )

        print(
            "num_modified =",
            num_modified
        )

        print("============================\n")

    print("---- SCORE BREAKDOWN ----")

    for k, v in sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    ):

        print(f"{k}: {v}")

    print("-------------------------")

    # ==================================================
    # FINAL SELECTION
    # ==================================================

    best = max(scores, key=scores.get)

    log_route(f"{best.upper()} (score={scores[best]})")

    return {"type": best}


# ======================================================
# LEGACY
# ======================================================

def explain_with_shap(*args, **kwargs):
    return None