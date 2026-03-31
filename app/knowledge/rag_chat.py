# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
RAG con query expansion semantica migliorata
"""

import requests
import chromadb
import os


# ======================================================
# CONFIG
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"

LLM_MODEL = "llama3"
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

    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": EMBED_MODEL,
            "prompt": text
        }
    )

    response.raise_for_status()
    return response.json()["embedding"]


# ======================================================
# SMART QUERY EXPANSION
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

    prompt = f"""
Sei un esperto di ecosistemi lacustri.

Rispondi alla domanda usando SOLO le informazioni presenti nel contesto.
Se l'informazione non è presente nel contesto, dichiaralo chiaramente.

Contesto:
{context}

Domanda:
{query}

Risposta:
"""

    return prompt


# ======================================================
# LLM
# ======================================================

def generate_answer(prompt):

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "temperature": 0.2
        }
    )

    response.raise_for_status()
    return response.json()["response"]


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    query = input("Fai una domanda: ")

    print("\n[1] Recupero documenti...")
    docs = retrieve_documents(query)

    print("Documenti trovati:", len(docs))

    if not docs:
        print("Nessun documento rilevante trovato.")
    else:
        print("\n[2] Generazione risposta...\n")
        prompt = build_prompt(query, docs)
        answer = generate_answer(prompt)

        print("RISPO
