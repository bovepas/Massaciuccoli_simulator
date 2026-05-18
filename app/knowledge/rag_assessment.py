# -*- coding: utf-8 -*-

"""
RAG Assessment — v2 (STRONG KB INJECTION)

✔ Retrieval guidato dai driver
✔ Prompt che forza uso della KB
✔ Output più “knowledge-grounded”
✔ Fallback sicuro
"""

from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm
import re


# ======================================================
# CONFIG
# ======================================================

MAX_CONTEXT_CHARS = 3000
DEBUG = False


# ======================================================
# UTILS
# ======================================================

def clean_text(text: str):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def build_context(retrieved):
    if not retrieved:
        return ""

    chunks = [r["text"] for r in retrieved]
    context = "\n\n".join(chunks)

    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]

    return context


def is_valid_output(text: str):
    if not text:
        return False
    if len(text.strip()) < 30:
        return False
    return True


def fallback():
    return (
        "Environmental drivers influence ecosystem risk through complex interactions "
        "involving hydrology, nutrient dynamics, and biodiversity processes."
    )


# ======================================================
# MAIN
# ======================================================

def generate_assessment_explanation(question: str, drivers: list):

    print("\n[RAG-ASSESSMENT v2] START")

    # ==================================================
    # 🔥 DRIVERS → QUERY DINAMICA (FIX PRINCIPALE)
    # ==================================================

    driver_text = ", ".join(drivers[:3])

    query = f"""
    lake ecosystem risk interactions {driver_text} hydrology biodiversity nutrient dynamics
    """

    print("[DEBUG] RAG query:", query)

    retrieved, _ = retrieve_documents(query)
    context = build_context(retrieved)

    print("[RAG] Retrieved documents:", len(retrieved))
    print("[RAG] Context length:", len(context))

    # ==================================================
    # 🔥 PROMPT FORZATO (USA LA KB)
    # ==================================================

    prompt = f"""
You are an environmental scientist.

TASK:
Explain how key environmental drivers influence ecosystem risk in a lake ecosystem.

DRIVERS:
{driver_text}

CONTEXT FROM SCIENTIFIC KNOWLEDGE BASE:
{context}

IMPORTANT:
- You MUST use the context to support your explanation
- Base your reasoning on the retrieved scientific content
- Integrate ecological mechanisms (hydrology, biodiversity, resilience)
- Do NOT list variables explicitly
- Do NOT mention models or SHAP
- Be concise (3–4 sentences)

Question:
{question}

Answer:
"""

    # ==================================================
    # LLM
    # ==================================================

    try:
        raw = call_llm(prompt)

        print("[RAG] RAW:", raw)

        if not is_valid_output(raw):
            return fallback()

        cleaned = clean_text(raw)

        print("[RAG-ASSESSMENT v2] END\n")

        return cleaned

    except Exception as e:
        print("[RAG-ASSESSMENT ERROR]", e)
        return fallback()