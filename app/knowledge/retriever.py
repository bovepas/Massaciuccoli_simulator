# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Engine Retriever — v5

✔ Retrieval timing instrumentation
✔ Embedding timing
✔ Chroma timing
✔ Query expansion observability
✔ Retrieval observability
✔ Keeps retrieval logic unchanged
"""

import requests
import chromadb

from typing import List, Dict, Tuple

import os

from knowledge.ingest_pdfs import ensure_kb_ready

from utils.logger import (

    start_timer,
    end_timer,
    log_data
)


# ======================================================
# CONFIG
# ======================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(__file__)
)

CHROMA_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)

COLLECTION_NAME = (
    "massaciuccoli_knowledge"
)

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434"
)

OLLAMA_EMBED_URL = (
    f"{OLLAMA_BASE_URL}/api/embeddings"
)

EMBED_MODEL = "nomic-embed-text"

TOP_K = 6

DEBUG = True


def debug_print(*args):

    if DEBUG:
        print("[RETRIEVER]", *args)


# ======================================================
# CHROMA CLIENT
# ======================================================

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = client.get_or_create_collection(
    COLLECTION_NAME
)


# ======================================================
# EMBEDDING
# ======================================================

def get_embedding(text: str):

    try:

        start_timer("embedding_generation")

        response = requests.post(

            OLLAMA_EMBED_URL,

            json={
                "model": EMBED_MODEL,
                "prompt": text
            }
        )

        response.raise_for_status()

        data = response.json()

        emb = data.get(
            "embedding",
            []
        )

        end_timer("embedding_generation")

        if not emb or not isinstance(
            emb,
            list
        ):

            debug_print(
                "Invalid embedding for:",
                text
            )

            return None

        return emb

    except Exception as e:

        end_timer("embedding_generation")

        debug_print(
            "Embedding error:",
            e
        )

        return None


# ======================================================
# QUERY EXPANSION
# ======================================================

def expand_query(query: str) -> List[str]:

    q = query.lower()

    expansions = [query]

    expansions.append(
        f"ecosystem risk factors {q}"
    )

    expansions.append(
        f"lake ecosystem dynamics {q}"
    )

    if (
        "temperature" in q
        or
        "precipitation" in q
    ):

        expansions.append(
            f"climate change impact "
            f"lake ecosystem {q}"
        )

    if (
        "biodiversity" in q
        or
        "species" in q
    ):

        expansions.append(
            f"biodiversity ecosystem "
            f"resilience {q}"
        )

    if (
        "land" in q
        or
        "tree" in q
        or
        "grassland" in q
    ):

        expansions.append(
            f"land use change "
            f"ecosystem impact {q}"
        )

    return expansions


# ======================================================
# RETRIEVAL
# ======================================================

def retrieve_documents(
    query: str
) -> Tuple[List[Dict], float]:

    start_timer("retriever_total")

    debug_print("Query:", query)

    # ==================================================
    # KB INIT
    # ==================================================

    start_timer("kb_check")

    ensure_kb_ready()

    end_timer("kb_check")

    # --------------------------------------------------
    # RELOAD COLLECTION
    # --------------------------------------------------

    global collection

    collection = client.get_or_create_collection(
        COLLECTION_NAME
    )

    if collection.count() == 0:

        debug_print(
            "Empty collection AFTER INIT"
        )

        end_timer("retriever_total")

        return [], 9999.0

    # ==================================================
    # QUERY EXPANSION
    # ==================================================

    start_timer("query_expansion")

    expanded_queries = expand_query(
        query
    )

    end_timer("query_expansion")

    debug_print(
        "Expanded queries:",
        expanded_queries
    )

    log_data(
        "expanded_queries",
        len(expanded_queries)
    )

    all_results = []

    # ==================================================
    # RETRIEVE
    # ==================================================

    start_timer("retrieval_loop")

    for q in expanded_queries:

        # --------------------------------------------------
        # EMBEDDING
        # --------------------------------------------------

        embedding = get_embedding(q)

        if embedding is None:
            continue

        # --------------------------------------------------
        # CHROMA QUERY
        # --------------------------------------------------

        try:

            start_timer("chroma_query")

            results = collection.query(

                query_embeddings=[embedding],

                n_results=TOP_K
            )

            end_timer("chroma_query")

        except Exception as e:

            end_timer("chroma_query")

            debug_print(
                "Chroma query error:",
                e
            )

            continue

        # --------------------------------------------------
        # EMPTY RESULTS
        # --------------------------------------------------

        if (
            not results
            or
            not results.get("documents")
        ):
            continue

        # --------------------------------------------------
        # STORE RESULTS
        # --------------------------------------------------

        for i in range(

            len(results["documents"][0])
        ):

            distance = results[
                "distances"
            ][0][i]

            metadata = results[
                "metadatas"
            ][0][i] or {}

            all_results.append({

                "text":
                    results["documents"][0][i],

                "source":
                    metadata.get(
                        "source",
                        "unknown"
                    ),

                "page":
                    metadata.get(
                        "page",
                        "N/A"
                    ),

                "distance":
                    distance
            })

    end_timer("retrieval_loop")

    # ==================================================
    # UNIQUE RESULTS
    # ==================================================

    start_timer("deduplication")

    unique_results = list({

        r["text"]: r

        for r in all_results

    }.values())

    end_timer("deduplication")

    if not unique_results:

        debug_print("No results found")

        end_timer("retriever_total")

        return [], 9999.0

    # ==================================================
    # AVG DISTANCE
    # ==================================================

    start_timer("distance_analysis")

    avg_distance = sum(

        r["distance"]

        for r in unique_results

    ) / len(unique_results)

    end_timer("distance_analysis")

    debug_print(
        "Avg distance (pre-filter):",
        avg_distance
    )

    # ==================================================
    # ADAPTIVE FILTER
    # ==================================================

    start_timer("adaptive_filter")

    filtered_results = [

        r for r in unique_results

        if r["distance"] <= avg_distance * 3
    ]

    end_timer("adaptive_filter")

    debug_print(
        f"After adaptive filter: "
        f"{len(filtered_results)} docs"
    )

    # --------------------------------------------------
    # FILTER FALLBACK
    # --------------------------------------------------

    if not filtered_results:

        debug_print(
            "Filter too strict "
            "→ fallback to all results"
        )

        filtered_results = unique_results

    # ==================================================
    # SORT + TOP_K
    # ==================================================

    start_timer("result_sorting")

    sorted_results = sorted(

        filtered_results,

        key=lambda x: x["distance"]
    )

    top_results = sorted_results[:TOP_K]

    end_timer("result_sorting")

    debug_print(
        f"Final retrieved: "
        f"{len(top_results)} documents"
    )

    avg_distance_final = sum(

        r["distance"]

        for r in top_results

    ) / len(top_results)

    debug_print(
        "Avg distance (final):",
        avg_distance_final
    )

    # ==================================================
    # OBSERVABILITY
    # ==================================================

    log_data(
        "retrieved_documents",
        len(top_results)
    )

    log_data(
        "unique_documents",
        len(unique_results)
    )

    log_data(
        "avg_distance",
        round(
            avg_distance_final,
            4
        )
    )

    end_timer("retriever_total")

    return (
        top_results,
        avg_distance_final
    )