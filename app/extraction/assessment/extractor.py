import json
import re

from tools.llm_client import call_llm
from extraction.assessment.prompt import load_assessment_prompt
from extraction.assessment.schema import AssessmentExtraction


def _extract_json(text: str) -> dict:
    """
    Extract the first JSON object from an LLM response.

    The LLM is instructed to return JSON only, but this keeps the
    extractor robust against accidental markdown fences or extra text.
    """

    text = text.strip()

    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON object found in LLM response.")

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON extracted from LLM response: {exc}"
        ) from exc


def _infer_qualitative_direction(expression: str):
    """
    Infer direction only from explicit directional wording
    in the original qualitative expression.
    """
    text = expression.lower()

    decrease_patterns = (
        r"\bdecreas(?:e|es|ed|ing)\b",
        r"\breduc(?:e|es|ed|ing)\b",
        r"\bdeclin(?:e|es|ed|ing)\b",
        r"\bfall(?:s|ing)?\b",
        r"\bfell\b",
        r"\blower(?:s|ed|ing)?\b",
        r"\bless\b",
    )

    increase_patterns = (
        r"\bincreas(?:e|es|ed|ing)\b",
        r"\bgrow(?:s|ing)?\b",
        r"\bgrowing\b",
        r"\bris(?:e|es|en|ing)\b",
        r"\brose\b",
        r"\bhigher\b",
        r"\bmore\b",
        r"\brais(?:e|es|ed|ing)\b",
    )

    has_decrease = any(
        re.search(pattern, text)
        for pattern in decrease_patterns
    )
    has_increase = any(
        re.search(pattern, text)
        for pattern in increase_patterns
    )

    # Avoid guessing when the wording is ambiguous.
    if has_increase and not has_decrease:
        return "increase"

    if has_decrease and not has_increase:
        return "decrease"

    return None


_DIRECTIONAL_TYPE_VALUES = {"increase", "decrease", "change"}


def _unit_from_expression(expression: str, fallback=None):
    """Return a unit only when it is supported by the source expression."""
    text = expression.lower()
    if "%" in text:
        return "percent"
    if re.search(r"(?:°\s*c|\bdegc\b|\bdegrees?\s*(?:celsius|c)\b|\bcelsius\b)", text):
        return "degC"
    if re.search(r"\bdays?\b", text):
        return "days"
    if re.search(r"\b(?:species|individuals|specimens|count)\b", text):
        return "count"
    return fallback if fallback in {"percent", "degC", "days", "count", "unknown"} else None


def _number_after_change_word(expression: str):
    """Read an explicitly stated absolute change such as 'by 3°C' or 'by 4 days'."""
    pattern = re.compile(
        r"\bby\s*([+-]?\d+(?:[.,]\d+)?)\s*"
        r"(°\s*C|degC\b|degrees?\s*(?:Celsius|C)?\b|days?\b|species\b|individuals?\b|specimens?\b|count\b)?",
        re.IGNORECASE,
    )
    match = pattern.search(expression)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit_text = (match.group(2) or "").lower().replace(" ", "")
    if unit_text and ("c" in unit_text or "degree" in unit_text):
        unit = "degC"
    elif unit_text.startswith("day"):
        unit = "days"
    elif unit_text in {"species", "individual", "individuals", "specimen", "specimens", "count"}:
        unit = "count"
    else:
        unit = None
    return value, unit


def _number_at_target(expression: str):
    """Read an explicitly stated final value such as 'set to 20°C'."""
    pattern = re.compile(
        r"\b(?:set\s+to|equal\s+to|increases?\s+to|increased\s+to|"
        r"decreases?\s+to|decreased\s+to|rises?\s+to|falls?\s+to|to)\s*"
        r"([+-]?\d+(?:[.,]\d+)?)\s*"
        r"(°\s*C|degC\b|degrees?\s*(?:Celsius|C)?\b|days?\b|species\b|count\b)?",
        re.IGNORECASE,
    )
    match = pattern.search(expression)
    if not match:
        return None
    value = float(match.group(1).replace(",", "."))
    unit_text = (match.group(2) or "").lower().replace(" ", "")
    if unit_text and ("c" in unit_text or "degree" in unit_text):
        unit = "degC"
    elif unit_text.startswith("day"):
        unit = "days"
    elif unit_text in {"species", "count"}:
        unit = "count"
    else:
        unit = None
    return value, unit


