"""
Massaciuccoli Digital Twin
Router v43 — FIX importance + IF scenario
"""

import os


def load_species_names():
    base_path = "/app/enm/presence"
    species = set()

    for root, dirs, files in os.walk(base_path):
        for f in files:
            if f.startswith("Presence_") and f.endswith(".csv"):
                name = f.replace("Presence_", "").replace(".csv", "")
                name = name.replace("_", " ").lower()
                species.add(name)

    return species


SPECIES_NAMES = load_species_names()


CATEGORY_KEYWORDS = [
    "fish", "birds", "mammals", "insects",
    "molluscs", "reptiles", "amphibians", "crustaceans"
]

VARIABLE_KEYWORDS = [
    "temperature",
    "precipitation",
    "biodiversity",
    "evapotranspiration",
    "grassland",
    "tree cover",
    "land use"
]

SYSTEM_TARGETS = [
    "ecosystem",
    "risk",
    "ecosystem risk"
]

IMPORTANCE_KEYWORDS = [
    "most important",
    "most influential",
    "most relevant",
    "top",
    "main factors",
    "key drivers",
    "driving",
    "what drives",
    "which variables",
    "which factors",
    "drivers"
]


def detect_enm(q):
    for s in SPECIES_NAMES:
        if s in q:
            print(f"[ROUTER] ENM species: {s}")
            return True

    enm_keywords = [
        "habitat suitability",
        "species distribution",
        "distribution",
        "suitability"
    ]

    has_enm_intent = any(k in q for k in enm_keywords)
    has_bio_ref = any(c in q for c in CATEGORY_KEYWORDS)

    if has_enm_intent and has_bio_ref:
        print("[ROUTER] ENM category + intent")
        return True

    return False


def route_question(question: str):

    print("\n================ ROUTER v43 DEBUG ================")

    q = question.lower().strip()
    print("QUESTION:", q)

    var_count = sum(v in q for v in VARIABLE_KEYWORDS)
    has_system = any(t in q for t in SYSTEM_TARGETS)
    has_importance = any(p in q for p in IMPORTANCE_KEYWORDS)

    # --------------------------------------------------
    # 1️⃣ ENM
    # --------------------------------------------------

    if detect_enm(q):
        print("[ROUTER] → enm")
        return {"type": "enm"}

    # --------------------------------------------------
    # 2️⃣ COMPARISON
    # --------------------------------------------------

    if any(p in q for p in ["compare", "vs", "versus", "difference between"]):
        print("[ROUTER] → comparison")
        return {"type": "comparison"}

    if "which" in q and " or " in q:
        print("[ROUTER] → comparison (implicit)")
        return {"type": "comparison"}

    # --------------------------------------------------
    # 3️⃣ DELTA
    # --------------------------------------------------

    if "from" in q and "to" in q:
        print("[ROUTER] → delta")
        return {"type": "delta"}

    # --------------------------------------------------
    # 🔥 4️⃣ IMPORTANCE (priority, even with IF)
    # --------------------------------------------------

    if has_importance:
        print("[ROUTER] → importance")
        return {"type": "importance"}

    # --------------------------------------------------
    # 🔥 5️⃣ MULTI-VARIABLE → SYSTEM
    # --------------------------------------------------

    if var_count >= 2 and has_system:
        print("[ROUTER] → assessment (multi-variable system)")
        return {"type": "assessment"}

    # --------------------------------------------------
    # 6️⃣ DEPENDENCY
    # --------------------------------------------------

    if "how does" in q and "if" in q:
        print("[ROUTER] → dependency (directional)")
        return {"type": "dependency"}

    if any(v in q for v in ["affect", "impact", "influence"]):
        print("[ROUTER] → dependency (variable relation)")
        return {"type": "dependency"}

    if "if" in q:
        if var_count == 1:
            print("[ROUTER] → dependency (single variable)")
            return {"type": "dependency"}

        print("[ROUTER] → assessment (multi-variable)")
        return {"type": "assessment"}

    # --------------------------------------------------
    # 7️⃣ DEFAULT
    # --------------------------------------------------

    print("[ROUTER] → assessment")
    return {"type": "assessment"}