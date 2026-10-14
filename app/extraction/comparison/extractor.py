import copy
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


def _canonical_variable_in_text(text):
    """Return canonical variables explicitly mentioned in text."""
    text = (text or "").lower()
    aliases = {
        "temperature": [r"\btemperature\b", r"\bwarmer\b", r"\bheat\b"],
        "precipitation": [r"\bprecipitation\b", r"\brainfall\b", r"\brain\b"],
        "evapotranspiration": [r"\bevapotranspiration\b", r"\bevaporation\b"],
        "biodiversity": [r"\bbiodiversity\b", r"\bspecies richness\b", r"\bnumber of species\b"],
        "tree_cover": [r"\btree cover\b", r"\btrees\b", r"\btree density\b"],
        "grassland": [r"\bgrassland\b", r"\bgrass\b"],
        "land_use": [r"\bland use\b", r"\bland-use class\b"],
        "productivity": [r"\bproductivity\b", r"\bplant productivity\b", r"\bvegetation productivity\b"],
        "land_imperviousness": [r"\bimperviousness\b", r"\bimpervious surface\b", r"\burbanization\b"],
    }
    return {
        variable for variable, patterns in aliases.items()
        if any(re.search(pattern, text) for pattern in patterns)
    }


def _canonical_variable_name(variable):
    """Normalize common LLM variable labels to the prompt's canonical names."""
    value = re.sub(r"[\s\-]+", "_", str(variable or "").strip().lower())
    aliases = {
        "tree_cover": "tree_cover",
        "tree_cover_density": "tree_cover",
        "trees": "tree_cover",
        "temperature": "temperature",
        "average_temperature": "temperature",
        "precipitation": "precipitation",
        "rainfall": "precipitation",
        "rain": "precipitation",
        "evapotranspiration": "evapotranspiration",
        "evaporation": "evapotranspiration",
        "biodiversity": "biodiversity",
        "species_richness": "biodiversity",
        "number_of_species": "biodiversity",
        "grass": "grassland",
        "grassland": "grassland",
        "land_use": "land_use",
        "productivity": "productivity",
        "land_imperviousness": "land_imperviousness",
        "imperviousness": "land_imperviousness",
    }
    return aliases.get(value, value)


def _repair_addition_after_but(question, data):
    """
    Repair the explicit construction:
      'a scenario with X and a scenario with X but Y'

    Keep X in both scenarios when X is explicitly present in the second
    scenario's text. Keep Y only in scenario_b when Y is introduced after
    'but' and is not part of scenario_a's text. This repair is deliberately
    limited to the recognizable wording pattern.
    """
    q = (question or "").strip()
    match = re.search(
        r"\bscenario\s+with\s+(.*?)\s+and\s+"
        r"(?:a\s+)?scenario\s+with\s+(.*?)\s+but\s+"
        r"(.+?)[.!?]*$",
        q,
        flags=re.IGNORECASE,
    )
    if not match:
        return data

    scenario_a_text, scenario_b_shared_text, additional_text = match.groups()
    variables_in_a_text = _canonical_variable_in_text(scenario_a_text)
    variables_in_b_shared_text = _canonical_variable_in_text(
        scenario_b_shared_text
    )
    variables_in_addition = (
        _canonical_variable_in_text(additional_text) - variables_in_a_text
    )

    scenario_a = data.get("scenario_a", [])
    scenario_b = data.get("scenario_b", [])

    # If the LLM wrongly put the additional 'but Y' modification into A,
    # remove it there only when the question text does not mention Y in A.
    data["scenario_a"] = [
        mod for mod in scenario_a
        if _canonical_variable_name(mod.get("variable"))
        not in variables_in_addition
    ]

    # Restore explicitly shared modifications from A into B, but only when
    # the variable is stated in the second scenario's pre-'but' clause.
    present_in_b = {
        _canonical_variable_name(mod.get("variable"))
        for mod in scenario_b
    }
    for mod in data["scenario_a"]:
        canonical = _canonical_variable_name(mod.get("variable"))
        if (
            canonical in variables_in_a_text
            and canonical in variables_in_b_shared_text
            and canonical not in present_in_b
        ):
            data["scenario_b"].append(copy.deepcopy(mod))
            present_in_b.add(canonical)

    return data


def _normalize_target(question, data):
    """
    Enforce the documented target default while preserving explicit targets.
    """
    q = (question or "").lower()

    if re.search(r"\bresilien(?:ce|t)\\b", q):
        data["target"] = "ecosystem_resilience"
    elif re.search(r"\becosystem health\\b|\\bhealth of the ecosystem\\b", q):
        data["target"] = "ecosystem_health"
    elif re.search(r"\brisk\\b", q):
        data["target"] = "ecosystem_risk"
    else:
        data["target"] = "ecosystem_risk"

    return data


def _normalize_comparison_data(data, question=""):
    """
    Deterministic normalization of the LLM extraction.

    The LLM performs semantic extraction. This function enforces the
    extraction contract for known, unambiguous cases; it does not perform
    arithmetic or model calculations.
    """
    data = _repair_addition_after_but(question, data)
    data = _normalize_target(question, data)

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

            elif modification_type == "qualitative":
                # Direction belongs in 'direction', not 'magnitude'.
                magnitude = modification.get("magnitude")
                direction = modification.get("direction")
                if (isinstance(magnitude, str) and isinstance(direction, str)
                        and magnitude.lower() == direction.lower()):
                    modification["magnitude"] = None

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
        parsed_json,
        question=question,
    )

    return ComparisonExtraction.model_validate(
        parsed_json
    )