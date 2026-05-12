# -*- coding: utf-8 -*-

"""
Centralized LLM Client (Ollama)

✔ Single point for all LLM calls
✔ Works in Docker and local
✔ Safe fallback (no crash)
✔ Debug logging
"""

import requests
import os


# ======================================================
# CONFIG
# ======================================================

MODEL = os.getenv("LLM_MODEL", "llama3:8b")

# Auto-detect environment
if os.path.exists("/.dockerenv"):
    BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
else:
    BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

GENERATE_URL = f"{BASE_URL}/api/generate"

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print("[LLM CLIENT]", *args)


# ======================================================
# MAIN CALL
# ======================================================

def call_llm(prompt: str) -> str:

    try:
        debug_print("Calling model:", MODEL)
        debug_print("Endpoint:", GENERATE_URL)

        response = requests.post(
            GENERATE_URL,
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0
                }
            },
            timeout=120
        )

        response.raise_for_status()

        output = response.json().get("response", "").strip()

        if not output:
            return "No response generated."

        return output

    except Exception as e:

        print("\n🔥 LLM CLIENT ERROR:")
        print(e)

        # SAFE FALLBACK
        return "Interpretation not available (LLM unavailable)."