def _normalize_invalid_directional_type(modification: dict) -> None:
    """Repair an LLM output that put direction in modification_type.

    This runs before Pydantic validation. It uses the original expression
    to distinguish an absolute delta, a final target, a percentage change,
    and a genuinely qualitative change.
    """
    raw_type = modification.get("modification_type")
    if raw_type not in _DIRECTIONAL_TYPE_VALUES:
        return

    expression = modification.get("original_expression", "")
    expression_lower = expression.lower()
    inferred_direction = _infer_qualitative_direction(expression)
    direction = inferred_direction or raw_type
    modification["direction"] = direction

    # Leave these as a temporary qualitative form; the existing deterministic
    # percentage/half rules below will convert them to percentage changes.
    if "%" in expression or "half" in expression_lower:
        modification["modification_type"] = "qualitative"
        modification["value"] = None
        modification["unit"] = None
        modification["from_value"] = None
        modification["to_value"] = None
        if str(modification.get("magnitude") or "").strip().lower() in {
            "increase", "increases", "increased", "increasing", "rise", "rising",
            "decrease", "decreases", "decreased", "decreasing", "fall", "falling",
            "change", "changes",
        }:
            modification["magnitude"] = None
        return

    # A final value takes precedence over an absolute change.
    target = _number_at_target(expression)
    if target is not None:
        value, unit = target
        modification["modification_type"] = "target"
        modification["value"] = value
        modification["unit"] = unit or _unit_from_expression(expression, modification.get("unit"))
        modification["from_value"] = None
        modification["to_value"] = None
        modification["magnitude"] = None
        return

    absolute_change = _number_after_change_word(expression)
    if absolute_change is not None:
        value, unit = absolute_change
        if direction == "decrease":
            value = -abs(value)
        elif direction == "increase":
            value = abs(value)
        modification["modification_type"] = "delta"
        modification["value"] = value
        modification["unit"] = unit or _unit_from_expression(expression, modification.get("unit"))
        modification["from_value"] = None
        modification["to_value"] = None
        modification["magnitude"] = None
        return

    # No explicit numeric magnitude or target: represent as qualitative.
    modification["modification_type"] = "qualitative"
    modification["value"] = None
    modification["unit"] = None
    modification["from_value"] = None
    modification["to_value"] = None
    if str(modification.get("magnitude") or "").strip().lower() in {
        "increase", "increases", "increased", "increasing", "rise", "rising",
        "decrease", "decreases", "decreased", "decreasing", "fall", "falling",
        "change", "changes",
    }:
        modification["magnitude"] = None

