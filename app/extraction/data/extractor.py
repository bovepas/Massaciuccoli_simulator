import json
import os
import re
import requests

from extraction.data.schema import DataExtraction
from semantic_variable_catalog import classify_data_query_intent


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


# Catalog-category questions have a deterministic source of truth. Do not ask
# the LLM to invent a variable name for a category such as harmful forces or
# fragile conditions. The generic inventory path is intentionally left as-is
# so the existing all-variables workflow is unchanged.
_CATALOG_RELATION_MARKERS = (
    "effect of", "effects of", "impact of", "impact on", "influence",
    "affect", "affects", "correlation", "correlate", "drivers of",
    "contributes", "cause", "causes", "increase risk", "reduce risk",
    "risk under a scenario", "how does", "how do", "what happens if",
)


def _catalog_intent_for_question(question: str):
    intent = classify_data_query_intent(question)
    if not intent or intent == "dataset_inventory":
        return None

    q = " ".join((question or "").lower().split())
    if any(marker in q for marker in _CATALOG_RELATION_MARKERS):
        return None

    return intent


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
    # Deterministic category recognition avoids unreliable LLM extraction for
    # taxonomies already defined in semantic_variable_catalog.py.
    catalog_intent = _catalog_intent_for_question(question)
    if catalog_intent:
        return DataExtraction(
            intent="data_query",
            variables=[],
            catalog_intent=catalog_intent,
        )

    # Keep the existing LLM extraction route for explicit variable requests
    # and the current dataset-inventory route.
    prompt_template = _load_prompt()
    prompt = prompt_template.replace("{{QUERY}}", question)

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
        raise ValueError("Empty response from Ollama")

    parsed_json = _extract_json(raw_text)
    return DataExtraction.model_validate(parsed_json)
