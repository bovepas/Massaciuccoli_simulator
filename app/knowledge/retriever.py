# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Engine Retriever - Robust SAFE Version
"""

import requests
import chromadb
from typing import List, Dict, Tuple
import os


# ======================================================
# CONFIG
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"

EMBED_MODEL = "nomic-embed-text"

TOP_K = 6


# ======================================================
# CHROMA CLIENT
# ======================================================

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(COLLECTION_NAME)


# ======================================================
# EMBEDDING (🔥 SAFE)
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

        # 🔥 CRITICAL FIX
        if not emb or not isinstance(emb, list):
            return None

        return emb

    except Exception as e:
        print(f"⚠️ Embedding error: {e}")
        return None


# ======================================================
# QUERY EXPANSION
# ======================================================

def expand_query(query: str) -> List[str]:

    return [
        query,
        f"ecosistema lago Massaciuccoli {query}",
        f"dinamiche ambientali {query}",
    ]


# ======================================================
# RETRIEVAL (🔥 SAFE)
# ======================================================

def retrieve_documents(query: str) -> Tuple[List[Dict], float]:

    if collection.count() == 0:
        return [], 9999.0

    expanded_queries = expand_query(query)
    all_results = []

    for q in expanded_queries:

        embedding = get_embedding(q)

        # 🔥 FIX: skip invalid embeddings
        if embedding is None:
            continue

        try:
            results = collection.query(
                query_embeddings=[embedding],
                n_results=TOP_K
            )
        except Exception as e:
            print(f"⚠️ Chroma query error: {e}")
            continue

        if not results or not results.get("documents"):
            continue

        for i in range(len(results["documents"][0])):

            metadata = results["metadatas"][0][i] or {}

            all_results.append({
                "text": results["documents"][0][i],
                "source": metadata.get("source", "unknown"),
                "page": metadata.get("page", "N/A"),
                "distance": results["distances"][0][i]
            })

    # Deduplicate
    unique_results = {r["text"]: r for r in all_results}.values()

    # Sort
    sorted_results = sorted(unique_results, key=lambda x: x["distance"])
    top_results = sorted_results[:TOP_K]

    if not top_results:
        return [], 9999.0

    avg_distance = sum(r["distance"] for r in top_results) / len(top_results)

    return top_results, avg_distance