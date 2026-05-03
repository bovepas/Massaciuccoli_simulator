"""
LLM Query Rewriter (STRICT + CLEAN OUTPUT)
"""

import os
import requests
import re


DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_BASE}/api/generate"


def clean_llm_output(text: str) -> str:
    """
    🔥 CRITICAL: remove LLM verbosity
    """

    # remove common prefixes
    text = re.sub(r"(?i)here is.*?:", "", text)
    text = re.sub(r"(?i)this rewritten question.*", "", text)

    # remove quotes
    text = text.strip().strip('"').strip("'")

    # remove newlines
    text = text.replace("\n", " ").strip()

    return text


def rewrite_query(question: str) -> str:
    prompt = f"""
Rewrite this question using ONLY these patterns:

ALLOWED STRUCTURES:
- "compare X and Y"
- "change from A to B"
- "effect of X on Y"
- "impact of X on Y"
- "estimate risk given X"

STRICT RULES:
- Keep original meaning
- DO NOT summarize
- DO NOT generalize
- DO NOT remove comparison structure
- Use the word "compare" if two scenarios are present
- Return ONLY one sentence
- NO explanations
- NO extra text

Q: {question}
A:
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "llama3:8b",
                "prompt": prompt,
                "stream": False
            },
            timeout=20   # 🔥 aumentato (prima era 10)
        )

        data = response.json()

        debug_print("[LLM RAW RESPONSE]:", data)

        if "response" not in data:
            debug_print("[LLM ERROR] Missing 'response' field")
            return question

        raw = data["response"].strip()
        cleaned = clean_llm_output(raw)

        debug_print("[LLM PARSER]")
        debug_print("Original:", question)
        debug_print("Raw:", raw)
        debug_print("Cleaned:", cleaned)

        return cleaned if cleaned else question

    except Exception as e:
        debug_print("[LLM PARSER ERROR]:", str(e))
        return question