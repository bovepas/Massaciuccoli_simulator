import json
import re

from tools.llm_client import call_llm
from extraction.enm.schema import ENMExtraction


PROMPT_PATH = "/app/extraction/enm/enm_extraction.txt"


def load_enm_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_json(raw_response: str) -> dict:
    text = raw_response.strip()

    # Caso 1: risposta JSON pura
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Caso 2: JSON dentro un blocco markdown
    match = re.search(
        r"```(?:json)?\s*(\{.*\})\s*```",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if match:
        return json.loads(match.group(1))

    # Caso 3: JSON contenuto in altro testo
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        return json.loads(text[start:end + 1])

    raise ValueError(
        "ENM extractor returned invalid JSON:\n"
        f"{raw_response}"
    )


def extract_enm(question: str) -> ENMExtraction:
    prompt = load_enm_prompt()
    prompt = prompt.replace("{{QUERY}}", question)

    raw_response = call_llm(prompt)

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw_response)
    print("======================================\n")

    data = _extract_json(raw_response)

    try:
        return ENMExtraction.model_validate(data)
    except Exception as exc:
        raise ValueError(
            "ENM extractor returned JSON with an invalid schema:\n"
            f"{data}"
        ) from exc