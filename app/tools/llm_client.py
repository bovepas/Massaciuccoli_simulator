# -*- coding: utf-8 -*-

"""
Centralized LLM Client (Ollama) — v5, role-aware model selection.

Legacy behaviour is preserved unless
LLM_USE_SELECTED_MODEL_FOR_INTERPRETATION_ONLY=true.

When that flag is enabled:
- call_llm(prompt) uses LLM_BASE_* (parsing/extraction/default calls).
- call_llm(prompt, role="interpretation") uses the selected
  LLM_MODEL / LLM_ENDPOINT / LLM_MAX_PREDICT configuration.

Routing based on embeddings is independent from this client.
"""

import requests
import os
import time
import re
from datetime import datetime

from utils.logger import (
    start_timer,
    end_timer,
    log_data,
)


# ======================================================
# SELECTED MODEL CONFIGURATION
# ======================================================

MODEL = os.getenv("LLM_MODEL", "llama3.2:3b")
GENERATE_URL = os.getenv(
    "LLM_ENDPOINT",
    "http://localhost:11434/api/generate",
)
MAX_PREDICT = int(os.getenv("LLM_MAX_PREDICT", "2048"))

# ======================================================
# BASE MODEL CONFIGURATION
# ======================================================

BASE_MODEL = os.getenv("LLM_BASE_MODEL", "llama3.2:3b")
BASE_GENERATE_URL = os.getenv(
    "LLM_BASE_ENDPOINT",
    "http://ollama:11434/api/generate",
)
BASE_MAX_PREDICT = int(os.getenv("LLM_BASE_MAX_PREDICT", "512"))

USE_SELECTED_MODEL_FOR_INTERPRETATION_ONLY = (
    os.getenv(
        "LLM_USE_SELECTED_MODEL_FOR_INTERPRETATION_ONLY",
        "false",
    ).strip().lower()
    in {"1", "true", "yes", "on"}
)

# ======================================================
# FALLBACK CONFIGURATION
# ======================================================

FALLBACK_PROFILE = os.getenv("LLM_FALLBACK_PROFILE", "fallback")
FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "llama3.2:3b")
FALLBACK_ENDPOINT = os.getenv(
    "LLM_FALLBACK_ENDPOINT",
    "http://ollama:11434/api/generate",
)
FALLBACK_MAX_PREDICT = int(os.getenv("LLM_FALLBACK_MAX_PREDICT", "256"))

# ======================================================
# PERFORMANCE SETTINGS
# ======================================================

DEBUG = True
DEBUG_SAVE_PROMPTS = True
MAX_RETRIES = 3
RETRY_DELAY = 1
TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))
TEMPERATURE = 0
DEBUG = True
DEBUG_SAVE_PROMPTS = True
DEBUG_RESPONSE_DETAILS = True  # Diagnostic of raw Ollama response fields
# ======================================================
# PERSISTENT SESSION
# ======================================================

SESSION = requests.Session()


def debug_print(*args):
    if DEBUG:
        print("[LLM CLIENT]", *args)


def _select_model_config(role: str = "default") -> tuple[str, str, int]:
    """Select model configuration for a call without changing legacy roles."""
    normalized_role = (role or "default").strip().lower()
    if normalized_role not in {"default", "parsing", "extraction", "interpretation"}:
        raise ValueError(
            "Unsupported LLM call role {!r}; use default, parsing, extraction, "
            "or interpretation.".format(role)
        )

    if USE_SELECTED_MODEL_FOR_INTERPRETATION_ONLY:
        if normalized_role == "interpretation":
            return MODEL, GENERATE_URL, MAX_PREDICT
        return BASE_MODEL, BASE_GENERATE_URL, BASE_MAX_PREDICT

    # Legacy mode: selected LLM_MODEL is used for all calls.
    return MODEL, GENERATE_URL, MAX_PREDICT


