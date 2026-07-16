# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin

RAG Chat — v5

Scientific Question Answering over the
Massaciuccoli Knowledge Base.

Uses the shared retrieval infrastructure
and a dedicated prompt builder.
"""

import os
import re

from knowledge.retriever import retrieve_documents
from tools.llm_client import call_llm


# ======================================================
# CONFIG
# ======================================================

DEBUG = True

MAX_CONTEXT_CHARS = 2000

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

PROMPTS_DIR = os.path.join(
    BASE_DIR,
    "prompts"
)

MODELS_DIR = os.path.join(
    PROMPTS_DIR,
    "models"
)

STYLES_DIR = os.path.join(
    PROMPTS_DIR,
    "styles"
)

TASKS_DIR = os.path.join(
    PROMPTS_DIR,
    "tasks"
)


# ======================================================
# UTILS
# ======================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def build_context(retrieved):

    if not retrieved:
        return ""

    context = "\n\n".join(
        r["text"] for r in retrieved
    )

    if len(context) > MAX_CONTEXT_CHARS:

        context = context[:MAX_CONTEXT_CHARS]

    return context


# ======================================================
# PROMPT BUILDER
# ======================================================

def load_prompt(path):

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:

        return f.read().strip()


def build_chat_prompt(question, context):

    base = load_prompt(
        os.path.join(
            MODELS_DIR,
            "base.txt"
        )
    )

    style = load_prompt(
        os.path.join(
            STYLES_DIR,
            "scientific.txt"
        )
    )

    task = load_prompt(
        os.path.join(
            TASKS_DIR,
            "chat.txt"
        )
    )

    prompt = f"""
[BASE]

{base}

[STYLE]

{style}

[TASK]

{task}

QUESTION:
{question}

SCIENTIFIC KNOWLEDGE:
{context}
"""

    if DEBUG:

        print(
            "\n========== COMPOSED PROMPT ==========\n"
        )

        print(prompt)

        print(
            "\n=====================================\n"
        )

    return prompt


# ======================================================
# MAIN
# ======================================================

def generate_chat_answer(question):

    print("\n[RAG-CHAT v5] START")

    retrieved, _ = retrieve_documents(
        question
    )

    print(
        "[RAG-CHAT] Retrieved documents:",
        len(retrieved)
    )

    if DEBUG:

        for i, doc in enumerate(retrieved, 1):

            print(
                f"\n----- DOCUMENT {i} -----"
            )

            print(
                doc["text"][:600]
            )

            print(
                "------------------------"
            )

    context = build_context(
        retrieved
    )

    if not context:

        return (
            "The scientific knowledge base "
            "does not contain information relevant "
            "to this question."
        )

    prompt = build_chat_prompt(
        question,
        context
    )

    print(
        "[RAG-CHAT] Prompt length:",
        len(prompt)
    )

    try:

        raw = call_llm(
            prompt
        )

        if (
            not raw
            or
            "Interpretation not available"
            in raw
        ):

            return (
                "The available scientific knowledge "
                "does not provide sufficient evidence "
                "to answer this question."
            )

        answer = clean_text(
            raw
        )

        print(
            "\n[RAG-CHAT] END"
        )

        return answer

    except Exception as e:

        print(
            "[RAG-CHAT ERROR]",
            e
        )

        return (
            "An error occurred while querying "
            "the scientific knowledge base."
        )