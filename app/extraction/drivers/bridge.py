from extraction.drivers.schema import DriversExtraction
from utils.feature_mapping import normalize_feature_name


def _normalize_target(target: str):
    feature = normalize_feature_name(target)
    if feature:
        return feature
    return target


def drivers_extraction_to_inputs(extraction: DriversExtraction):
    if extraction is None:
        raise ValueError("Drivers extraction is None")

    if extraction.intent != "drivers_query":
        raise ValueError(
            f"Unexpected intent: {extraction.intent}"
        )

    target = _normalize_target(extraction.target)

    if not target:
        raise ValueError("No target extracted")

    direction = extraction.direction

    if direction not in {"increase", "decrease", "unspecified"}:
        raise ValueError(
            f"Unexpected direction: {direction}"
        )

    return {
        "target": target,
        "direction": direction,
    }
