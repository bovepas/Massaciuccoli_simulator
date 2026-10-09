from typing import Dict, Any

from utils.feature_mapping import normalize_feature_name


def assessment_extraction_to_inputs(extraction) -> Dict[str, Any]:
    """
    Convert an AssessmentExtraction object into the input structures
    expected by the existing handle_assessment() function.

    The LLM extractor is responsible for semantic interpretation.
    This bridge is responsible only for translating that semantic
    representation into the structures already used by Assessment.

    Returns:
        {
            "features": {...},
            "qualitative_changes": [...]
        }
    """

    if extraction is None:
        return {
            "features": {},
            "qualitative_changes": [],
        }

    features = {}
    qualitative_changes = []

    for modification in extraction.scenario:

        feature = normalize_feature_name(modification.variable)

        # Assessment extractor may use compact semantic names
        # that are not directly present in the legacy feature mapper.
        if not feature and modification.variable == "land_use":
            feature = "Land use and cover"

        if not feature:
            continue

        modification_type = modification.modification_type

        if modification_type == "delta":
            if modification.value is None:
                continue
            features[feature] = {
                "type": "numeric",
                "value": modification.value,
            }

        elif modification_type == "percentage":
            if modification.value is None:
                continue
            features[feature] = {
                "type": "percentage_change",
                "value": modification.value,
            }

        elif modification_type == "target":
            if modification.value is None:
                continue
            features[feature] = modification.value

        elif modification_type == "qualitative":
            qualitative_changes.append({
                "feature": feature,
                "direction": modification.direction,
                "magnitude": modification.magnitude,
            })

        elif modification_type == "state_change":
            if modification.to_value is None:
                continue
            features[feature] = modification.to_value

        

    return {
        "features": features,
        "qualitative_changes": qualitative_changes,
    }