from extraction.importance_compare.schema import (
    ImportanceCompareExtraction
)

from utils.feature_mapping import (
    normalize_feature_name
)


def _normalize_entity(entity: str):
    feature = normalize_feature_name(entity)

    if feature:
        return feature

    return entity


def importance_compare_extraction_to_inputs(
    extraction: ImportanceCompareExtraction
):
    if extraction is None:
        raise ValueError(
            "Importance Compare extraction is None"
        )

    if extraction.intent != "importance_compare_query":
        raise ValueError(
            f"Unexpected intent: {extraction.intent}"
        )

    if not extraction.entity_a:
        raise ValueError(
            "No first entity extracted"
        )

    if not extraction.entity_b:
        raise ValueError(
            "Importance comparison requires two entities"
        )

    entity_a = _normalize_entity(
        extraction.entity_a
    )

    entity_b = _normalize_entity(
        extraction.entity_b
    )

    if not entity_a:
        raise ValueError(
            "Could not normalize first entity"
        )

    if not entity_b:
        raise ValueError(
            "Could not normalize second entity"
        )

    return {
        "entity_a": entity_a,
        "entity_b": entity_b
    }