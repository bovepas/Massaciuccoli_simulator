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
    if focus not in {"increase", "decrease", "all"}:
        raise ValueError(
            f"Unexpected focus: {focus}"
        )

    return {
        "top_k": top_k,
        "focus": focus,
    }