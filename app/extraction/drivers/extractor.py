import json
import re

from tools.llm_client import call_llm
from extraction.drivers.schema import DriversExtraction


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

    try:
        return DriversExtraction.model_validate(data)

    except Exception as exc:
        raise ValueError(
            "Drivers extractor returned JSON with an invalid schema:\n"
            f"{data}"
        ) from exc