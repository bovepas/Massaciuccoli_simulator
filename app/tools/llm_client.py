# -*- coding: utf-8 -*-

"""
Centralized LLM Client (Ollama) — v4

✔ Centralized model management
✔ Faster HTTP reuse with Session()
✔ Timing instrumentation
✔ Ollama latency observability
✔ Retry mechanism
✔ Better responsiveness
✔ Easy model switching
✔ Debug logging
"""

import requests
import os
import time

from utils.logger import (

    start_timer,
    end_timer,
    log_data
)


# ======================================================
# CONFIG
# ======================================================

MODEL = os.getenv(
    "LLM_MODEL",
    "llama3.2:3b"
)

# ======================================================
# ENVIRONMENT DETECTION
# ======================================================

if os.path.exists("/.dockerenv"):

    BASE_URL = os.getenv(

        "OLLAMA_BASE_URL",

        "http://ollama:11434"
    )

else:

    BASE_URL = os.getenv(

        "OLLAMA_BASE_URL",

        "http://localhost:11434"
    )

GENERATE_URL = f"{BASE_URL}/api/generate"

DEBUG = True

# ======================================================
# PERFORMANCE SETTINGS
# ======================================================

MAX_RETRIES = 3

RETRY_DELAY = 1

TIMEOUT = 60

MAX_PREDICT = 256

TEMPERATURE = 0

# ======================================================
# PERSISTENT SESSION
# ======================================================

SESSION = requests.Session()


def debug_print(*args):

    if DEBUG:
        print("[LLM CLIENT]", *args)


# ======================================================
# MAIN CALL
# ======================================================

def call_llm(prompt: str) -> str:

    # ==================================================
    # OBSERVABILITY
    # ==================================================

    log_data(
        "llm_prompt_length",
        len(prompt)
    )

    for attempt in range(

        1,

        MAX_RETRIES + 1
    ):

        try:

            debug_print(

                f"Attempt "
                f"{attempt}/"
                f"{MAX_RETRIES}"
            )

            debug_print(
                "Model:",
                MODEL
            )

            debug_print(
                "Endpoint:",
                GENERATE_URL
            )

            # ==================================================
            # OLLAMA REQUEST TIMER
            # ==================================================

            start_timer("ollama_request")

            # --------------------------------------------------
            # REQUEST
            # --------------------------------------------------

            response = SESSION.post(

                GENERATE_URL,

                json={

                    "model": MODEL,

                    "prompt": prompt,

                    "stream": False,

                    "options": {

                        "temperature":
                            TEMPERATURE,

                        "num_predict":
                            MAX_PREDICT
                    }
                },

                timeout=TIMEOUT
            )

            end_timer("ollama_request")

            # ==================================================
            # STATUS VALIDATION
            # ==================================================

            start_timer("ollama_response_processing")

            response.raise_for_status()

            data = response.json()

            print(
                "[LLM CLIENT] done_reason:",
                data.get("done_reason")
            )

            print(
                "[LLM CLIENT] eval_count:",
                data.get("eval_count")
            )

            log_data(
                "llm_done_reason",
                data.get("done_reason")
            )

            log_data(
                "llm_eval_count",
                data.get("eval_count")
            )

            output = data.get(
                "response",
                ""
            ).strip()

            if data.get("done_reason") == "length":

                print(
                    "⚠️ Output truncated "
                    "(MAX_PREDICT reached)"
                )

            end_timer(
                "ollama_response_processing"
            )

            # ==================================================
            # OBSERVABILITY
            # ==================================================

            log_data(
                "llm_output_length",
                len(output)
            )

            # --------------------------------------------------
            # EMPTY OUTPUT
            # --------------------------------------------------

            if not output:

                return (
                    "No response generated."
                )

            return output

        except Exception as e:

            end_timer("ollama_request")

            print(

                f"\n🔥 LLM CLIENT ERROR "
                f"(attempt {attempt}):"
            )

            print(e)

            # --------------------------------------------------
            # RETRY
            # --------------------------------------------------

            if attempt < MAX_RETRIES:

                print(

                    f"[LLM CLIENT] "
                    f"Retrying in "
                    f"{RETRY_DELAY}s..."
                )

                time.sleep(RETRY_DELAY)

            else:

                print(
                    "[LLM CLIENT] "
                    "All retries failed."
                )

    # ======================================================
    # FINAL SAFE FALLBACK
    # ======================================================

    return (

        "Interpretation not available "
        "(LLM unavailable)."
    )