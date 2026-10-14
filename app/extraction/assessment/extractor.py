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

def _normalize_assessment_data(data: dict) -> dict:
    """
    Apply deterministic structural normalization to the raw LLM output.

    The LLM remains responsible for semantic extraction.
    This function only enforces interpretations that are directly
    determined by explicit expressions in the original user text.
    """

    scenario = data.get("scenario", [])

    for modification in scenario:
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
