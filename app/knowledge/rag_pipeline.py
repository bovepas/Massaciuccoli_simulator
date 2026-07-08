# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Pipeline — v5
(timing instrumentation + retrieval observability)

✔ Retrieval timing
✔ Context building timing
✔ Prompt sizing observability
✔ LLM timing
✔ Full RAG profiling
✔ Keeps existing architecture unchanged
"""

import re

from knowledge.retriever import retrieve_documents

from tools.llm_client import call_llm

from utils.logger import (

    start_timer,
    end_timer,
    log_data
)

from utils.feature_semantics import (
    build_semantic_context
)


# ======================================================
# CONFIG
# ======================================================

DEBUG = True

USE_SEMANTIC_CONTEXT = True

MAX_CONTEXT_CHARS = 1500


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

    text = re.sub(
        r"\(id\s*\d+\)",
        "",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ======================================================
# CONTEXT BUILDER
# ======================================================

def build_context(retrieved):

    if not retrieved:
        return ""

    chunks = [

        r["text"]

        for r in retrieved
    ]

    context = "\n\n".join(
        chunks
    )

    if len(context) > MAX_CONTEXT_CHARS:

        context = context[
            :MAX_CONTEXT_CHARS
        ]

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

    # --------------------------------------------------
    # LLM REFUSALS
    # --------------------------------------------------

    bad_patterns = [

        "no mention",

        "not present in the context",

        "cannot answer",

        "not enough information",

        "outside the scope"
    ]

    if any(

        p in text

        for p in bad_patterns
    ):

        return False

    return True


# ======================================================
# FALLBACK
# ======================================================

def fallback_answer(question: str):

    return (

        "The system could not retrieve "
        "sufficient domain-specific "
        "information to provide a grounded "
        "answer. This may happen if the "
        "knowledge base is not fully "
        "initialized or if the query is "
        "outside the available scientific "
        "context."
    )


# ======================================================
# MAIN
# ======================================================

def generate_answer(
    question: str,
    features=None,
    extra_prompt: str = ""
):

    # ==================================================
    # TOTAL RAG TIMER
    # ==================================================

    start_timer("rag_total")

    # ==================================================
    # RETRIEVAL
    # ==================================================

    start_timer("retrieval")

    retrieved, _ = retrieve_documents(
        question
    )

    if DEBUG:

        print("\n[RAG] Retrieved documents:")

        for i, doc in enumerate(retrieved, 1):

            print(f"\n--- Document {i} ---")

            print(
                f"{doc['source']} "
                f"(page {doc['page']}) "
                f"distance={doc['distance']:.2f}"
            )

            print(doc["text"][:300])

    end_timer("retrieval")

    # ==================================================
    # HARD STOP
    # ==================================================

    if not retrieved:

        debug_print(
            "[RAG] No documents "
            "retrieved → fallback"
        )

        end_timer("rag_total")

        return fallback_answer(question)

    # ==================================================
    # CONTEXT BUILDING
    # ==================================================

    start_timer("context_building")

    context = build_context(
        retrieved
    )

    end_timer("context_building")

    # --------------------------------------------------
    # EMPTY CONTEXT
    # --------------------------------------------------

    if not context.strip():

        debug_print(
            "[RAG] Empty context "
            "after build → fallback"
        )

        end_timer("rag_total")

        return fallback_answer(question)

    # ==================================================
    # PROMPT BUILDING
    # ==================================================

    start_timer("prompt_building")

    # ==================================================
    # SEMANTIC CONTEXT
    # ==================================================

    semantic_context = ""

    if USE_SEMANTIC_CONTEXT and features:


         semantic_context = build_semantic_context(
             features
         )
        
         debug_print(
             "\n[RAG] Semantic context:"
         )

         debug_print(
             semantic_context
         )
        

    prompt = f"""
You are an environmental scientist assisting
the Massaciuccoli Digital Twin.

TASK:
Provide a clear and concise scientific interpretation.

Use the retrieved scientific knowledge to interpret
the environmental model outputs provided below.

Do not introduce unsupported ecological claims.

{semantic_context}

{extra_prompt}

User Question:
{question}

Retrieved Scientific Knowledge:
{context}

Scientific Interpretation:
"""

    end_timer("prompt_building")

    # ==================================================
    # OBSERVABILITY
    # ==================================================

    log_data(
        "retrieved_documents",
        len(retrieved)
    )

    log_data(
        "context_length",
        len(context)
    )

    log_data(
        "prompt_length",
        len(prompt)
    )

    # ==================================================
    # DEBUG
    # ==================================================

    debug_print(
        "\n================ "
        "RAG DEBUG "
        "================"
    )

    debug_print(
        "[RAG] Question:",
        question
    )

    debug_print(
        "[RAG] Retrieved documents:",
        len(retrieved)
    )

    debug_print(
        "[RAG] Context length:",
        len(context)
    )

    debug_print(
        "[RAG] Prompt length:",
        len(prompt)
    )

    if DEBUG:

        preview = (

            prompt[:1000] + "..."

            if len(prompt) > 1000

            else prompt
        )

        debug_print(
            "\n[RAG] --- "
            "PROMPT PREVIEW ---"
        )

        debug_print(preview)

    # ==================================================
    # LLM
    # ==================================================

    try:

        start_timer("llm_generation")

        raw = call_llm(prompt)

        end_timer("llm_generation")

        debug_print(
            "\n[RAG] --- "
            "RAW LLM OUTPUT ---"
        )

        debug_print(raw)

        # ==================================================
        # VALIDATION
        # ==================================================

        start_timer("output_validation")

        if not is_valid_output(raw):

            debug_print(
                "[RAG] Invalid "
                "LLM output → fallback"
            )

            end_timer("output_validation")

            end_timer("rag_total")

            return fallback_answer(question)

        cleaned = clean_text(raw)

        end_timer("output_validation")

        # ==================================================
        # FINAL DEBUG
        # ==================================================

        debug_print(
            "\n[RAG] --- "
            "CLEANED OUTPUT ---"
        )

        debug_print(cleaned)

        debug_print(
            "==========================================\n"
        )

        end_timer("rag_total")

        return cleaned

    except Exception as e:

        print(
            "\n🔥 RAG-PIPELINE ERROR:"
        )

        print(e)

        end_timer("rag_total")

        return fallback_answer(question)