# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Pipeline — v2 (centralized LLM + safe + docker-ready)

✔ Uses centralized llm_client
✔ Works in Docker + local
✔ Safe fallback (no crash)
✔ Clean debug
"""

import re
from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm


# ======================================================
# CONFIG
# ======================================================

DEBUG = False  # toggle unico


# ======================================================
# DEBUG PRINT
# ======================================================

def debug_print(*args):
    if DEBUG:
        print(*args)


# ======================================================
# CLEAN TEXT
# ======================================================

def clean_text(text: str):

    if not text:
        return ""

    text = re.sub(r"\(id\s*\d+\)", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ======================================================
# FALLBACK
# ======================================================

def fallback_answer(question: str):

    return "The system retrieved relevant information, but a detailed explanation is currently unavailable."


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
    try:

        raw = call_llm(prompt)

        debug_print("\n[RAG] --- RAW LLM OUTPUT ---")
        debug_print(raw)

        if not raw or "Interpretation not available" in raw:
            return fallback_answer(question)

        cleaned = clean_text(raw)

        debug_print("\n[RAG] --- CLEANED OUTPUT ---")
        debug_print(cleaned)
        debug_print("==========================================\n")

        return cleaned

    except Exception as e:

        print("\n🔥 RAG-PIPELINE ERROR:")
        print(e)

        return fallback_answer(question)