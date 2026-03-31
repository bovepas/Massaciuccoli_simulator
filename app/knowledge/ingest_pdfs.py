# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Base Ingestion Script - Versione Migliorata
"""

import os
import re
import requests
import chromadb
from pypdf import PdfReader
from uuid import uuid4


# ======================================================
# Config
# ======================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

PDF_FOLDER = os.path.join(BASE_DIR, "knowledge", "pdfs")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 300
MIN_CHUNK_LENGTH = 400


# ======================================================
# Text cleaning
# ======================================================

def clean_text(text):

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = text.strip()

    return text


# ======================================================
# Text chunking
# ======================================================

def chunk_text(text, chunk_size=1200, overlap=300):

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:

        end = start + chunk_size
        chunk = text[start:end]

        if len(chunk) >= MIN_CHUNK_LENGTH:
            chunks.append(chunk)

        start = end - overlap

    return chunks


# ======================================================
# Embedding via Ollama
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
# Main ingestion
# ======================================================

def ingest_pdfs():

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # ricreiamo la collection pulita
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

        chunks = chunk_text(full_text, CHUNK_SIZE, CHUNK_OVERLAP)

        print(f"   → Chunk generati: {len(chunks)}")

        for chunk in chunks:

            embedding = get_embedding(chunk)

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
# Run
# ======================================================

if __name__ == "__main__":
    ingest_pdfs()
