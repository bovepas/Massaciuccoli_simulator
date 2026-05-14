# knowledge/rag_assessment.py

"""
RAG Assessment — v1 (modular + SHAP-aware)

✔ Uses shared retriever
✔ Uses shared llm client
✔ Task-specific prompt
✔ Injects SHAP drivers into explanation
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

    print("\n[RAG-ASSESSMENT] START")

    # ==================================================
    # 🔥 QUERY (più generica → migliore retrieval)
    # ==================================================

    query = (
        "lake ecosystem risk hydrology biodiversity nutrient loading "
        "climate change ecosystem processes"
    )

    print("[DEBUG] RAG query:", query)

    retrieved, _ = retrieve_documents(query)
    context = build_context(retrieved)

    print("[RAG] Retrieved documents:", len(retrieved))
    print("[RAG] Context length:", len(context))

    # ==================================================
    # 🔥 SHAP → testo
    # ==================================================

    driver_text = ", ".join(drivers[:3])

    # ==================================================
    # 🔥 PROMPT (QUI STA LA MAGIA)
    # ==================================================

    prompt = f"""
You are an environmental scientist.

TASK:
Explain how key environmental drivers influence ecosystem risk in a lake ecosystem.

DRIVERS:
{driver_text}

RULES:
- Use scientific and academic tone
- Integrate ecological mechanisms (hydrology, biodiversity, resilience)
- Do NOT list variables explicitly
- Do NOT mention models or SHAP
- Be concise (3–4 sentences)

Question:
{question}

Context:
{context}

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

        print("[RAG-ASSESSMENT] END\n")

        return cleaned

    except Exception as e:
        print("[RAG-ASSESSMENT ERROR]", e)
        return fallback()