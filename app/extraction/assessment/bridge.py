
from typing import Dict, Any

from utils.feature_mapping import normalize_feature_name


def assessment_extraction_to_inputs(extraction) -> Dict[str, Any]:
    """
    Convert an AssessmentExtraction object into the input structures
    expected by handle_assessment().

    The LLM extractor is responsible for semantic interpretation.
    This bridge translates the extracted modifications into dataset
    features while preserving every unsupported modification.

    Returns:
        {
            "features": {...},
            "qualitative_changes": [...],
            "unsupported_modifications": [...]
        }
    """

    if extraction is None:
        return {
            "features": {},
            "qualitative_changes": [],
            "unsupported_modifications": [],
        }

    features = {}
    qualitative_changes = []
    unsupported_modifications = []

    for modification in extraction.scenario:

        variable = modification.variable
        modification_type = modification.modification_type

        # --------------------------------------------------
        # FEATURE NORMALIZATION
        # --------------------------------------------------

        feature = normalize_feature_name(variable)

        # Legacy compatibility
        if not feature and variable == "land_use":
            feature = "Land use and cover"

        # --------------------------------------------------
        # UNSUPPORTED VARIABLE
        # --------------------------------------------------

        if not feature:
            unsupported_modifications.append({
                "variable": variable,
                "original_expression": modification.original_expression,
                "modification_type": modification_type,
                "value": modification.value,
                "reason": "Variable not recognized or not mapped to a dataset feature."
            })
            continue


        # --------------------------------------------------
        # GRASSLAND COVER VALIDATION
        # --------------------------------------------------

        variable_text = (
            f"{variable} {modification.original_expression or ''}"
        ).lower().replace("_", " ")

        is_grassland_cover = (
            "grassland" in variable_text
            and any(
                term in variable_text
                for term in ("cover", "coverage")
            )
        )

        if (
            is_grassland_cover
            and modification_type == "percentage"
            and feature == "Presence of grassland"
        ):
            unsupported_modifications.append({
                "variable": variable,
                "original_expression": modification.original_expression,
                "normalized_feature": feature,
                "modification_type": modification_type,
                "value": modification.value,
                "reason": (
                    "Grassland is represented as binary presence/absence. "
                    "Percentage changes in grassland coverage cannot be "
                    "simulated using this feature."
                )
            })
            continue


        # --------------------------------------------------
        # MODIFICATION TRANSLATION
        # --------------------------------------------------

        if modification_type == "delta":

            if modification.value is None:
                unsupported_modifications.append({
                    "variable": variable,
                    "normalized_feature": feature,
                    "modification_type": modification_type,
                    "reason": "Missing modification value."
                })
                continue

            features[feature] = {
                "type": "numeric",
                "value": modification.value,
            }

        elif modification_type == "percentage":

            if modification.value is None:
                unsupported_modifications.append({
                    "variable": variable,
                    "normalized_feature": feature,
                    "modification_type": modification_type,
                    "reason": "Missing percentage value."
                })
                continue

            features[feature] = {
                "type": "percentage_change",
                "value": modification.value,
            }

        elif modification_type == "target":

            if modification.value is None:
                unsupported_modifications.append({
                    "variable": variable,
                    "normalized_feature": feature,
                    "modification_type": modification_type,
                    "reason": "Missing target value."
                })
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
                unsupported_modifications.append({
                    "variable": variable,
                    "normalized_feature": feature,
                    "modification_type": modification_type,
                    "reason": "Missing target state."
                })
                continue

            features[feature] = modification.to_value

        else:

            unsupported_modifications.append({
                "variable": variable,
                "normalized_feature": feature,
                "modification_type": modification_type,
                "reason": "Unsupported modification type."
            })

    # --------------------------------------------------
    # FINAL OUTPUT
    # --------------------------------------------------

    return {
        "features": features,
        "qualitative_changes": qualitative_changes,
        "unsupported_modifications": unsupported_modifications,
    }
