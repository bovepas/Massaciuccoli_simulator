# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin

Task: CHAT

Scientific Question Answering over the
Massaciuccoli Knowledge Base.

This task is executed only when no specialized
Digital Twin task matches the user's request.

It provides direct access to the scientific
knowledge base underlying the Digital Twin.
"""

from knowledge.rag_chat import generate_chat_answer


# ======================================================
# MAIN
# ======================================================

def handle_chat(question):

    print("\n========== SCIENTIFIC QA ==========")

    try:

        response = generate_chat_answer(
            question
        )

    except Exception as e:

        print(
            "[CHAT ERROR]",
            e
        )

        response = (
            "The scientific knowledge base "
            "could not be queried."
        )

    return {

        "type": "chat",

        "summary":
            "Scientific knowledge query",

        "data": {},

        "drivers": [],

        "interpretation":
            response

    }