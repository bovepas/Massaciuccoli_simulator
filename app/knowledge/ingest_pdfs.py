# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Knowledge Base Ingestion Script — v2

✔ Timing instrumentation
✔ KB initialization observability
✔ Embedding timing
✔ PDF processing timing
✔ Chunking observability
✔ Keeps ingestion logic unchanged
"""

import os
import re
import requests
import chromadb

from pypdf import PdfReader

from uuid import uuid4

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

PDF_FOLDER = os.path.join(
    BASE_DIR,
    "knowledge",
    "pdfs"
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

CHUNK_SIZE = 600

CHUNK_OVERLAP = 150

MIN_CHUNK_LENGTH = 200


# ======================================================
# TEXT CLEANING
# ======================================================

def clean_text(text):

    text = re.sub(
        r'\s+',
        ' ',
        text
    )

    text = re.sub(
        r'http\S+',
        '',
        text
    )

    text = re.sub(
        r'\[\d+\]',
        '',
        text
    )

    text = re.sub(
        r'Figure \d+.*?',
        '',
        text
    )

    text = re.sub(
        r'Table \d+.*?',
        '',
        text
    )

    text = re.sub(
        r'Fig\. \d+.*?',
        '',
        text
    )

    text = re.sub(
        r'\bdoi:.*?\b',
        '',
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


# ======================================================
# CHUNKING
# ======================================================

def chunk_text(text):

    start_timer("chunking")

    sentences = re.split(
        r'(?<=[.!?]) +',
        text
    )

    chunks = []

    current_chunk = ""

    for sentence in sentences:

        if (
            len(current_chunk)
            + len(sentence)
            < CHUNK_SIZE
        ):

            current_chunk += " " + sentence

        else:

            if (
                len(current_chunk)
                >= MIN_CHUNK_LENGTH
            ):

                chunks.append(
                    current_chunk.strip()
                )

            current_chunk = sentence

    if (
        len(current_chunk)
        >= MIN_CHUNK_LENGTH
    ):

        chunks.append(
            current_chunk.strip()
        )

    end_timer("chunking")

    return chunks


# ======================================================
# EMBEDDING
# ======================================================

def get_embedding(text):

    try:

        start_timer("ingest_embedding")

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

        emb = data.get(
            "embedding",
            None
        )

        end_timer("ingest_embedding")

        if not emb:
            return None

        return emb

    except Exception as e:

        end_timer("ingest_embedding")

        print(
            f"⚠️ Embedding error: {e}"
        )

        return None


# ======================================================
# KB CHECK
# ======================================================

def is_kb_empty():

    start_timer("kb_empty_check")

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        COLLECTION_NAME
    )

    try:

        count = collection.count()

        end_timer("kb_empty_check")

        log_data(
            "kb_chunk_count",
            count
        )

        return count == 0

    except:

        end_timer("kb_empty_check")

        return True


# ======================================================
# INGEST
# ======================================================

def ingest_pdfs(force=False):

    start_timer("pdf_ingestion_total")

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    # --------------------------------------------------
    # RESET COLLECTION
    # --------------------------------------------------

    if force:

        try:

            client.delete_collection(
                COLLECTION_NAME
            )

        except:
            pass

    collection = client.get_or_create_collection(
        COLLECTION_NAME
    )

    total_chunks = 0

    # ==================================================
    # PDF LOOP
    # ==================================================

    for filename in os.listdir(PDF_FOLDER):

        if not filename.lower().endswith(
            ".pdf"
        ):
            continue

        start_timer(f"pdf::{filename}")

        print(
            f"\n📄 Processing "
            f"{filename}..."
        )

        filepath = os.path.join(
            PDF_FOLDER,
            filename
        )

        # --------------------------------------------------
        # PDF READ
        # --------------------------------------------------

        start_timer("pdf_read")

        reader = PdfReader(filepath)

        full_text = ""

        for page in reader.pages:

            text = page.extract_text()

            if text:
                full_text += text + " "

        end_timer("pdf_read")

        # --------------------------------------------------
        # CLEANING
        # --------------------------------------------------

        start_timer("text_cleaning")

        full_text = clean_text(
            full_text
        )

        end_timer("text_cleaning")

        # --------------------------------------------------
        # CHUNKING
        # --------------------------------------------------

        chunks = chunk_text(
            full_text
        )

        log_data(
            f"chunks::{filename}",
            len(chunks)
        )

        print(
            f"   → Chunk generati: "
            f"{len(chunks)}"
        )

        # --------------------------------------------------
        # EMBEDDING + INSERTION
        # --------------------------------------------------

        start_timer("chunk_insertion")

        for chunk in chunks:

            embedding = get_embedding(
                chunk
            )

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

        end_timer("chunk_insertion")

        end_timer(f"pdf::{filename}")

    # ==================================================
    # FINAL
    # ==================================================

    print("\n✅ Ingestion completata.")

    print(
        "Totale chunk nel DB:",
        total_chunks
    )

    log_data(
        "total_chunks",
        total_chunks
    )

    end_timer("pdf_ingestion_total")


# ======================================================
# AUTO INIT
# ======================================================

def ensure_kb_ready():

    start_timer("ensure_kb_ready")

    if is_kb_empty():

        print(
            "\n📚 Knowledge base empty "
            "→ running ingestion...\n"
        )

        ingest_pdfs(force=True)

    else:

        print(
            "\n✅ Knowledge base "
            "already populated.\n"
        )

    end_timer("ensure_kb_ready")


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":

    ingest_pdfs(force=True)