# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Pipeline — v3 (robust + demo-ready)

✔ Uses centralized llm_client
✔ Context trimming (important for LLM quality)
✔ Output validation
✔ Strong fallback
✔ Clean debug
"""

import re
from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm


# ======================================================
# CONFIG
# ======================================================

DEBUG = False

MAX_CONTEXT_CHARS = 3000  # 🔥 limit context size


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
# CONTEXT BUILDER (🔥 NEW)
# ======================================================

def build_context(retrieved):

    if not retrieved:
        return ""

    chunks = [r["text"] for r in retrieved]

    context = "\n\n".join(chunks)

    # 🔥 trim if too long
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]

    return context


# ======================================================
# OUTPUT VALIDATION (🔥 NEW)
# ======================================================

def is_valid_output(text: str):

    if not text:
        return False

    text = text.strip()

    if len(text) < 30:
        return False

    if "Interpretation not available" in text:
        return False

    return True


# ======================================================
# FALLBACK
# ======================================================

def fallback_answer(question: str):

    return (
        "The system retrieved relevant environmental information, "
        "but a detailed explanation could not be generated at this time."
    )


# ======================================================
# MAIN
# ======================================================

def generate_answer(question: str, extra_prompt: str = ""):

    retrieved, _ = retrieve_documents(question)

    context = build_context(retrieved)

    prompt = f"""
You are an environmental scientist.

TASK:
Provide a clear and concise explanation based ONLY on the provided context.

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
    debug_print("[RAG] Context length:", len(context))

    if DEBUG:
        preview = prompt[:1000] + "..." if len(prompt) > 1000 else prompt
        debug_print("\n[RAG] --- PROMPT PREVIEW ---")
        debug_print(preview)

    # ================= LLM =================
    try:

        raw = call_llm(prompt)

        debug_print("\n[RAG] --- RAW LLM OUTPUT ---")
        debug_print(raw)

        # 🔥 VALIDATION
        if not is_valid_output(raw):
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