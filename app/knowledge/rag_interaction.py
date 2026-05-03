"""
Massaciuccoli Digital Twin
RAG — INTERACTION v11 (RELEVANCE-AWARE + CONTROLLED TEXT)
"""

# ======================================================
# CLEAN NAME (aligned with tasks)
# ======================================================

def clean_name(name):

    name = name.lower()

    if "temperature" in name:
        return "temperature"
    if "precipitation" in name:
        return "precipitation"
    if "evapotranspiration" in name:
        return "evapotranspiration"
    if "tree cover" in name:
        return "tree cover"
    if "species" in name:
        return "biodiversity"
    if "phenology" in name:
        return "ecosystem productivity"
    if "grassland" in name:
        return "grassland"

    return name


# ======================================================
# VALUE → DIRECTION
# ======================================================

def value_to_direction(value):

    try:
        value = float(value)
    except:
        return "remains stable"

    if value > 0:
        return "increases"
    elif value < 0:
        return "decreases"
    else:
        return "remains stable"


# ======================================================
# MAIN
# ======================================================

def generate_interaction_explanation(features, relevant, irrelevant):

    """
    features: [(feature_name, value)]
    relevant: [feature_name]
    irrelevant: [feature_name]
    """

    print("\n[RAG-INTERACTION v11] START")

    # --------------------------------------------------
    # CLEAN FEATURES
    # --------------------------------------------------

    clean_features = [(clean_name(f), v) for f, v in features]

    relevant_clean = [clean_name(f) for f in relevant]
    irrelevant_clean = [clean_name(f) for f in irrelevant]

    print("[RELEVANT]:", relevant_clean)
    print("[IRRELEVANT]:", irrelevant_clean)

    # --------------------------------------------------
    # BUILD TEXT BLOCKS
    # --------------------------------------------------

    dynamic_statements = []
    relevant_statements = []
    irrelevant_statements = []

    for f, v in clean_features:

        direction = value_to_direction(v)

        # dynamic description
        if direction != "remains stable":
            dynamic_statements.append(f"{f} {direction}")

        # relevance separation
        if f in relevant_clean:
            relevant_statements.append(f"{f} plays a significant role")
        elif f in irrelevant_clean:
            irrelevant_statements.append(f"{f} shows limited influence under these conditions")

    # --------------------------------------------------
    # SENTENCE BUILDING
    # --------------------------------------------------

    parts = []

    # dynamic changes
    if dynamic_statements:
        parts.append(
            ", ".join(dynamic_statements).capitalize()
        )

    # relevant drivers
    if relevant_statements:
        parts.append(
            "Key drivers include " + ", ".join(relevant_statements)
        )

    # irrelevant drivers
    if irrelevant_statements:
        parts.append(
            "while " + ", ".join(irrelevant_statements)
        )

    # --------------------------------------------------
    # FINAL TEXT
    # --------------------------------------------------

    if not parts:
        final_text = "The system shows stable conditions with no significant environmental changes."
    else:
        final_text = ". ".join(parts) + "."

    print("[FINAL]:", final_text)
    print("[RAG-INTERACTION v11] END")

    return final_text