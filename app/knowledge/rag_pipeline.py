"""
Massaciuccoli Digital Twin
RAG Pipeline — Clean Scientific Extraction (Final Demo)
"""

import requests
import os
from knowledge.retriever import retrieve_documents


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

LLM_MODEL = "llama3:8b"

LOW_CONFIDENCE_THRESHOLD = 500


def call_llm(prompt: str) -> str:

    response = requests.post(
        OLLAMA_GENERATE_URL,
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}
        }
    )

    response.raise_for_status()
    return response.json()["response"].strip()


def generate_answer(question: str):

    retrieved, avg_distance = retrieve_documents(question)

    if not retrieved:
        return "No scientific evidence found in the knowledge base."

    context_blocks = []

    for r in retrieved:
        context_blocks.append(
            f"DOCUMENT: {r['source']} | PAGE: {r['page']}\n{r['text']}"
        )

    context = "\n\n".join(context_blocks)

    confidence_note = ""

    if avg_distance > LOW_CONFIDENCE_THRESHOLD:
        confidence_note = (
            "\n\n⚠ Note: Retrieved evidence shows low semantic similarity to the query."
        )

    # 🔥 FINAL PROMPT
    extractive_prompt = f"""
You are a scientific extraction system.

TASK:
List the main environmental pressures affecting biodiversity.

RULES:
- Use ONLY the provided context
- Do NOT use phrases like "based on the context"
- Do NOT explain reasoning
- Do NOT mention datasets or metadata
- Provide ONLY a bullet list
- Each bullet = one pressure

Question:
{question}

Context:
{context}

Answer:
"""

    answer = call_llm(extractive_prompt)

    return answer.strip() + confidence_note