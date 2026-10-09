import json
import re

from tools.llm_client import call_llm
from extraction.delta.prompt import load_delta_prompt
from extraction.delta.schema import DeltaExtraction


def _extract_json(raw_response: str) -> dict:
    """
    Extract a JSON object from the LLM response.

    Handles:
    1. Pure JSON responses
    2. JSON wrapped in Markdown code fences
    3. JSON surrounded by explanatory text
    """

    text = raw_response.strip()

    # Caso 1: risposta già JSON puro
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Caso 2: JSON dentro ```json ... ```
    match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if match:
        return json.loads(match.group(1))

    # Caso 3: JSON preceduto/s seguito da testo
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end + 1])

    raise ValueError(
        f"Delta extractor returned invalid JSON:\n{raw_response}"
    )


def _calculate_range_change(
    from_value: float,
    to_value: float,
    unit: str,
) -> float:
    """
    Calculate the deterministic change associated with an explicit range.

    For percentage variables:
        relative percentage change =
        ((to - from) / from) * 100

    For temperature:
        absolute difference =
        to - from
    """

    if unit == "percent":
        if from_value == 0:
            raise ValueError(
                "Cannot calculate relative percentage change "
                "when from_value is zero."
            )

        return ((to_value - from_value) / from_value) * 100

    if unit == "degC":
        return to_value - from_value

    raise ValueError(
        f"Unsupported range unit: {unit}"
    )


def _apply_deterministic_range_calculation(data: dict) -> dict:
    """
    Replace the LLM-generated change.value with a deterministic
    Python calculation whenever an explicit range is present.

    The LLM remains responsible for semantic extraction.
    Python is responsible for arithmetic.
    """

    scenarios = data.get("scenario", [])

    if not isinstance(scenarios, list):
        return data

    for scenario in scenarios:

        if not isinstance(scenario, dict):
            continue

        range_data = scenario.get("range")

        # No explicit range:
        # keep the change.value produced by the LLM.
        if not range_data:
            continue

        try:
            from_value = float(range_data["from_value"])
            to_value = float(range_data["to_value"])
            unit = range_data["unit"]
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid delta range returned by LLM: {range_data}"
            ) from exc

        calculated_value = _calculate_range_change(
            from_value=from_value,
            to_value=to_value,
            unit=unit,
        )

        # The LLM's arithmetic is deliberately ignored.
        scenario.setdefault("change", {})
        scenario["change"]["value"] = calculated_value
        scenario["change"]["unit"] = unit

    return data


def extract_delta(question: str) -> DeltaExtraction:
    """
    Extract a structured Delta scenario from a natural-language question.

    Semantic interpretation is delegated to the LLM.
    Deterministic arithmetic is performed locally in Python.
    """

    prompt = load_delta_prompt()
    prompt = prompt.replace("{{QUERY}}", question)

    raw_response = call_llm(prompt)

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw_response)
    print("======================================\n")

    data = _extract_json(raw_response)

    # ---------------------------------------------------------
    # Deterministic post-processing
    # ---------------------------------------------------------
    #
    # If the LLM extracted an explicit range, Python calculates
    # the actual change and overwrites the LLM-generated value.
    #
    # This prevents the LLM from being responsible for arithmetic.
    #
    data = _apply_deterministic_range_calculation(data)

    # ---------------------------------------------------------
    # Schema validation
    # ---------------------------------------------------------

    try:
        return DeltaExtraction.model_validate(data)

    except Exception as exc:
        raise ValueError(
            f"Delta extractor returned JSON with an invalid schema:\n{data}"
        ) from exc