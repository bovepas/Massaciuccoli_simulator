import json
import re

from tools.llm_client import call_llm
from extraction.delta.prompt import load_delta_prompt
from extraction.delta.schema import DeltaExtraction
from extraction.delta.range_detector import detect_range


# ------------------------------------------------------------------
# Reference units for canonical variables
# ------------------------------------------------------------------
# Used only when an explicit range has no unit in the user's text.
# An explicitly detected unit always takes precedence.
REFERENCE_UNITS = {
    "temperature": "degC",
    "tree_cover": "percent",
    "evapotranspiration": "percent",
    "precipitation": "percent",
}


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
    Deterministic arithmetic for an explicit range.

    For degC:
        delta = to - from

    For percent:
        an explicit range represents an absolute change between
        the two percentage values:
            delta = to - from

        Examples:
            0% -> 15%    = +15%
            0% -> -15%   = -15%
            15% -> 0%    = -15%
            -15% -> 0%   = +15%
            -10% -> +10% = +20%
            20% -> 40%   = +20%

        We deliberately do NOT calculate relative percentage change
        for explicit ranges, because that would produce misleading
        results when the starting value is zero or negative.
    """
    if unit in ("percent", "degC"):
        return round(to_value - from_value, 2)

    raise ValueError(f"Unsupported range unit: {unit}")


def _complete_with_python_range(data: dict, detected_range: dict) -> dict:
    """
    Complete and normalize an explicitly detected range using
    deterministic Python logic.

    Python is authoritative for:
    - the existence of the range
    - range endpoints
    - direction of the change
    - change calculation
    - natural-language interpretation when a range is explicit

    The LLM remains responsible for:
    - semantic variable identification
    - original expression
    - other semantic extraction fields
    """

    scenarios = data.get("scenario", [])

    if not isinstance(scenarios, list):
        return data

    if not scenarios:
        return data

    # Current delta extraction is expected to describe one scenario.
    scenario = scenarios[0]

    if not isinstance(scenario, dict):
        return data

    from_value = detected_range["from_value"]
    to_value = detected_range["to_value"]
    detected_unit = detected_range["unit"]

    # ----------------------------------------------------------
    # 1. Resolve the unit
    # ----------------------------------------------------------
    # If the user explicitly provided a unit (% or °C), Python
    # trusts the detector.
    #
    # If the range has no explicit unit, infer the reference unit
    # from the canonical variable identified by the LLM.
    variable_name = scenario.get("variable")

    if detected_unit is not None:
        unit = detected_unit
    else:
        unit = REFERENCE_UNITS.get(variable_name)

    # A range without an explicit unit is valid only when its
    # canonical variable has a known reference unit.
    if unit is None:
        raise ValueError(
            "Cannot determine the unit for explicit range: "
            f"variable={variable_name!r}, "
            f"from_value={from_value}, "
            f"to_value={to_value}"
        )

    # ----------------------------------------------------------
    # 2. Python is authoritative about the explicit range
    # ----------------------------------------------------------
    scenario["range"] = {
        "from_value": from_value,
        "to_value": to_value,
        "unit": unit,
    }

    # ----------------------------------------------------------
    # 3. Python determines the direction from the endpoints
    # ----------------------------------------------------------
    if to_value > from_value:
        direction = "increase"
    elif to_value < from_value:
        direction = "decrease"
    else:
        direction = "no change"

    # ----------------------------------------------------------
    # 4. Python owns the mathematical calculation
    # ----------------------------------------------------------
    if unit is not None:
        calculated_value = _calculate_range_change(
            from_value=from_value,
            to_value=to_value,
            unit=unit,
        )

        scenario["change"] = {
            "value": calculated_value,
            "unit": unit,
        }

    # ----------------------------------------------------------
    # 5. Python builds a deterministic interpretation
    # ----------------------------------------------------------

    if direction == "increase":
        if unit == "percent":
            interpretation = (
                f"increase in {variable_name} by "
                f"{abs(calculated_value):g} percentage points"
            )
        elif unit == "degC":
            interpretation = (
                f"increase in {variable_name} by "
                f"{abs(calculated_value):g}°C"
            )
        else:
            interpretation = (
                f"increase in {variable_name} "
                f"from {from_value:g} to {to_value:g}"
            )

    elif direction == "decrease":
        if unit == "percent":
            interpretation = (
                f"decrease in {variable_name} by "
                f"{abs(calculated_value):g} percentage points"
            )
        elif unit == "degC":
            interpretation = (
                f"decrease in {variable_name} by "
                f"{abs(calculated_value):g}°C"
            )
        else:
            interpretation = (
                f"decrease in {variable_name} "
                f"from {from_value:g} to {to_value:g}"
            )

    else:
        interpretation = (
            f"no change in {variable_name}"
        )

    scenario["interpretation"] = interpretation

    return data

def _normalize_qualitative_change(
    data: dict,
    question: str,
) -> dict:
    """
    Enforce the project's qualitative normalization:
    increase -> +50%, decrease -> -50%.

    Never override explicit numeric changes, ranges,
    or absolute targets.
    """
    scenarios = data.get("scenario", [])
    if not isinstance(scenarios, list):
        return data

    # Explicit numeric magnitude: leave it untouched.
    numeric_pattern = re.compile(
        r"\b(?:by|to|from)\s*[+-]?\d+(?:[.,]\d+)?"
        r"|[+-]?\d+(?:[.,]\d+)?\s*"
        r"(?:%|percent(?:age)?|°\s*c|degc|degrees?)\b",
        re.IGNORECASE,
    )

    if numeric_pattern.search(question):
        return data

    qualitative_units = {
        "tree_cover",
        "evapotranspiration",
        "precipitation",
        "biodiversity",
    }

    increase_pattern = re.compile(
        r"\b(increase|increases|increased|increasing|"
        r"rise|rises|rose|rising|grow|grows|growth|"
        r"higher|gain|gains|improve|warming|warmer)\b",
        re.IGNORECASE,
    )
    decrease_pattern = re.compile(
        r"\b(decrease|decreases|decreased|decreasing|"
        r"decline|declines|declined|declining|"
        r"reduce|reduces|reduced|reducing|"
        r"lower|loss|losses|drop|drops|dropped|"
        r"fall|falls|fell|cooling|colder)\b",
        re.IGNORECASE,
    )

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue

        variable = scenario.get("variable")
        if variable not in qualitative_units:
            continue

        if scenario.get("change_type") == "absolute_target":
            continue

        expression = scenario.get("original_expression") or question

        inc = increase_pattern.search(expression)
        dec = decrease_pattern.search(expression)

        if inc is None and dec is None:
            continue

        # If both directions occur, do not guess.
        if inc is not None and dec is not None:
            continue

        if inc is not None:
            value = 50.0
            direction = "increase"
        else:
            value = -50.0
            direction = "decrease"

        scenario["change"] = {
            "value": value,
            "unit": "percent",
        }
        scenario["interpretation"] = (
            f"qualitative {direction} in {variable}, "
            f"normalized to {value:+g}%"
        )

    return data

def _remove_llm_range_when_not_detected(
    data: dict,
    question: str,
) -> dict:
    """
    Remove ranges hallucinated by the LLM when Python did not
    detect an explicit range.

    Also correct explicit absolute targets such as:
        "tree cover increases to 70%"
    """

    scenarios = data.get("scenario", [])

    if not isinstance(scenarios, list):
        return data

    # Remove ranges not supported by the original question.
    for scenario in scenarios:
        if isinstance(scenario, dict):
            scenario.pop("range", None)

    # Recognize explicit percentage targets deterministically.
    target_pattern = re.compile(
        r"\b(?:increase(?:s|d|ing)?|"
        r"decrease(?:s|d|ing)?|"
        r"rise(?:s|n|d|ing)?|"
        r"decline(?:s|d|ing)?|"
        r"fall(?:s|ing)?|"
        r"drop(?:s|ped|ping)?|"
        r"reduce(?:s|d|ing)?|"
        r"raise(?:s|d|ing)?|"
        r"reach(?:es|ed|ing)?|"
        r"set|sets|setting|"
        r"bring|brings|brought)"
        r"\s+to\s+(-?\d+(?:[.,]\d+)?)\s*%",
        flags=re.IGNORECASE,
    )

    for scenario in scenarios:
        if not isinstance(scenario, dict):
            continue

        expression = scenario.get("original_expression", "")
        match = target_pattern.search(expression)

        if not match:
            continue

        target_value = float(match.group(1))

        scenario["change_type"] = "absolute_target"
        scenario["change"] = {
            "value": target_value,
            "unit": "percent",
        }
        scenario["interpretation"] = (
            f"set {scenario.get('variable', 'variable')} "
            f"to {target_value:g}%"
        )

    return data




def extract_delta(question: str) -> DeltaExtraction:
    # ----------------------------------------------------------
    # 1. Deterministic structural decision BEFORE the LLM
    # ----------------------------------------------------------
    detected_range = detect_range(question)

    print("\n========== PYTHON RANGE DETECTOR ==========")
    print("Detected range:", detected_range)
    print("===========================================\n")

    # ----------------------------------------------------------
    # 2. LLM performs semantic extraction
    # ----------------------------------------------------------
    prompt = load_delta_prompt()
    prompt = prompt.replace("{{QUERY}}", question)

    raw_response = call_llm(prompt)

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw_response)
    print("======================================\n")

    data = _extract_json(raw_response)

    # ----------------------------------------------------------
    # 3. Python is authoritative about range + arithmetic
    # ----------------------------------------------------------
    if detected_range is not None:
        data = _complete_with_python_range(
            data,
            detected_range,
        )
    else:
        data = _remove_llm_range_when_not_detected(
            data,
            question,
        )

        data = _normalize_qualitative_change(
            data,
            question,
        )

    # ----------------------------------------------------------
    # 4. Final schema validation
    # ----------------------------------------------------------
    try:
        return DeltaExtraction.model_validate(data)
    except Exception as exc:
        raise ValueError(
            f"Delta extractor returned JSON with an invalid schema:\n{data}"
        ) from exc

