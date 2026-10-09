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


def extract_importance(question: str) -> ImportanceExtraction:
    prompt = load_importance_prompt()
    prompt = prompt.replace("{{QUERY}}", question)

    raw_response = call_llm(prompt)

    print("\n========== RAW LLM RESPONSE ==========")
    print(raw_response)
    print("======================================\n")

    data = _extract_json(raw_response)

    try:
        return ImportanceExtraction.model_validate(data)

    except Exception as exc:
        raise ValueError(
            "Importance extractor returned JSON with an invalid schema:\n"
            f"{data}"
        ) from exc