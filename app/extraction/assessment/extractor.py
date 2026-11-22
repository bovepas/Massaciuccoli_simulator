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


def _validate_assessment_payload(data: dict) -> dict:
    """
    Validate the top-level structure returned by the LLM before normalization
    or Pydantic model validation.

    This check does not repair or infer values: it only reports malformed
    or incomplete extraction payloads with a targeted diagnostic.
    """
    if not isinstance(data, dict):
        raise ValueError(
            "Invalid Assessment extraction: JSON root must be an object "
            f"(received {type(data).__name__})."
        )

    required_fields = ("intent", "target", "scenario")
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        received_keys = list(data.keys())
        raise ValueError(
            "Invalid Assessment extraction: missing required top-level "
            f"field(s): {', '.join(missing_fields)}. "
            f"Received keys: {received_keys[:20]!r}."
        )

    for field in ("intent", "target"):
        if not isinstance(data[field], str) or not data[field].strip():
            raise ValueError(
                "Invalid Assessment extraction: "
                f"'{field}' must be a non-empty string "
                f"(received {data[field]!r})."
            )

    if not isinstance(data["scenario"], list):
        raise ValueError(
            "Invalid Assessment extraction: 'scenario' must be a list "
            f"(received {type(data['scenario']).__name__})."
        )

    for index, modification in enumerate(data["scenario"]):
        if not isinstance(modification, dict):
            raise ValueError(
                "Invalid Assessment extraction: "
                f"scenario[{index}] must be an object "
                f"(received {type(modification).__name__})."
            )

    return data


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




# Semantic aliases used only to anchor each extracted modification to the
# actual user question. This prevents the LLM from supplying a rewritten
# "original_expression" that can then contaminate deterministic parsing.
_VARIABLE_ALIASES = {
    "temperature": ("average temperature", "air temperature", "temperature"),
    "precipitation": ("cumulative precipitation", "precipitation", "rainfall", "rain"),
    "evapotranspiration": ("potential evapotranspiration", "evapotranspiration"),
    "potential evapotranspiration": ("potential evapotranspiration", "evapotranspiration"),
    "biodiversity": ("species richness", "number of species", "biodiversity"),
    "species richness": ("species richness", "number of species", "biodiversity"),
    "species_richness": ("species richness", "number of species", "biodiversity"),
    "tree cover": ("tree cover",),
    "tree_cover": ("tree cover",),
    "grassland": ("grassland cover", "grassland"),
    "land use": ("land use and cover", "land-use change", "land use"),
    "land_use": ("land use and cover", "land-use change", "land use"),
    "land imperviousness": ("land imperviousness", "imperviousness", "urbanization", "sealing"),
    "land_imperviousness": ("land imperviousness", "imperviousness", "urbanization", "sealing"),
    "productivity": ("plant productivity", "vegetation productivity", "productivity"),
}

# Split only when the conjunction introduces a new modification predicate.
# This preserves shared predicates such as "temperature and precipitation
# decrease by 10%" in one source clause.
_MODIFIER_START = (
    r"(?:a|an|the)?\s*(?:(?:slight|moderate|significant|substantial|strong|"
    r"severe|extreme)(?:ly)?\s+)?(?:increase|increases|increased|increasing|"
    r"decrease|decreases|decreased|decreasing|decline|declines|declined|"
    r"declining|reduction|reduces|reduced|loss|gain|rise|rises|rose|growth|"
    r"drop|drops|dropped)\b"
)


