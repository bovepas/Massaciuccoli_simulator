import json
import re

from tools.llm_client import call_llm
from extraction.drivers.schema import DriversExtraction
from utils.feature_mapping import FEATURE_LABELS


PROMPT_PATH = "/app/extraction/drivers/drivers_extraction.txt"


def load_drivers_prompt() -> str:
    """
    Load the Drivers extraction prompt from disk.
    """

    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


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
        f"Drivers extractor returned invalid JSON:\n{raw_response}"
    )



def _normalise_spaces(text: str) -> str:
    """Case-insensitive text normalisation used for exact column matching."""
    return re.sub(r"\s+", " ", str(text or "").strip()).lower()


def _match_explicit_dataset_target(question: str):
    """Return a full canonical dataset column if it is explicitly named.

    Longest-first matching prevents a shorter label from taking precedence over
    a longer column label that contains the same concepts.
    """
    question_norm = _normalise_spaces(question)
    canonical_names = sorted(
        (name for name in FEATURE_LABELS.keys() if name != "ecosystem_risk"),
        key=len,
        reverse=True,
    )
    # First honour complete canonical column names explicitly quoted by the user.
    for canonical in canonical_names:
        quoted_variants = (
            f'"{_normalise_spaces(canonical)}"',
            f"'{_normalise_spaces(canonical)}'",
            f'“{_normalise_spaces(canonical)}”',
            f'‘{_normalise_spaces(canonical)}’',
        )
        if any(quoted in question_norm for quoted in quoted_variants):
            return canonical

    # Then honour a complete canonical name wherever it appears.
    for canonical in canonical_names:
        if _normalise_spaces(canonical) in question_norm:
            return canonical

    # Common paraphrases for dataset columns that explicitly represent change
    # over a decade. These rules avoid collapsing a time-varying feature into
    # its static base variable when the wording is not an exact column label.
    has_change_word = bool(re.search(r"\b(change|changes|changing|dynamics)\b", question_norm))
    has_decade_reference = bool(re.search(
        r"\b(past|last|previous)\s+(?:decade|10 years|ten years)\b|"
        r"\bover the past decade\b|\bduring the past decade\b|"
        r"\bin the past decade\b|\bover the last decade\b|"
        r"\bduring the last decade\b|\bin the last decade\b",
        question_norm,
    ))
    if has_change_word and has_decade_reference:
        if "grassland" in question_norm and "presence" in question_norm:
            return "Change in grassland presence in the past decade"
        if "tree cover" in question_norm:
            return "Change in tree cover density in the past decade"
        if "land use" in question_norm or "land cover" in question_norm:
            return "Change in land use and cover in the past decade"
    return None


def _direction_outside_explicit_target(question: str, target: str) -> str:
    """Infer direction only from words outside a quoted/canonical target label."""
    residual = _normalise_spaces(question)
    target_norm = _normalise_spaces(target)
    if target_norm:
        residual = residual.replace(target_norm, " ", 1)

    increase_pattern = re.compile(
        r"\b(increase|increased|increases|increasing|rise|rises|rising|"
        r"grow|grows|growing|growth|higher|gain|gains|gained|improve|"
        r"improvement|positive change)\b",
        re.IGNORECASE,
    )
    decrease_pattern = re.compile(
        r"\b(decrease|decreased|decreases|decreasing|decline|declines|"
        r"declining|fall|falls|falling|lower|loss|lose|loses|losing|"
        r"reduction|reduce|reduces|reduced|reducing|negative change|"
        r"degradation|collapse|drop|drops|dropping)\b",
        re.IGNORECASE,
    )
    has_increase = bool(increase_pattern.search(residual))
    has_decrease = bool(decrease_pattern.search(residual))
    if has_increase and not has_decrease:
        return "increase"
    if has_decrease and not has_increase:
        return "decrease"
    return "unspecified"

def extract_drivers(question: str) -> DriversExtraction:
    """
    Extract a structured Drivers query from a natural-language question.

    Semantic interpretation is delegated to the LLM.
    """

    prompt = load_drivers_prompt()
    prompt = prompt.replace("{{QUERY}}", question)

    raw_response = call_llm(prompt)

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw_response)
    print("======================================\n")

    data = _extract_json(raw_response)

    # Priority 1: if the user explicitly names a complete dataset column,
    # preserve that exact canonical target rather than the LLM's shorter alias.
    explicit_target = _match_explicit_dataset_target(question)
    if isinstance(data, dict):
        if explicit_target:
            data["target"] = explicit_target
            target_for_direction = explicit_target
        else:
            target_for_direction = str(data.get("target", ""))

        # Direction is reconstructed from explicit words in the question,
        # excluding the target label. This prevents the LLM from interpreting
        # the word "change" within a column name as an increase or decrease.
        data["direction"] = _direction_outside_explicit_target(
            question,
            target_for_direction,
        )

    try:
        return DriversExtraction.model_validate(data)

    except Exception as exc:
        raise ValueError(
            "Drivers extractor returned JSON with an invalid schema:\n"
            f"{data}"
        ) from exc