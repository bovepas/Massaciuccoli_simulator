# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG Chat — v2 (centralized LLM + safe + docker-ready)

✔ Uses centralized llm_client for generation
✔ Keeps embedding logic (Ollama)
✔ Works in Docker + local
✔ Safe fallback
"""

import requests
import chromadb
import os

from tools.llm_client import call_llm


# ======================================================
# CONFIG
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

# 🔥 embedding endpoint (keep separate)
if os.path.exists("/.dockerenv"):
    OLLAMA_EMBED_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434") + "/api/embeddings"
else:
    OLLAMA_EMBED_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434") + "/api/embeddings"

EMBED_MODEL = "nomic-embed-text"

TOP_K = 8
SIMILARITY_THRESHOLD = 320


# ======================================================
# CHROMA
# ======================================================

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)


# ======================================================
# EMBEDDING
# ======================================================

def get_embedding(text):

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBED_MODEL,
                "prompt": text
            },
            timeout=60
        )

        response.raise_for_status()
        return response.json()["embedding"]

    except Exception as e:
        print("[EMBED ERROR]", e)
        return None


# ======================================================
# QUERY EXPANSION
# ======================================================

def expand_query(query):

    expansions = [query]

    q = query.lower()

    if "pressioni" in q or "antropiche" in q:
        expansions += [
            "human impact on Massaciuccoli lake",
            "land use change",
            "agricultural runoff",
            "nutrient loading",
            "urbanization",
            "pollution sources"
        ]

    if "eutrof" in q:
        expansions += [
            "nutrient enrichment",
            "phosphorus concentration",
            "nitrogen loading",
            "algal bloom",
            "water quality degradation"
        ]

    return expansions


# ======================================================
# RETRIEVAL
# ======================================================

def retrieve_documents(query):

    if collection.count() == 0:
        return []

    expanded_queries = expand_query(query)
    all_results = []

    for q in expanded_queries:

        embedding = get_embedding(q)
        if embedding is None:
            continue

        results = collection.query(
            query_embeddings=[embedding],
            n_results=TOP_K
        )

        for i in range(len(results["documents"][0])):

            distance = results["distances"][0][i]

            if distance <= SIMILARITY_THRESHOLD:
                all_results.append({
                    "text": results["documents"][0][i],
                    "distance": distance
                })

    unique_results = {r["text"]: r for r in all_results}.values()
    sorted_results = sorted(unique_results, key=lambda x: x["distance"])

    return [r["text"] for r in sorted_results]


# ======================================================
# PROMPT
# ======================================================

def build_prompt(query, documents):

    context = "\n\n".join(documents[:5])

    return f"""
You are an expert in lake ecosystems.

Answer the question using ONLY the provided context.
If the answer is not contained in the context, say so clearly.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""


# ======================================================
# MAIN GENERATION
# ======================================================

def generate_chat_answer(query):

    print("\n[RAG-CHAT] START")

    docs = retrieve_documents(query)

    print("[RAG-CHAT] Retrieved docs:", len(docs))

    if not docs:
        return "No relevant information found in the knowledge base."

    prompt = build_prompt(query, docs)

    try:

        raw = call_llm(prompt)

        if not raw or "Interpretation not available" in raw:
            return "The system could not generate a reliable answer from the available data."

        return raw.strip()

    except Exception as e:

        print("[RAG-CHAT ERROR]", e)

        return "An error occurred while generating the answer."