def _normalize_assessment_data(data: dict) -> dict:
    """
    Apply deterministic structural normalization to the raw LLM output.

    The LLM remains responsible for semantic extraction.
    This function only enforces interpretations that are directly
    determined by explicit expressions in the original user text.
    """

    scenario = data.get("scenario", [])

    for modification in scenario:
        # Some LLM responses incorrectly put a direction (increase/decrease)
        # in modification_type. Normalize it before the schema is validated.
        _normalize_invalid_directional_type(modification)

        expression = modification.get("original_expression", "")
        expression_lower = expression.lower()
        
        # Recover an omitted direction for qualitative modifications
        # using only the explicit wording in the original expression.
        if modification.get("modification_type") == "qualitative":
            direction = modification.get("direction")

            if direction not in ("increase", "decrease", "change"):
                inferred_direction = _infer_qualitative_direction(
                    expression
                )

                if inferred_direction is not None:
                    modification["direction"] = inferred_direction


        # Explicit percentage expressions
        if "%" in expression:
            value_match = re.search(
                r"(\d+(?:[.,]\d+)?)\s*%",
                expression
            )

            if value_match:
                value = float(value_match.group(1).replace(",", "."))

                if any(
                    phrase in expression_lower
                    for phrase in [
                        "reduced by half",
                        "decreased by half",
                        "cut in half",
                        "reduced to half",
                        "decreased to half",
                    ]
                ):
                    value = -50.0
                    direction = "decrease"

                elif any(
                    phrase in expression_lower
                    for phrase in [
                        "increased by half",
                        "increase by half",
                        "increased to half",
                    ]
                ):
                    value = 50.0
                    direction = "increase"

                else:
                    direction = modification.get("direction")

                    if direction is None:
                        if any(
                            word in expression_lower
                            for word in [
                                "decrease",
                                "decreases",
                                "decreased",
                                "decreasing",
                                "reduce",
                                "reduces",
                                "reduced",
                                "reducing",
                                "fall",
                                "falls",
                                "fell",
                                "decline",
                                "declines",
                                "declined",
                                "declining",
                                "lower",
                                "lowers",
                                "lowered",
                            ]
                        ):
                            direction = "decrease"

                        elif any(
                            word in expression_lower
                            for word in [
                                "increase",
                                "increases",
                                "increased",
                                "increasing",
                                "rise",
                                "rises",
                                "rose",
                                "growing",
                                "grow",
                                "grows",
                                "higher",
                                "raises",
                                "raised",
                            ]
                        ):
                            direction = "increase"

                    if direction == "decrease":
                        value = -abs(value)
                    elif direction == "increase":
                        value = abs(value)

                modification["modification_type"] = "percentage"
                modification["value"] = value
                modification["unit"] = "percent"
                modification["magnitude"] = None

                if direction in {"increase", "decrease"}:
                    modification["direction"] = direction

                modification["from_value"] = None
                modification["to_value"] = None

        # "Half" without an explicit percentage
        elif "half" in expression_lower:
            if any(
                phrase in expression_lower
                for phrase in [
                    "reduced by half",
                    "decreased by half",
                    "cut in half",
                    "reduced to half",
                    "decreased to half",
                ]
            ):
                modification["modification_type"] = "percentage"
                modification["value"] = -50.0
                modification["unit"] = "percent"
                modification["direction"] = "decrease"
                modification["magnitude"] = None
                modification["from_value"] = None
                modification["to_value"] = None

            elif any(
                phrase in expression_lower
                for phrase in [
                    "increased by half",
                    "increase by half",
                    "increased to half",
                ]
            ):
                modification["modification_type"] = "percentage"
                modification["value"] = 50.0
                modification["unit"] = "percent"
                modification["direction"] = "increase"
                modification["magnitude"] = None
                modification["from_value"] = None
                modification["to_value"] = None

        # A percentage-like magnitude is never qualitative.
        magnitude = modification.get("magnitude")

        if (
            modification.get("modification_type") == "qualitative"
            and isinstance(magnitude, str)
            and re.fullmatch(
                r"\s*\d+(?:[.,]\d+)?\s*%\s*",
                magnitude
            )
        ):
            value = float(
                re.sub(r"[^\d.,]", "", magnitude).replace(",", ".")
            )

            direction = modification.get("direction")

            if direction == "decrease":
                value = -abs(value)
            elif direction == "increase":
                value = abs(value)

            modification["modification_type"] = "percentage"
            modification["value"] = value
            modification["unit"] = "percent"
            modification["magnitude"] = None
            modification["from_value"] = None
            modification["to_value"] = None

    return data


def extract_assessment(question: str) -> AssessmentExtraction:
    """
    Extract semantic Assessment modifications from a user question.

    The LLM performs semantic extraction only.
    Numerical interpretation and application to the dataset are handled
    by the Python application layer.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    prompt = load_assessment_prompt()

    llm_input = f"""
{prompt}

==================================================
USER QUESTION
==================================================

{question}

==================================================
END USER QUESTION
==================================================
"""

    response = call_llm(llm_input)

    if not response:
        raise ValueError("LLM returned an empty response.")

    data = _extract_json(response)

    data = _normalize_assessment_data(data)

    return AssessmentExtraction.model_validate(data)
