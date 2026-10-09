from extraction.data.schema import DataExtraction
from utils.feature_mapping import normalize_feature_name


def _normalize_variable(variable: str):
    feature = normalize_feature_name(variable)

    if feature:
        return feature

    return variable


def data_extraction_to_inputs(extraction: DataExtraction):
    if extraction is None:
        raise ValueError("Data extraction is None")

    if extraction.intent != "data_query":
        raise ValueError(
            f"Unexpected intent: {extraction.intent}"
        )

    variables = []

    for variable in extraction.variables:
        normalized = _normalize_variable(variable)

        if normalized not in variables:
            variables.append(normalized)

    if not variables:
        raise ValueError(
            "No variables extracted"
        )

    return {
        "variables": variables
    }