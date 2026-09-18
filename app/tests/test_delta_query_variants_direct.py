"""Test Delta RAG query variants with and without automatic query expansion.

This test does NOT modify project RAG code.

It compares:
1. NORMAL retrieval: the real retrieve_documents() pipeline, including query expansion.
2. DIRECT retrieval: the same embedding model + Chroma collection, but using ONLY
   the original query, bypassing expand_query(), pooling, adaptive filtering and
   the final reranking.

Purpose:
Determine whether retrieval problems come from query formulation or from the
automatic query-expansion/pooling stage.
"""

from knowledge.retriever import (
    retrieve_documents,
    get_embedding,
    collection,
    TOP_K,
    ensure_kb_ready,
)


TESTS = {
    "temperature": {"concept": "temperature", "directions": ["increase", "decrease"]},
    "precipitation": {"concept": "precipitation", "directions": ["increase", "decrease"]},
    "biodiversity": {"concept": "biodiversity", "directions": ["increase", "decrease"]},
    "evapotranspiration": {"concept": "evapotranspiration", "directions": ["increase", "decrease"]},
}


def print_results(variable, label, query, results):
    print("\n" + "=" * 100)
    print(f"{variable.upper()} — {label}")
    print(f"QUERY: {query}")
    print("=" * 100)

    if not results:
        print("\nNO RESULTS")
        return

    for i, item in enumerate(results[:6], start=1):
        if isinstance(item, dict):
            text = item.get("text", "")
            distance = item.get("distance")
            metadata = item.get("metadata", {})
            source = item.get("source", metadata.get("source", "unknown"))
            page = item.get("page", metadata.get("page", "N/A"))
        else:
            text = str(item)
            distance = None
            source = "unknown"
            page = "N/A"

        print(f"\n--- RESULT {i} ---")
        print(f"distance: {distance}")
        print(f"source: {source}")
        print(f"page: {page}")
        print(text[:1200])


def direct_retrieve(query):
    """Retrieve ONLY the original query from Chroma.

    Deliberately bypasses:
    - expand_query()
    - multi-query pooling
    - deduplication
    - adaptive filtering
    - rerank_results()

    Embedding generation and Chroma collection are the same ones used by the
    real retriever.
    """
    ensure_kb_ready()

    embedding = get_embedding(query)
    if embedding is None:
        return []

    results = collection.query(
        query_embeddings=[embedding],
        n_results=TOP_K,
    )

    if not results or not results.get("documents"):
        return []

    direct_results = []
    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results.get("metadatas", [[]])[0]

    for i, text in enumerate(documents):
        metadata = metadatas[i] or {}
        direct_results.append({
            "text": text,
            "source": metadata.get("source", "unknown"),
            "page": metadata.get("page", "N/A"),
            "distance": distances[i],
        })

    return direct_results


def run_test(variable, label, query):
    try:
        results, _ = retrieve_documents(query)
        print_results(variable, f"{label} — NORMAL RETRIEVER", query, results)
    except Exception as exc:
        print("\n" + "!" * 100)
        print(f"ERROR — {variable.upper()} — {label} — NORMAL RETRIEVER")
        print(f"QUERY: {query}")
        print(f"{type(exc).__name__}: {exc}")
        print("!" * 100)

    try:
        results = direct_retrieve(query)
        print_results(variable, f"{label} — DIRECT CHROMA", query, results)
    except Exception as exc:
        print("\n" + "!" * 100)
        print(f"ERROR — {variable.upper()} — {label} — DIRECT CHROMA")
        print(f"QUERY: {query}")
        print(f"{type(exc).__name__}: {exc}")
        print("!" * 100)


def main():
    print("=" * 100)
    print("DELTA RAG QUERY EXPERIMENT — NORMAL vs DIRECT")
    print("=" * 100)
    print("\nNo project files are modified.")
    print("\nNORMAL:")
    print("  query → automatic expansion → Chroma → pool/dedup/filter/rerank → top 6")
    print("\nDIRECT:")
    print("  query → embedding → Chroma → top 6")
    print("\nThe DIRECT path uses the same embedding model and Chroma collection,")
    print("but bypasses automatic query expansion and all downstream pooling/filtering.")
    print("=" * 100)

    for variable, config in TESTS.items():
        concept = config["concept"]
        run_test(variable, "BASELINE", f"{concept} ecosystem risk")
        for direction in config["directions"]:
            run_test(variable, f"DIRECTION: {direction.upper()}", f"{concept} {direction} ecosystem risk")
        run_test(variable, "CHANGE", f"{concept} change ecosystem risk")

    print("\n" + "=" * 100)
    print("END OF DELTA RAG QUERY EXPERIMENT")
    print("=" * 100)


if __name__ == "__main__":
    main()
