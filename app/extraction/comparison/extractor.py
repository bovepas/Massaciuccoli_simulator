import json
import os
import re

import requests

from extraction.comparison.schema import ComparisonExtraction


OLLAMA_URL = os.getenv(
    "OLLAMA_URL",
    "http://ollama:11434/api/generate"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "llama3.2:3b"
)

PROMPT_PATH = os.path.join(
    os.path.dirname(__file__),
    "comparison_extraction.txt"
)


def _load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_json(text):
    """
    Extract the first JSON object returned by the LLM.
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE
        )
        text = re.sub(
            r"\s*```$",
            "",
            text
        ).strip()

    match = re.search(
        r"\{.*\}",
        text,
        re.DOTALL
    )

    if not match:
        raise ValueError(
            f"No JSON object found in LLM response:\n{text}"
        )

    return json.loads(match.group(0))


def _infer_percentage_direction(modification):
    """
    Infer the direction of an explicit percentage modification
    when the LLM did not provide it.

    The numeric value remains positive.
    The sign is applied later by the bridge.
    """

    if modification.get("direction") in {
        "increase",
        "decrease",
        "change",
    }:
        return

    text = " ".join(
        str(modification.get(key, "") or "")
        for key in (
            "original_expression",
            "interpretation",
        )
    ).lower()

    decrease_terms = [
        "decrease",
        "decreases",
        "decreased",
        "decline",
        "declines",
        "declined",
        "lower",
        "lowers",
        "lowered",
        "reduce",
        "reduces",
        "reduced",
        "loss",
        "losses",
        "decrease by",
    ]

    increase_terms = [
        "increase",
        "increases",
        "increased",
        "rise",
        "rises",
        "rose",
        "higher",
        "raises",
        "raised",
        "gain",
        "gains",
        "increase by",
    ]

    if any(term in text for term in decrease_terms):
        modification["direction"] = "decrease"
        return

    if any(term in text for term in increase_terms):
        modification["direction"] = "increase"


def _normalize_comparison_data(data):
    """
    Deterministic normalization of the LLM extraction.

    The LLM performs semantic extraction.
    This function only enforces the extraction contract.
    It does not perform arithmetic or model calculations.
    """

    for scenario_key in ("scenario_a", "scenario_b"):
        scenario = data.get(scenario_key, [])

        for modification in scenario:
            modification_type = modification.get(
                "modification_type"
            )

            if modification_type == "percentage":
                # Percentage magnitude is never qualitative.
                modification["magnitude"] = None

                # The bridge expects a positive magnitude plus
                # a separate direction.
                _infer_percentage_direction(modification)

    return data


def extract_comparison(question: str) -> ComparisonExtraction:
    """
    Extract the semantic structure of a comparison question.

    The LLM performs semantic extraction only.
    Numerical calculations and model application are handled elsewhere.
    """

    prompt_template = _load_prompt()

    prompt = prompt_template.replace(
        "{{QUERY}}",
        question
    )

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "format": "json",
        },
        timeout=120,
    )

    response.raise_for_status()

    data = response.json()

    raw_text = data.get("response", "").strip()

    if not raw_text:
        raise ValueError(
            "Empty response from Ollama"
        )

    parsed_json = _extract_json(raw_text)

    parsed_json = _normalize_comparison_data(
        parsed_json
    )

    return ComparisonExtraction.model_validate(
        parsed_json
    )