def _split_source_clauses(question: str):
    text = re.sub(r"[\r\n]+", " ", question).strip()
    clauses = re.split(r"[;,.!?]+", text)

    aliases = sorted(
        {alias for values in _VARIABLE_ALIASES.values() for alias in values},
        key=len,
        reverse=True,
    )
    subject_first = (
        r"(?:" + "|".join(re.escape(alias) for alias in aliases) + r")"
        r"\s+(?:(?:also|both|significantly|substantially|slightly|"
        r"moderately|strongly|severely|extremely)\s+)*"
        r"(?:is\s+)?(?:increases?|increased|increasing|decreases?|"
        r"decreased|decreasing|declines?|declined|declining|rises?|rose|"
        r"falls?|fell|grows?|grew|reduced|increased)\b"
    )
    split_pattern = rf"\s+(?:and|but|while|whereas)\s+(?=(?:{_MODIFIER_START}|{subject_first}))"

    result = []
    for clause in clauses:
        parts = re.split(split_pattern, clause, flags=re.IGNORECASE)
        result.extend(part.strip() for part in parts if part.strip())
    return result


def _source_clause_for_variable(question: str, variable: str, modification_index: int, scenario_size: int) -> str:
    """Find the user's own clause containing the extracted variable."""
    key = str(variable or "").strip().lower().replace("-", " ")
    aliases = _VARIABLE_ALIASES.get(key)
    if aliases is None:
        aliases = _VARIABLE_ALIASES.get(key.replace(" ", "_"), ())
    clauses = _split_source_clauses(question)

    matches = []
    for clause in clauses:
        lower_clause = clause.lower()
        matched_aliases = [a for a in aliases if re.search(rf"(?<!\w){re.escape(a)}(?!\w)", lower_clause)]
        if matched_aliases:
            # Prefer the longest alias when one phrase contains another.
            matches.append((len(max(matched_aliases, key=len)), clause))

    if matches:
        # If the variable appears in multiple clauses, use the occurrence
        # corresponding to its order in the extracted scenario.
        unique_clauses = []
        for _, clause in matches:
            if clause not in unique_clauses:
                unique_clauses.append(clause)
        return unique_clauses[min(modification_index, len(unique_clauses) - 1)]

    if scenario_size == 1:
        return question.strip()

    raise ValueError(
        f"Cannot anchor extracted Assessment variable {variable!r} "
        "to the original user question. Refusing to apply an unverified modification."
    )

# Qualitative magnitudes supported by qualitative_grounding.py.
# Variants are accepted, but all map to the canonical grounding label.
_QUALITATIVE_MAGNITUDE_PATTERNS = (
    (r"\bslight(?:ly)?\b", "slightly"),
    (r"\bmoderate(?:ly)?\b", "moderately"),
    (r"\bsignificant(?:ly)?\b", "significantly"),
    (r"\bsubstantial(?:ly)?\b", "substantially"),
    (r"\bstrong(?:ly)?\b", "strongly"),
    (r"\bsevere(?:ly)?\b", "severely"),
    (r"\bextreme(?:ly)?\b", "extremely"),
)


def _extract_supported_qualitative_magnitude(expression: str):
    """Return a grounding-supported magnitude explicitly present in the expression."""
    text = expression.lower()
    for pattern, canonical_value in _QUALITATIVE_MAGNITUDE_PATTERNS:
        if re.search(pattern, text):
            return canonical_value
    return None


