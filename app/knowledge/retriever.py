# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Engine Retriever - v4 (AUTO-KB INIT)
"""

import requests
import chromadb
from typing import List, Dict, Tuple
import os

# 🔥 NEW
from knowledge.ingest_pdfs import ensure_kb_ready


# ======================================================
# CONFIG
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"

EMBED_MODEL = "nomic-embed-text"

TOP_K = 8

DEBUG = True


def debug_print(*args):
    if DEBUG:
        print("[RETRIEVER]", *args)


# ======================================================
# CHROMA CLIENT
# ======================================================

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)


# ======================================================
# EMBEDDING
# ======================================================

def get_embedding(text: str):

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBED_MODEL,
                "prompt": text
            }
        )

        response.raise_for_status()
        data = response.json()

        emb = data.get("embedding", [])

        if not emb or not isinstance(emb, list):
            debug_print("Invalid embedding for:", text)
            return None

        return emb

    except Exception as e:
        debug_print("Embedding error:", e)
        return None


# ======================================================
# QUERY EXPANSION
# ======================================================

def expand_query(query: str) -> List[str]:

    q = query.lower()

    expansions = [query]

    expansions.append(f"ecosystem risk factors {q}")
    expansions.append(f"lake ecosystem dynamics {q}")

    if "temperature" in q or "precipitation" in q:
        expansions.append(f"climate change impact lake ecosystem {q}")

    if "biodiversity" in q or "species" in q:
        expansions.append(f"biodiversity ecosystem resilience {q}")

    if "land" in q or "tree" in q or "grassland" in q:
        expansions.append(f"land use change ecosystem impact {q}")

    return expansions


# ======================================================
# RETRIEVAL
# ======================================================

def retrieve_documents(query: str) -> Tuple[List[Dict], float]:

    debug_print("Query:", query)

    # ======================================================
    # 🔥 AUTO-KB INIT
    # ======================================================

    ensure_kb_ready()

    # 🔥 reload collection dopo ingest (importantissimo)
    global collection
    collection = client.get_or_create_collection(COLLECTION_NAME)

    if collection.count() == 0:
        debug_print("Empty collection AFTER INIT")
        return [], 9999.0

    expanded_queries = expand_query(query)

    debug_print("Expanded queries:", expanded_queries)

    all_results = []

    # ======================================================
    # STEP 1 — RETRIEVE EVERYTHING (NO FILTER)
    # ======================================================

    for q in expanded_queries:

        embedding = get_embedding(q)

        if embedding is None:
            continue

        try:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=TOP_K
            )
        except Exception as e:
            debug_print("Chroma query error:", e)
            continue

        if not results or not results.get("documents"):
            continue

        for i in range(len(results["documents"][0])):

            distance = results["distances"][0][i]
            metadata = results["metadatas"][0][i] or {}

            all_results.append({
                "text": results["documents"][0][i],
                "source": metadata.get("source", "unknown"),
                "page": metadata.get("page", "N/A"),
                "distance": distance
            })

    # ======================================================
    # STEP 2 — UNIQUE RESULTS
    # ======================================================

    unique_results = list({r["text"]: r for r in all_results}.values())

    if not unique_results:
        debug_print("No results found")
        return [], 9999.0

    # ======================================================
    # STEP 3 — AVG DISTANCE
    # ======================================================

    avg_distance = sum(r["distance"] for r in unique_results) / len(unique_results)

    debug_print("Avg distance (pre-filter):", avg_distance)

    # ======================================================
    # STEP 4 — ADAPTIVE FILTER
    # ======================================================

    filtered_results = [
        r for r in unique_results
        if r["distance"] <= avg_distance * 3
    ]

    debug_print(f"After adaptive filter: {len(filtered_results)} docs")

    # fallback safety
    if not filtered_results:
        debug_print("Filter too strict → fallback to all results")
        filtered_results = unique_results

    # ======================================================
    # STEP 5 — SORT + TOP_K
    # ======================================================

    sorted_results = sorted(filtered_results, key=lambda x: x["distance"])
    top_results = sorted_results[:TOP_K]

    debug_print(f"Final retrieved: {len(top_results)} documents")

    avg_distance_final = sum(r["distance"] for r in top_results) / len(top_results)

    debug_print("Avg distance (final):", avg_distance_final)

    return top_results, avg_distance_final