def call_fallback_llm(prompt: str) -> str:
    print("\n========================================")
    print("PRIMARY LLM UNAVAILABLE")
    print(f"Switching to fallback profile: {FALLBACK_PROFILE}")
    print(f"Model   : {FALLBACK_MODEL}")
    print(f"Endpoint: {FALLBACK_ENDPOINT}")
    print("========================================\n")

    response = SESSION.post(
        FALLBACK_ENDPOINT,
        json={
            "model": FALLBACK_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": TEMPERATURE,
                "num_predict": FALLBACK_MAX_PREDICT,
            },
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    if DEBUG_RESPONSE_DETAILS:
        print("[LLM CLIENT] Response keys:", list(data.keys()))
        print("[LLM CLIENT] response type:", type(data.get("response")).__name__)
        print("[LLM CLIENT] response length:", len(data.get("response") or ""))
        print("[LLM CLIENT] thinking type:", type(data.get("thinking")).__name__)
        print("[LLM CLIENT] thinking length:", len(data.get("thinking") or ""))
        print("[LLM CLIENT] done_reason:", data.get("done_reason"))
        print("[LLM CLIENT] eval_count:", data.get("eval_count"))

    output = data.get("response", "").strip()

    output = re.sub(
        r"<think>.*?</think>", "", output,
        flags=re.DOTALL | re.IGNORECASE,
    )
    output = re.sub(
        r"<think>.*", "", output,
        flags=re.DOTALL | re.IGNORECASE,
    ).strip()
    return output if output else "No response generated."


def call_llm(prompt: str, role: str = "default") -> str:
    """Generate a response using the selected model role.

    Existing call_llm(prompt) usages remain valid. In interpretation-only mode
    they use the base model; RAG/explanation call sites must explicitly pass
    role="interpretation" to use the model selected by LLM_MODEL.
    """
    model, generate_url, max_predict = _select_model_config(role)

    log_data("llm_prompt_length", len(prompt))
    debug_print("Role:", role)
    debug_print("Interpretation-only mode:", USE_SELECTED_MODEL_FOR_INTERPRETATION_ONLY)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            debug_print(f"Attempt {attempt}/{MAX_RETRIES}")
            debug_print("Model:", model)
            debug_print("Endpoint:", generate_url)

            request_prompt = prompt
            if not request_prompt.rstrip().endswith("/no_think"):
                request_prompt = request_prompt.rstrip() + "\n\n/no_think"

            if DEBUG_SAVE_PROMPTS:
                folder = os.path.join("debug_prompts", model.replace(":", "_"))
                os.makedirs(folder, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(folder, f"{timestamp}.txt")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(request_prompt)
                print(
                    f"[LLM CLIENT] Prompt saved -> {filename} "
                    f"({len(request_prompt)} chars)"
                )

            # Qwen3.5 can spend the entire num_predict budget generating
            # hidden reasoning when called through /api/generate unless the
            # thinking flag is sent at the TOP LEVEL of the JSON payload.
            # Putting "think" inside "options" is not equivalent and may be
            # silently ignored by Ollama. Restrict this behavior to the
            # selected interpretation role so parsing/extraction behavior is
            # unchanged.
            payload = {
                "model": model,
                "prompt": request_prompt,
                "stream": False,
                "options": {
                    "temperature": TEMPERATURE,
                    "num_predict": max_predict,
                    "num_ctx": 16384,
                },
            }
            normalized_role = (role or "default").strip().lower()
            if (
                normalized_role == "interpretation"
                and model.strip().lower().startswith(("qwen3.5", "gemma4"))

            ):
                payload["think"] = False
                debug_print("Qwen3.5 interpretation: API thinking disabled")

            start_timer("ollama_request")
            response = SESSION.post(
                generate_url,
                json=payload,
                timeout=TIMEOUT,
            )
            end_timer("ollama_request")

            start_timer("ollama_response_processing")
            response.raise_for_status()
            data = response.json()

            if DEBUG_RESPONSE_DETAILS:
                print("[LLM CLIENT] Response keys:", list(data.keys()))
                print("[LLM CLIENT] response type:", type(data.get("response")).__name__)
                print("[LLM CLIENT] response length:", len(data.get("response") or ""))
                print("[LLM CLIENT] thinking type:", type(data.get("thinking")).__name__)
                print("[LLM CLIENT] thinking length:", len(data.get("thinking") or ""))
                print("[LLM CLIENT] done_reason:", data.get("done_reason"))
                print("[LLM CLIENT] eval_count:", data.get("eval_count"))

            log_data("llm_done_reason", data.get("done_reason"))
            log_data("llm_eval_count", data.get("eval_count"))

            raw_output = data.get("response", "").strip()
            output = re.sub(
                r"<think>.*?</think>", "", raw_output,
                flags=re.DOTALL | re.IGNORECASE,
            )
            output = re.sub(
                r"<think>.*", "", output,
                flags=re.DOTALL | re.IGNORECASE,
            ).strip()

            if raw_output != output:
                debug_print("Removed reasoning block")
            if not output and "<think>" in raw_output:
                debug_print("Output contained only reasoning.")
            if data.get("done_reason") == "length":
                print("⚠️ Output truncated (MAX_PREDICT reached)")

            end_timer("ollama_response_processing")
            log_data("llm_output_length", len(output))
            if not output:
                return "No response generated."
            return output

        except Exception as exc:
            # Ensure a failed request does not leave the request timer open.
            end_timer("ollama_request")
            print(f"\n🔥 LLM CLIENT ERROR (attempt {attempt}):")
            print(exc)
            if attempt < MAX_RETRIES:
                print(f"[LLM CLIENT] Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                print("[LLM CLIENT] All retries failed.")

    try:
        return call_fallback_llm(prompt)
    except Exception as exc:
        print("\n🔥 FALLBACK LLM UNAVAILABLE")
        print(exc)
        return "Interpretation not available (LLM unavailable)."
