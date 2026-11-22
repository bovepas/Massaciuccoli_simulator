import json
import re

from tools.llm_client import call_llm
from extraction.importance.schema import ImportanceExtraction


PROMPT_PATH = "/app/extraction/importance/importance_extraction.txt"


def load_importance_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_json(raw_response: str) -> dict:
    text = raw_response.strip()

    # Plain JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # JSON inside markdown code block
    match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if match:
        return json.loads(match.group(1))

    # JSON embedded in additional text
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end + 1])

    raise ValueError(
        f"Importance extractor returned invalid JSON:\n{raw_response}"
    )



# Direction is intentionally determined with explicit linguistic rules rather
# than delegated to the LLM. The default is "all": only an unambiguous request
# about increasing or reducing ecosystem risk narrows the analysis.
_DECREASE_PATTERNS = (
    r"\breduc(?:e|es|ed|ing|tion)\b.{0,50}\brisk\b",
    r"\blower(?:s|ed|ing)?\b.{0,50}\brisk\b",
    r"\bdecreas(?:e|es|ed|ing)\b.{0,50}\brisk\b",
    r"\bmitigat(?:e|es|ed|ing|ion)\b.{0,50}\brisk\b",
    r"\brisk\s+(?:reduction|mitigation)\b",
    r"\brisk\s+(?:is|be|being|was|were|would be|could be)\s+(?:reduced|lowered|decreased|mitigated)\b",
    r"\b(?:lower|reduced|decreased|mitigated)\s+ecosystem\s+risk\b",
    r"\bassociated\s+with\s+(?:a\s+)?(?:lower|reduced|decreased)\s+(?:ecosystem\s+)?risk\b",
)

_INCREASE_PATTERNS = (
    r"\bincreas(?:e|es|ed|ing)\b.{0,50}\brisk\b",
    r"\brais(?:e|es|ed|ing)\b.{0,50}\brisk\b",
    r"\bwors(?:en|ens|ened|ening)\b.{0,50}\brisk\b",
    r"\baggravat(?:e|es|ed|ing)\b.{0,50}\brisk\b",
    r"\brisk\s+(?:increase|worsening|aggravation)\b",
    r"\brisk\s+(?:is|be|being|was|were|would be|could be)\s+(?:increased|raised|worsened|aggravated)\b",
    r"\b(?:higher|increased|worsened)\s+ecosystem\s+risk\b",
    r"\bassociated\s+with\s+(?:a\s+)?(?:higher|increased)\s+(?:ecosystem\s+)?risk\b",
)


def _has_local_negation(text: str, match_start: int) -> bool:
    """Ignore a directional phrase when it is explicitly negated just before it."""
    prefix = text[max(0, match_start - 45):match_start]
    return bool(re.search(
        r"\b(?:not|no|never|without|cannot|can't|dont|don't|doesn't|isn't|aren't)"
        r"(?:\W+\w+){0,3}\W*$",
        prefix,
    ))


def _has_direction(text: str, patterns: tuple[str, ...]) -> bool:
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            if not _has_local_negation(text, match.start()):
                return True
    return False


def infer_direction(question: str) -> str:
    """Return increase/decrease only when the requested risk direction is explicit."""
    normalized = re.sub(r"[-–—]", " ", question.lower())
    decrease = _has_direction(normalized, _DECREASE_PATTERNS)
    increase = _has_direction(normalized, _INCREASE_PATTERNS)

    # Contradictory or ambiguous directional wording must not narrow results.
    if decrease == increase:
        return "all"
    return "decrease" if decrease else "increase"

def extract_importance(question: str) -> ImportanceExtraction:
    prompt = load_importance_prompt()
    prompt = prompt.replace("{{QUERY}}", question)

    raw_response = call_llm(prompt)

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw_response)
    print("======================================\n")

    data = _extract_json(raw_response)

    # The LLM supplies top_k and focus. Direction is overwritten by the
    # deterministic classifier so an LLM interpretation cannot silently
    # filter the task to only positive or negative model impacts.
    data["direction"] = infer_direction(question)
    print(f"[IMPORTANCE] Deterministic direction: {data['direction']}")

    try:
        return ImportanceExtraction.model_validate(data)

    except Exception as exc:
        raise ValueError(
            "Importance extractor returned JSON with an invalid schema:\n"
            f"{data}"
        ) from exc