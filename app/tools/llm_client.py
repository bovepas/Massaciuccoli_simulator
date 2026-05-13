# -*- coding: utf-8 -*-

"""
Centralized LLM Client (Ollama) — v2

✔ Single point for all LLM calls
✔ Works in Docker and local
✔ Retry mechanism (important for startup timing)
✔ Safe fallback (no crash)
✔ Debug logging
"""

import requests
import os
import time


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

# 🔥 NEW: retry config (important for Docker startup)
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds


def debug_print(*args):
    if DEBUG:
        print("[LLM CLIENT]", *args)


# ======================================================
# MAIN CALL
# ======================================================

def call_llm(prompt: str) -> str:

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            debug_print(f"Attempt {attempt}/{MAX_RETRIES}")
            debug_print("Model:", MODEL)
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

            print(f"\n🔥 LLM CLIENT ERROR (attempt {attempt}):")
            print(e)

            if attempt < MAX_RETRIES:
                print(f"[LLM CLIENT] Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print("[LLM CLIENT] All retries failed.")

    # 🔥 FINAL SAFE FALLBACK
    return "Interpretation not available (LLM unavailable)."