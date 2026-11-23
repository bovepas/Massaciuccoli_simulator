import json
import re

from tools.llm_client import call_llm
from extraction.importance_compare.schema import ImportanceCompareExtraction


PROMPT_PATH = (
    "/app/extraction/importance_compare/"
    "importance_compare_extraction.txt"
)


def load_importance_compare_prompt() -> str:
    with open(
        PROMPT_PATH,
        "r",
        encoding="utf-8"
    ) as f:
        return f.read()


def _extract_json(raw_response: str) -> dict:
    text = raw_response.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if match:
        return json.loads(match.group(1))

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(
            text[start:end + 1]
        )

    raise ValueError(
        "Importance Compare extractor returned "
        f"invalid JSON:\n{raw_response}"
    )


# The schema deliberately accepts only canonical directions. The LLM may
# express the same meaning with a synonym; normalize those labels before
# Pydantic validation, while leaving unknown values untouched so that
# genuinely invalid outputs are still rejected.
_DIRECTION_ALIASES = {
    "increase": "increase",
    "increases": "increase",
    "increased": "increase",
    "increasing": "increase",
    "rise": "increase",
    "rises": "increase",
    "rose": "increase",
    "rising": "increase",
    "grow": "increase",
    "grows": "increase",
    "grew": "increase",
    "grown": "increase",
    "growing": "increase",
    "higher": "increase",
    "high": "increase",
    "gain": "increase",
    "gains": "increase",
    "gained": "increase",
    "gaining": "increase",
    "raise": "increase",
    "raises": "increase",
    "raised": "increase",
    "raising": "increase",
    "expand": "increase",
    "expands": "increase",
    "expanded": "increase",
    "expanding": "increase",
    "expansion": "increase",
    "restore": "increase",
    "restores": "increase",
    "restored": "increase",
    "restoring": "increase",
    "restoration": "increase",
    "improve": "increase",
    "improves": "increase",
    "improved": "increase",
    "improving": "increase",
    "improvement": "increase",
    "increase in": "increase",
    "decrease": "decrease",
    "decreases": "decrease",
    "decreased": "decrease",
    "decreasing": "decrease",
    "reduce": "decrease",
    "reduces": "decrease",
    "reduced": "decrease",
    "reducing": "decrease",
    "reduction": "decrease",
    "decline": "decrease",
    "declines": "decrease",
    "declined": "decrease",
    "declining": "decrease",
    "lower": "decrease",
    "low": "decrease",
    "fall": "decrease",
    "falls": "decrease",
    "fell": "decrease",
    "fallen": "decrease",
    "falling": "decrease",
    "loss": "decrease",
    "losses": "decrease",
    "drop": "decrease",
    "drops": "decrease",
    "dropped": "decrease",
    "dropping": "decrease",
    "diminish": "decrease",
    "diminishes": "decrease",
    "diminished": "decrease",
    "diminishing": "decrease",
    "degradation": "decrease",
    "degrade": "decrease",
    "degrades": "decrease",
    "degraded": "decrease",
    "degrading": "decrease",
    "unspecified": "unspecified",
    "unknown": "unspecified",
    "none": "unspecified",
    "n/a": "unspecified",
}


def _normalize_directions(data: dict) -> dict:
    """Map direction synonyms to the schema's three canonical values."""
    normalized = dict(data)

    for field in ("direction_a", "direction_b"):
        value = normalized.get(field)

        if not isinstance(value, str):
            # Leave missing/null/non-string values to schema validation.
            continue

        key = re.sub(r"\s+", " ", value.strip().lower())
        canonical = _DIRECTION_ALIASES.get(key)

        if canonical is not None and canonical != value:
            print(
                f"[IMPORTANCE_COMPARE] Normalized {field}: "
                f"{value!r} -> {canonical!r}"
            )
            normalized[field] = canonical

    return normalized


def extract_importance_compare(
    question: str
) -> ImportanceCompareExtraction:

    prompt = load_importance_compare_prompt()

    prompt = prompt.replace(
        "{{QUERY}}",
        question
    )

    raw_response = call_llm(prompt, role="extraction")

    print(
        "\n========== RAW LLM RESPONSE =========="
    )
    print(raw_response)
    print(
        "======================================\n"
    )

    data = _extract_json(
        raw_response
    )
    data = _normalize_directions(data)

    try:
        return ImportanceCompareExtraction.model_validate(
            data
        )

    except Exception as exc:
        raise ValueError(
            "Importance Compare extractor returned "
            "JSON with an invalid schema:\n"
            f"{data}"
        ) from exc