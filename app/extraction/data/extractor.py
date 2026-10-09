import json
import os
import re
import requests

from extraction.data.schema import DataExtraction


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
    "data_extraction.txt"
)


def _load_prompt():
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def _extract_json(text):
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


def extract_data(question: str) -> DataExtraction:

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

    raw_text = data.get(
        "response",
        ""
    ).strip()

    if not raw_text:
        raise ValueError(
            "Empty response from Ollama"
        )

    parsed_json = _extract_json(
        raw_text
    )

    return DataExtraction.model_validate(
        parsed_json
    )