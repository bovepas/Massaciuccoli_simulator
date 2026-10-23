# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Engine Retriever — v5

✔ Retrieval timing instrumentation
✔ Embedding timing
✔ Chroma timing
✔ Query expansion observability
✔ Retrieval observability
✔ Best-distance deduplication and section metadata
"""

import requests
import re
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
    """Keep the original query and add concise, topic-focused variants.

    Avoid generic prefixes appended to the full query: those variants are
    near-duplicates and waste embedding/retrieval calls. For Drivers queries,
    preserve the target and driver names while removing boilerplate.
    """
    original = str(query).strip()
    if not original:
        return []

    expansions = [original]
    target_match = re.search(
        r"\btarget\s*=\s*(.*?)(?=;\s*drivers\s*=|$)",
        original, re.I | re.S
    )
    drivers_match = re.search(
        r"\bdrivers\s*=\s*(.*?)(?=\.\s*(?:Relevant context|Do not assume)|$)",
        original, re.I | re.S
    )
    target = target_match.group(1).strip(" ;.\n\t") if target_match else ""
    drivers = drivers_match.group(1).strip(" ;.\n\t") if drivers_match else ""

    if target or drivers:
        fields = []
        if target:
            fields.append(f"target: {target}")
        if drivers:
            fields.append(f"environmental variables: {drivers}")
        variables = "; ".join(fields)
        expansions.append(
            f"Massaciuccoli wetland scientific ecological context — {variables}"
        )

        terms = f"{target} {drivers}".lower()
        if any(t in terms for t in ("productivity", "phenology", "tree cover", "grassland", "vegetation")):
            expansions.append(f"Wetland vegetation ecology and ecological meaning of {variables}")
        if any(t in terms for t in ("temperature", "precipitation", "evapotranspiration", "climate")):
            expansions.append(f"Wetland climate and hydrological context of {variables}")
        if any(t in terms for t in ("species", "biodiversity", "habitat")):
            expansions.append(f"Wetland biodiversity and habitat context of {variables}")
        if any(t in terms for t in ("land use", "imperviousness", "urban", "land cover")):
            expansions.append(f"Wetland land-use and land-cover context of {variables}")

    # Remove exact/normalised duplicates while preserving order.
    unique = []
    seen = set()
    for item in expansions:
        key = re.sub(r"\s+", " ", item).strip().casefold()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


# LIGHT LEXICAL RE-RANKING
# ======================================================

def rerank_results(query: str, results: List[Dict]) -> List[Dict]:

    q = query.lower()

    keyword_groups = {
        "method": [
            "method","methodology","approach","framework",
            "workflow","pipeline","algorithm","analysis",
            "variational autoencoder","multi k-means"
        ],
        "result": [
            "result","finding","conclusion","performance","accuracy"
        ]
    }

    active_terms = []

    for terms in keyword_groups.values():
        for term in terms:
            if term in q:
                active_terms.append(term)

    if not active_terms:
        return results

    reranked = []

    for r in results:

        score = r["distance"]

        text = r["text"].lower()

        for term in active_terms:
            if term in text:
                score -= 20

        rr = dict(r)
        rr["ranking_score"] = score

        reranked.append(rr)

    reranked.sort(
        key=lambda x: x["ranking_score"]
    )

    return reranked


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

                "section":
                    metadata.get(
                        "section",
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

    # Keep the occurrence with the smallest Chroma distance for each chunk.
    best_by_text = {}
    for result in all_results:
        key = result["text"]
        previous = best_by_text.get(key)
        if previous is None or result["distance"] < previous["distance"]:
            best_by_text[key] = result
    unique_results = list(best_by_text.values())

    end_timer("deduplication")

    if not unique_results:

        debug_print("No results found")

        end_timer("retriever_total")

        return [], 9999.0

    # ==================================================
    # CANDIDATES
    # Rank all unique candidates. The previous avg_distance * 3 threshold
    # had no validated relevance interpretation, so it is intentionally removed.
    candidate_results = unique_results
    debug_print(f"Unique candidate chunks: {len(candidate_results)}")

    # ==================================================
    # SORT + TOP_K
    # ==================================================

    start_timer("result_sorting")

    sorted_results = rerank_results(

        query,

        candidate_results
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