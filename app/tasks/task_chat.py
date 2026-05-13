# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Task: CHAT (v3 - RAG + LLM fallback safe)
"""

from knowledge.rag_chat import generate_chat_answer
from tools.llm_client import call_llm


# ======================================================
# LLM FALLBACK
# ======================================================

def generate_fallback_chat(question):

    prompt = f"""
You are the Massaciuccoli Digital Twin assistant.

IMPORTANT RULES:
- Be friendly and natural
- DO NOT invent capabilities
- ONLY mention what the system actually does:
  - ecosystem risk assessment
  - biodiversity analysis
  - environmental scenario evaluation
- If greeted, introduce yourself briefly
- Keep answers concise

USER QUESTION:
{question}

ANSWER:
"""

    try:
        response = call_llm(prompt)

        if response:
            return response.strip()

    except Exception as e:
        print("[LLM FALLBACK ERROR]", e)

    return (
        "Hello! I'm the Massaciuccoli Digital Twin assistant. "
        "I can help you explore ecosystem risk, biodiversity, and environmental changes."
    )


# ======================================================
# MAIN (⚠️ QUESTA È QUELLA CHE SERVE ALL'ORCHESTRATOR)
# ======================================================

def handle_chat(question):

    print("\n========== CHAT TASK ==========")

    try:

        rag_response = generate_chat_answer(question)

        if (
            not rag_response or
            "No relevant information" in rag_response
        ):
            print("[CHAT] Switching to LLM fallback")
            response = generate_fallback_chat(question)
        else:
            response = rag_response

    except Exception as e:

        print("[CHAT ERROR]", e)

        response = generate_fallback_chat(question)

    return {
        "type": "chat",
        "summary": "General interaction",
        "data": {},
        "drivers": [],
        "interpretation": response
    }