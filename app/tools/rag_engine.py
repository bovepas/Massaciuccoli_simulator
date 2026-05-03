"""
RAG Engine — STEP 1 (Retrieval only)
"""

import os
import glob


# ======================================================
# CONFIG
# ======================================================

DOCS_PATH = "rag_docs"  # cartella con file .txt


# ======================================================
# LOAD DOCUMENTS
# ======================================================

def load_documents():

    docs = []

    if not os.path.exists(DOCS_PATH):
        return docs

    files = glob.glob(os.path.join(DOCS_PATH, "*.txt"))

    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as file:
                text = file.read()
                docs.append({
                    "name": os.path.basename(f),
                    "content": text.lower()
                })
        except:
            continue

    return docs


# ======================================================
# SIMPLE KEYWORD MATCH
# ======================================================

def score_document(doc, keywords):

    score = 0

    for kw in keywords:
        if kw.lower() in doc["content"]:
            score += 1

    return score


# ======================================================
# RETRIEVE
# ======================================================

def retrieve_relevant_docs(keywords, top_k=3):

    docs = load_documents()

    if not docs:
        return []

    scored = []

    for doc in docs:
        score = score_document(doc, keywords)
        if score > 0:
            scored.append((doc, score))

    scored = sorted(scored, key=lambda x: x[1], reverse=True)

    return [d[0] for d in scored[:top_k]]


# ======================================================
# EXTRACT SNIPPETS
# ======================================================

def extract_relevant_snippets(docs, keywords, max_chars=300):

    snippets = []

    for doc in docs:

        text = doc["content"]

        for kw in keywords:
            idx = text.find(kw.lower())

            if idx != -1:
                start = max(0, idx - 100)
                end = min(len(text), idx + 200)

                snippet = text[start:end]

                snippets.append({
                    "source": doc["name"],
                    "text": snippet.strip()
                })

                break  # uno snippet per doc

    return snippets


# ======================================================
# MAIN RAG FUNCTION
# ======================================================

def run_rag(keywords):

    docs = retrieve_relevant_docs(keywords)

    snippets = extract_relevant_snippets(docs, keywords)

    return snippets