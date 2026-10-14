from extraction.dependency.schema import DependencyExtraction
from utils.feature_mapping import normalize_feature_name


ABSTRACT_TARGETS = {
    "water availability", "water level", "climate stress",
    "hydrological stress", "hydrology", "water",
    "ecosystem productivity", "ecosystem stability",
}


def _normalize_variable(variable: str, preserve_abstract: bool = False):
    if not variable:
        return None

    cleaned = variable.strip()
    if preserve_abstract and cleaned.lower() in ABSTRACT_TARGETS:
        return cleaned

    feature = normalize_feature_name(cleaned)
    if feature:
        # Abstract concepts can map to multiple features. This bridge must
        # preserve a scalar target and let task_dependency resolve it.
        if isinstance(feature, list):
            return cleaned
        return feature

    return cleaned


def dependency_extraction_to_inputs(extraction: DependencyExtraction):
    if extraction is None:
        raise ValueError("Dependency extraction is None")

    if extraction.intent != "dependency_query":
        raise ValueError(f"Unexpected intent: {extraction.intent}")

    driver = _normalize_variable(extraction.driver)
    target = _normalize_variable(extraction.target, preserve_abstract=True)

    if not driver:
        raise ValueError("No driver extracted")
    if not target:
        raise ValueError("No target extracted")

    return {"driver": driver, "target": target}