def _extract_explicit_percentage(expression: str):
    """Extract an explicit percentage or an unambiguous half-change."""
    text = expression.lower()

    decrease_half = (
        "reduced by half", "decreased by half", "cut in half",
        "reduced to half", "decreased to half", "halve", "halved",
    )
    increase_half = (
        "increased by half", "increase by half", "increases by half",
        "raised by half", "increased to one and a half",
    )

    if any(phrase in text for phrase in decrease_half):
        return -50.0, "decrease"
    if any(phrase in text for phrase in increase_half):
        return 50.0, "increase"

    match = re.search(
        r"(?<![\w.])([+-]?\d+(?:[.,]\d+)?)\s*(?:%|percent\b|per\s+cent\b)",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    value = float(match.group(1).replace(",", "."))
    direction = _infer_qualitative_direction(text)
    if direction == "decrease":
        value = -abs(value)
    elif direction == "increase":
        value = abs(value)
    return value, direction


def _apply_numeric_normalization(modification: dict, expression: str) -> bool:
    """
    Reconcile the LLM's modification type/value with explicit numeric evidence.
    Returns True when the expression contains a recognized numeric modification.
    """
    # A categorical transition must not be reinterpreted as a numeric target.
    if (
        modification.get("modification_type") == "state_change"
        and modification.get("to_value") is not None
    ):
        return True

    target = _number_at_target(expression)
    if target is not None:
        value, unit = target
        modification.update({
            "modification_type": "target",
            "value": value,
            "unit": unit or _unit_from_expression(expression, modification.get("unit")),
            "from_value": None,
            "to_value": None,
            "direction": _infer_qualitative_direction(expression),
            "magnitude": None,
        })
        return True

    percentage = _extract_explicit_percentage(expression)
    if percentage is not None:
        value, direction = percentage
        if direction == "decrease":
            value = -abs(value)
        elif direction == "increase":
            value = abs(value)
        modification.update({
            "modification_type": "percentage",
            "value": value,
            "unit": "percent",
            "from_value": None,
            "to_value": None,
            "direction": direction or modification.get("direction"),
            "magnitude": None,
        })
        return True

    absolute_change = _number_after_change_word(expression)
    if absolute_change is not None:
        value, unit = absolute_change
        direction = _infer_qualitative_direction(expression)
        if direction == "decrease":
            value = -abs(value)
        elif direction == "increase":
            value = abs(value)
        modification.update({
            "modification_type": "delta",
            "value": value,
            "unit": unit or _unit_from_expression(expression, modification.get("unit")),
            "from_value": None,
            "to_value": None,
            "direction": direction or modification.get("direction"),
            "magnitude": None,
        })
        return True

    return False


def _normalize_assessment_data(data: dict, question: str) -> dict:
    """
    Normalize the LLM extraction against the original user question.

    The LLM identifies variables and their semantic roles. The source wording
    for each modification is recovered from the user's question itself; the
    LLM-generated original_expression is never trusted as evidence.
    """
    scenario = data.get("scenario", [])
    if not isinstance(scenario, list):
        raise ValueError("Assessment scenario must be a list.")

    for index, modification in enumerate(scenario):
        if not isinstance(modification, dict):
            raise ValueError(f"Invalid Assessment modification at index {index}.")

        source_expression = _source_clause_for_variable(
            question,
            modification.get("variable", ""),
            index,
            len(scenario),
        )

        # Critical: replace the LLM paraphrase with text anchored in the
        # original question BEFORE running any numeric/qualitative rules.
        modification["original_expression"] = source_expression
        modification["interpretation"] = source_expression

        # Repair legacy outputs that put direction in modification_type.
        _normalize_invalid_directional_type(modification)

        # Only explicit numerical evidence in the user's own wording can
        # produce delta/percentage/target modifications.
        has_numeric_modification = _apply_numeric_normalization(
            modification, source_expression
        )

        if has_numeric_modification:
            continue

        # No explicit numeric evidence in the user's wording:
        # normalize the modification as qualitative.
        direction = _infer_qualitative_direction(source_expression)
        if direction is None:
            direction = "change"

        magnitude = _extract_supported_qualitative_magnitude(
            source_expression
        )

        modification.update({
            "modification_type": "qualitative",
            "value": None,
            "unit": None,
            "from_value": None,
            "to_value": None,
            "direction": direction,
            "magnitude": magnitude,
        })

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

    response = call_llm(llm_input, role="extraction")
    print("\n========== RAW LLM RESPONSE ==========")
    print(response)
    print("========== END RAW RESPONSE ==========\n")
    if not response:
        raise ValueError("LLM returned an empty response.")

    data = _extract_json(response)
    data = _validate_assessment_payload(data)

    data = _normalize_assessment_data(data, question)

    return AssessmentExtraction.model_validate(data)
