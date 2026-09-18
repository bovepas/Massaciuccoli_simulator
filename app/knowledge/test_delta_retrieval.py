from retriever import expand_query, get_embedding, collection

import sys

query = sys.argv[1] if len(sys.argv) > 1 else "Presence of grassland"

queries = expand_query(query)

print("\n" + "=" * 80)
print("QUERY ORIGINALE:", query)
print("=" * 80)

for i, q in enumerate(queries, 1):

    print(f"\n{'-' * 80}")
    print(f"ESPANSIONE {i}")
    print(q)
    print("-" * 80)

    embedding = get_embedding(q)

    results = collection.query(
        query_embeddings=[embedding],
        n_results=6
    )

    documents = results["documents"][0]
    distances = results["distances"][0]
    metadatas = results["metadatas"][0]

    for rank, (doc, distance, metadata) in enumerate(
        zip(documents, distances, metadatas), 1
    ):
        source = metadata.get("source", "?")

        markers = [
            "grassland",
            "habitat degradation",
            "biodiversity",
            "ecological connectivity",
            "fragmentation"
        ]

        found = [m for m in markers if m in doc.lower()]

        print(
            f"\n#{rank}  distance={distance:.2f}  source={source}"
        )
        print(
            f"    keywords: {', '.join(found) if found else '-'}"
        )
        print(
            "    " + doc[:300].replace("\n", " ")
        )