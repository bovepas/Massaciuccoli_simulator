# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Pipeline — v4 (robust + anti-empty + anti-llm-failure)

✔ Handles empty retrieval
✔ Prevents LLM useless responses
✔ Strong fallback
✔ Clean debug
"""

import re
from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm


# ======================================================
# CONFIG
# ======================================================

DEBUG = True

MAX_CONTEXT_CHARS = 3000


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
# CONTEXT BUILDER
# ======================================================

def build_context(retrieved):

    if not retrieved:
        return ""

    chunks = [r["text"] for r in retrieved]

    context = "\n\n".join(chunks)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]

    return context


# ======================================================
# OUTPUT VALIDATION
# ======================================================

def is_valid_output(text: str):

    if not text:
        return False

    text = text.strip().lower()

    if len(text) < 30:
        return False

    # 🔥 intercetta rifiuti LLM
    bad_patterns = [
        "no mention",
        "not present in the context",
        "cannot answer",
        "not enough information",
        "outside the scope"
    ]

    if any(p in text for p in bad_patterns):
        return False

    return True


# ======================================================
# FALLBACK (🔥 MIGLIORATO)
# ======================================================

def fallback_answer(question: str):

    return (
        "The system could not retrieve sufficient domain-specific information "
        "to provide a grounded answer. This may happen if the knowledge base "
        "is not fully initialized or if the query is outside the available "
        "scientific context."
    )


# ======================================================
# MAIN
# ======================================================

def generate_answer(question: str, extra_prompt: str = ""):

    retrieved, _ = retrieve_documents(question)

    # ======================================================
    # 🔥 HARD STOP: NO CONTEXT
    # ======================================================

    if not retrieved:
        debug_print("[RAG] No documents retrieved → fallback")
        return fallback_answer(question)

    context = build_context(retrieved)

    # sicurezza extra
    if not context.strip():
        debug_print("[RAG] Empty context after build → fallback")
        return fallback_answer(question)

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

        # ======================================================
        # 🔥 VALIDATION (ANTI-FAIL)
        # ======================================================

        if not is_valid_output(raw):
            debug_print("[RAG] Invalid LLM output → fallback")
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