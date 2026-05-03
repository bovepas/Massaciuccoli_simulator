"""
Massaciuccoli Digital Twin
RAG Dependency — v5 (uncertainty-aware)
"""

import requests
import os


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

LLM_MODEL = "llama3:8b"

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# LLM CALL
# ======================================================

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


# ======================================================
# PROMPT (🔥 UNCERTAINTY-AWARE)
# ======================================================

def build_prompt(source, target, strength, direction, drivers):

    drivers_text = ""
    if drivers:
        drivers_text = "\nMODEL DRIVERS:\n" + "\n".join([f"- {d}" for d in drivers])

    return f"""
You are a hydrology expert.

RELATION:
{source} → {target} ({strength}, {direction})

{drivers_text}

TASK:
Explain the relationship between these variables.

IMPORTANT:
- If strength is negligible or weak, emphasize uncertainty
- DO NOT present a strong causal mechanism
- Describe the effect as small, unclear, or data-dependent

RULES:
- Use cautious language (e.g., "suggests", "may indicate")
- Only mention physical processes if clearly justified
- Avoid deterministic explanations
- Keep explanation realistic
- Max 2 sentences
"""


# ======================================================
# FALLBACK
# ======================================================

def fallback_response(source, target, strength, direction):

    if strength == "negligible":
        return (
            f"The model does not detect a meaningful relationship between {source} and {target}. "
            f"Any observed effect is very small and may reflect noise rather than a consistent pattern."
        )

    return (
        f"The relationship between {source} and {target} appears {direction}, "
        f"but should be interpreted as a general tendency rather than a strong causal link."
    )


# ======================================================
# MAIN
# ======================================================

def generate_dependency_explanation(source, target, strength, direction, drivers=None):

    print("\n[RAG-DEPENDENCY] START")

    try:

        # 🔥 HARD RULE: skip LLM if negligible
        if strength == "negligible":
            return fallback_response(source, target, strength, direction)

        prompt = build_prompt(source, target, strength, direction, drivers)

        debug_print("\n[RAG-DEPENDENCY] Prompt:")
        debug_print(prompt)

        raw = call_llm(prompt)

        debug_print("\n[RAG-DEPENDENCY] Raw output:")
        debug_print(raw)

        final = raw.strip().replace("\n", " ")

        debug_print("\n[RAG-DEPENDENCY] Final output:")
        debug_print(final)

        return final

    except Exception as e:

        print("\n🔥 RAG-DEPENDENCY ERROR:")
        print(e)

        return fallback_response(source, target, strength, direction)

    finally:
        print("[RAG-DEPENDENCY] END\n")