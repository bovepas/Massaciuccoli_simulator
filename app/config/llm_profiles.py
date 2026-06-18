# app/config/llm_profiles.py

import os

# ======================================================
# LLM STYLES
# ======================================================

LLM_STYLES = {

    "qwen": "narrative",

    "scout": "literal",

    "gemini": "literal",

    "llama70b": "literal"
}

# ======================================================
# ACTIVE PROFILE
# ======================================================

LLM_PROFILE = os.getenv(
    "LLM_PROFILE",
    "qwen"
)

# ======================================================
# ACTIVE STYLE
# ======================================================

LLM_STYLE = LLM_STYLES.get(
    LLM_PROFILE,
    "literal"
)