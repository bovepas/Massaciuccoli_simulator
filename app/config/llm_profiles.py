# app/config/llm_profiles.py

import os

# ======================================================
# LLM STYLES
# ======================================================

LLM_STYLES = {

    "qwen": "scientific",

    "scout": "scientific",

    "gemini": "scientific",

    "llama70b": "scientific",

    "llama3.2": "scientific"
}

# ======================================================
# ACTIVE PROFILE
# ======================================================

LLM_PROFILE = os.getenv(
    "LLM_PROFILE",
    "llama3.2"
)

# ======================================================
# ACTIVE STYLE
# ======================================================

LLM_STYLE = LLM_STYLES.get(
    LLM_PROFILE,
    "scientific"
)