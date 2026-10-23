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

    The first scenario contains X. The second contains the explicitly
    repeated X plus the additional Y introduced after "but".

    The LLM may incorrectly place Y in scenario_a. When that happens,
    move the already-extracted Y modification to scenario_b rather than
    dropping it. This repair never invents a modification or a value.
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
    if not isinstance(scenario_a, list) or not isinstance(scenario_b, list):
        return data

    # Collect additional modifications before removing any misassigned ones.
    # The extraction already contains their semantic details; we only repair
    # scenario ownership and do not infer numeric values.
    additional_modifications = [
        mod for mod in scenario_a
        if isinstance(mod, dict)
        and _canonical_variable_name(mod.get("variable")) in variables_in_addition
    ]

    # Remove the "but Y" modification from A when Y was not mentioned in A.
    data["scenario_a"] = [
        mod for mod in scenario_a
        if not (
            isinstance(mod, dict)
            and _canonical_variable_name(mod.get("variable")) in variables_in_addition
        )
    ]

    # Ensure the explicitly repeated condition X is present in B, if the LLM
    # omitted it there but extracted it in A. Never copy unrelated variables.
    present_in_b = {
        _canonical_variable_name(mod.get("variable"))
        for mod in scenario_b if isinstance(mod, dict)
    }
    for mod in data["scenario_a"]:
        if not isinstance(mod, dict):
            continue
        canonical = _canonical_variable_name(mod.get("variable"))
        if (
            canonical in variables_in_a_text
            and canonical in variables_in_b_shared_text
            and canonical not in present_in_b
        ):
            data["scenario_b"].append(copy.deepcopy(mod))
            present_in_b.add(canonical)

    # Move the extracted additional condition to B. If B already contains a
    # modification for that variable, preserve B's version and avoid a clash.
    for mod in additional_modifications:
        canonical = _canonical_variable_name(mod.get("variable"))
        if canonical not in present_in_b:
            data["scenario_b"].append(copy.deepcopy(mod))
            present_in_b.add(canonical)

    return data


def _deduplicate_modifications_by_variable(modifications):
    """
    For a single-variable alternative, retain at most one extracted
    modification per canonical variable. Prefer the first occurrence:
    scenario order in the raw extraction is not treated as evidence that
    repeated copies represent distinct requested changes.
    """
    result = []
    seen = set()

    for modification in modifications:
        if not isinstance(modification, dict):
            continue

        canonical = _canonical_variable_name(
            modification.get("variable")
        )
        if canonical in seen:
            continue

        seen.add(canonical)
        result.append(modification)

    return result


def _repair_explicit_or_alternatives(question, data):
    """
    Repair a narrow, unambiguous comparison pattern:
      "...: variable A ... or variable B ..."

    Assign the already-extracted modification for each named variable to
    its corresponding scenario. No modification or numeric value is invented.
    """
    q = (question or "").strip()

    # Only handle a colon-introduced pair of alternatives, e.g.
    # "Which ...: biodiversity -30% or tree cover -30%?"
    match = re.search(
        r":\s*(.+?)\s+\bor\b\s+(.+?)[.!?]*\s*$",
        q,
        flags=re.IGNORECASE,
    )
    if not match:
        return data

    left_text, right_text = match.groups()
    left_variables = _canonical_variable_in_text(left_text)
    right_variables = _canonical_variable_in_text(right_text)

    # Leave ambiguous or multi-variable alternatives untouched.
    if (
        len(left_variables) != 1
        or len(right_variables) != 1
        or left_variables == right_variables
    ):
        return data

    left_variable = next(iter(left_variables))
    right_variable = next(iter(right_variables))

    all_modifications = []
    for key in ("scenario_a", "scenario_b"):
        scenario = data.get(key, [])
        if isinstance(scenario, list):
            all_modifications.extend(
                mod for mod in scenario if isinstance(mod, dict)
            )

    left_modifications = [
        mod for mod in all_modifications
        if _canonical_variable_name(mod.get("variable")) == left_variable
    ]
    right_modifications = [
        mod for mod in all_modifications
        if _canonical_variable_name(mod.get("variable")) == right_variable
    ]

    # Do not fabricate missing modifications.
    if not left_modifications or not right_modifications:
        return data

    # Each alternative explicitly names one variable, so duplicate copies
    # of that variable are extraction noise, not additional requested changes.
    data["scenario_a"] = _deduplicate_modifications_by_variable(
        left_modifications
    )
    data["scenario_b"] = _deduplicate_modifications_by_variable(
        right_modifications
    )
    return data


def _normalize_target(question, data):
    """
    Enforce the documented target default while preserving explicit targets.
    """
    q = (question or "").lower()

    if re.search(r"\bresilien(?:ce|t)\b", q):
        data["target"] = "ecosystem_resilience"
    elif re.search(r"\becosystem health\b|\bhealth of the ecosystem\b", q):
        data["target"] = "ecosystem_health"
    elif re.search(r"\brisk\b", q):
        data["target"] = "ecosystem_risk"
    else:
        data["target"] = "ecosystem_risk"

    return data


def _remove_exact_duplicate_modifications(modifications):
    """Remove byte-for-byte-equivalent semantic modifications within a scenario."""
    result = []
    seen = set()

    for modification in modifications:
        if not isinstance(modification, dict):
            result.append(modification)
            continue

        signature = (
            _canonical_variable_name(modification.get("variable")),
            modification.get("modification_type"),
            str(modification.get("original_expression") or "").strip().lower(),
            modification.get("value"),
            modification.get("from_value"),
            modification.get("to_value"),
            modification.get("direction"),
            modification.get("unit"),
        )
        if signature in seen:
            continue

        seen.add(signature)
        result.append(modification)

    return result


def _normalize_comparison_data(data, question=""):
    """
    Deterministic normalization of the LLM extraction.

    The LLM performs semantic extraction. This function enforces the
    extraction contract for known, unambiguous cases; it does not perform
    arithmetic or model calculations.
    """
    data = _repair_addition_after_but(question, data)
    data = _repair_explicit_or_alternatives(question, data)
    data = _normalize_target(question, data)

    for scenario_key in ("scenario_a", "scenario_b"):
        scenario = data.get(scenario_key, [])
        if isinstance(scenario, list):
            scenario = _remove_exact_duplicate_modifications(scenario)
            data[scenario_key] = scenario

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
    print("COMPARISON RAW JSON:", json.dumps(parsed_json, indent=2))

    parsed_json = _normalize_comparison_data(
        parsed_json,
        question=question,
    )
    print("COMPARISON NORMALIZED JSON:", json.dumps(parsed_json, indent=2))

    if not isinstance(parsed_json, dict):
        raise ValueError("Comparison extraction must be a JSON object.")

    for scenario_key in ("scenario_a", "scenario_b"):
        scenario = parsed_json.get(scenario_key)
        if not isinstance(scenario, list) or not scenario:
            raise ValueError(
                f"Comparison extraction produced an empty or invalid "
                f"{scenario_key}. Raw extraction: "
                f"{json.dumps(parsed_json, ensure_ascii=False)}"
            )

    return ComparisonExtraction.model_validate(parsed_json)