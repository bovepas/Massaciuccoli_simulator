from extraction.dependency.schema import DependencyExtraction
from utils.feature_mapping import normalize_feature_name


def _normalize_variable(variable: str):
    feature = normalize_feature_name(variable)

    if feature:
        return feature

    return variable


def dependency_extraction_to_inputs(
    extraction: DependencyExtraction
):
    if extraction is None:
        raise ValueError(
            "Dependency extraction is None"
        )

    if extraction.intent != "dependency_query":
        raise ValueError(
            f"Unexpected intent: {extraction.intent}"
        )

    driver = _normalize_variable(
        extraction.driver
    )

    target = _normalize_variable(
        extraction.target
    )

    if not driver:
        raise ValueError(
            "No driver extracted"
        )

    if not target:
        raise ValueError(
            "No target extracted"
        )

    return {
        "driver": driver,
        "target": target
    }