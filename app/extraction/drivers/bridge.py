import re

from extraction.drivers.schema import DriversExtraction
from utils.feature_mapping import FEATURE_LABELS, normalize_feature_name


def _normalise_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip()).lower()


def _normalize_target(target: str):
    """Preserve canonical dataset columns before applying synonym mapping.

    normalize_feature_name() deliberately supports partial semantic matching; for
    a full column label that behaviour can collapse e.g. a decade-change column
    into its base variable. Exact canonical names must therefore be preserved first.
    """
    target_norm = _normalise_spaces(target)
    for canonical in FEATURE_LABELS.keys():
        if _normalise_spaces(canonical) == target_norm:
            return canonical

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
