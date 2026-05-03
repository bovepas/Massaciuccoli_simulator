"""
RAG Assessment — v2 (FIXED SIGNATURE)
"""


def generate_assessment_explanation(features):

    """
    features: list of tuples
    [
        ("feature_name", value),
        ...
    ]
    """

    if not features:
        return ""

    parts = []

    for name, value in features:

        name = name.lower()

        if "temperature" in name:
            parts.append("temperature increases ecosystem stress")

        elif "precipitation" in name:
            if value < 0:
                parts.append("reduced precipitation increases drought risk")
            else:
                parts.append("higher precipitation may support ecosystem stability")

        elif "evapotranspiration" in name:
            parts.append("evapotranspiration influences water balance")

        elif "tree cover" in name:
            parts.append("tree cover affects ecosystem resilience")

        elif "species" in name:
            parts.append("biodiversity influences ecosystem vulnerability")

        elif "phenology" in name:
            parts.append("ecosystem productivity affects nutrient dynamics")

        elif "grassland" in name:
            parts.append("grassland presence impacts habitat stability")

    return ". ".join(parts) + "."