"""
Massaciuccoli Digital Twin
RAG Pipeline — Clean Debug Version
"""

import requests
import os
import re
from knowledge.retriever import retrieve_documents


# ======================================================
# CONFIG
# ======================================================

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_GENERATE_URL = f"{OLLAMA_BASE_URL}/api/generate"

LLM_MODEL = "llama3:8b"

DEBUG = False  # 🔥 toggle unico


# ======================================================
# DEBUG PRINT
# ======================================================

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
# CLEAN TEXT
# ======================================================

def clean_text(text: str):

    text = re.sub(r"\(id\s*\d+\)", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ======================================================
# MAIN
# ======================================================

def generate_answer(question: str, extra_prompt: str = ""):

    retrieved, _ = retrieve_documents(question)

    context = ""
    if retrieved:
        context = "\n\n".join([r["text"] for r in retrieved])

    prompt = f"""
You are an environmental scientist.

TASK:
Explain clearly and concisely.

{extra_prompt}

Question:
{question}

Context:
{context}

Answer:
"""

    # ================= DEBUG =================
    debug_print("\n================ RAG DEBUG ================")
    debug_print("[RAG] Question:", question)
    debug_print("[RAG] Retrieved documents:", len(retrieved))
    debug_print("[RAG] Context length:", len(context), "characters")

    if DEBUG:
        preview = prompt[:1000] + "..." if len(prompt) > 1000 else prompt
        debug_print("\n[RAG] --- PROMPT PREVIEW ---")
        debug_print(preview)

    # ================= LLM =================
    raw = call_llm(prompt)

    debug_print("\n[RAG] --- RAW LLM OUTPUT ---")
    debug_print(raw)

    cleaned = clean_text(raw)

    debug_print("\n[RAG] --- CLEANED OUTPUT ---")
    debug_print(cleaned)
    debug_print("==========================================\n")

    return cleaned