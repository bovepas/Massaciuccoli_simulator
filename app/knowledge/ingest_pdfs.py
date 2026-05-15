# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Base Ingestion Script - AUTO-INIT READY
"""

import os
import re
import requests
import chromadb
from pypdf import PdfReader
from uuid import uuid4


# ======================================================
# CONFIG
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

PDF_FOLDER = os.path.join(BASE_DIR, "knowledge", "pdfs")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"

EMBED_MODEL = "nomic-embed-text"

CHUNK_SIZE = 600
CHUNK_OVERLAP = 150
MIN_CHUNK_LENGTH = 200


# ======================================================
# TEXT CLEANING
# ======================================================

def clean_text(text):

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\[\d+\]', '', text)

    text = re.sub(r'Figure \d+.*?', '', text)
    text = re.sub(r'Table \d+.*?', '', text)
    text = re.sub(r'Fig\. \d+.*?', '', text)

    text = re.sub(r'\bdoi:.*?\b', '', text, flags=re.IGNORECASE)

    return text.strip()


# ======================================================
# CHUNKING
# ======================================================

def chunk_text(text):

    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:

        if len(current_chunk) + len(sentence) < CHUNK_SIZE:
            current_chunk += " " + sentence
        else:
            if len(current_chunk) >= MIN_CHUNK_LENGTH:
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if len(current_chunk) >= MIN_CHUNK_LENGTH:
        chunks.append(current_chunk.strip())

    return chunks


# ======================================================
# EMBEDDING (SAFE)
# ======================================================

def get_embedding(text):

    try:
        response = requests.post(
            OLLAMA_EMBED_URL,
            json={
                "model": EMBED_MODEL,
                "prompt": text
            },
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        emb = data.get("embedding", None)

        if not emb:
            return None

        return emb

    except Exception as e:
        print(f"⚠️ Embedding error: {e}")
        return None


# ======================================================
# 🔥 KB CHECK
# ======================================================

def is_kb_empty():

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)

    try:
        count = collection.count()
        return count == 0
    except:
        return True


# ======================================================
# INGEST
# ======================================================

def ingest_pdfs(force=False):

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # 🔥 cancella solo se richiesto
    if force:
        try:
            client.delete_collection(COLLECTION_NAME)
        except:
            pass

    collection = client.get_or_create_collection(COLLECTION_NAME)

    total_chunks = 0

    for filename in os.listdir(PDF_FOLDER):

        if not filename.lower().endswith(".pdf"):
            continue

        print(f"\n📄 Processing {filename}...")

        filepath = os.path.join(PDF_FOLDER, filename)
        reader = PdfReader(filepath)

        full_text = ""

        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + " "

        full_text = clean_text(full_text)
        chunks = chunk_text(full_text)

        print(f"   → Chunk generati: {len(chunks)}")

        for chunk in chunks:

            embedding = get_embedding(chunk)

            if embedding is None:
                continue

            collection.add(
                ids=[str(uuid4())],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{
                    "source": filename
                }]
            )

            total_chunks += 1

    print("\n✅ Ingestion completata.")
    print("Totale chunk nel DB:", total_chunks)


# ======================================================
# 🔥 AUTO INIT
# ======================================================

def ensure_kb_ready():

    if is_kb_empty():
        print("\n📚 Knowledge base empty → running ingestion...\n")
        ingest_pdfs(force=True)
    else:
        print("\n✅ Knowledge base already populated.\n")


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":
    ingest_pdfs(force=True)