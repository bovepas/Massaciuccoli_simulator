from extraction.importance.schema import ImportanceExtraction


def importance_extraction_to_inputs(
    extraction: ImportanceExtraction,
):
    if extraction is None:
        raise ValueError("Importance extraction is None")

    if extraction.intent != "importance_query":
        raise ValueError(
            f"Unexpected intent: {extraction.intent}"
        )

    top_k = extraction.top_k
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError(
            f"Invalid top_k: {top_k}"
        )

    focus = extraction.focus
    valid_focuses = {"all", "climate", "biodiversity", "land_use"}
    if focus not in valid_focuses:
        raise ValueError(
            f"Unexpected focus: {focus}"
        )

    direction = extraction.direction
    valid_directions = {"all", "increase", "decrease"}
    if direction not in valid_directions:
        raise ValueError(
            f"Unexpected direction: {direction}"
        )

    return {
        "top_k": top_k,
        "focus": focus,
        "direction": direction,
    }
