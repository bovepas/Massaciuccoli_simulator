
# Semantic ingestion template v5
# Ingest every .txt file in knowledge/rag_sources.

import os
import re
import sys
from uuid import uuid4

import chromadb
import requests


# ======================================================
# PATHS AND CONFIGURATION
# ======================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Ensure application root is available for imports.
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.logger import log_data


PDF_FOLDER = os.path.join(
    BASE_DIR, "knowledge", "rag_sources"
)

CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

COLLECTION_NAME = "massaciuccoli_knowledge"

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434"
)

OLLAMA_EMBED_URL = (
    f"{OLLAMA_BASE_URL}/api/embeddings"
)

EMBED_MODEL = "nomic-embed-text"

MAX_SECTION_SIZE = 2500


# ======================================================
# SECTION SPLITTING
# ======================================================

def split_sections(text):

    pattern = re.compile(
        r'={10,}\s*\n([A-Z0-9 /()-]+?)\s*\n={10,}',
        re.MULTILINE
    )

    matches = list(pattern.finditer(text))

    if not matches:
        return [{
            "title": "FULL_DOCUMENT",
            "text": text.strip()
        }]

    sections = []

    for i, match in enumerate(matches):

        start = match.end()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        body = text[start:end].strip()

        if body:
            sections.append({
                "title": match.group(1).strip(),
                "text": body
            })

    return sections


# ======================================================
# LARGE SECTION SPLITTING
# ======================================================

def split_large_section(section):

    if len(section["text"]) <= MAX_SECTION_SIZE:
        return [section]

    sentences = re.split(
        r'(?<=[.!?])\s+',
        section["text"]
    )

    chunks = []

    current = ""

    chunk_index = 1

    for sentence in sentences:

        if len(current) + len(sentence) < MAX_SECTION_SIZE:

            current += " " + sentence

        else:

            if current.strip():

                chunks.append({
                    "title": (
                        f'{section["title"]} '
                        f'({chunk_index})'
                    ),
                    "text": current.strip()
                })

                chunk_index += 1

            current = sentence

    if current.strip():

        chunks.append({
            "title": (
                f'{section["title"]} '
                f'({chunk_index})'
            ),
            "text": current.strip()
        })

    return chunks


# ======================================================
# EMBEDDINGS
# ======================================================

def get_embedding(text):

    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": EMBED_MODEL,
            "prompt": text
        },
        timeout=30
    )

    response.raise_for_status()

    return response.json()["embedding"]


# ======================================================
# SOURCE DISCOVERY
# ======================================================

def list_txt_sources():

    if not os.path.isdir(PDF_FOLDER):

        raise FileNotFoundError(
            f"RAG sources directory not found: {PDF_FOLDER}"
        )

    files = sorted(
        [
            filename
            for filename in os.listdir(PDF_FOLDER)
            if filename.lower().endswith(".txt")
            and os.path.isfile(
                os.path.join(PDF_FOLDER, filename)
            )
        ],
        key=str.casefold
    )

    if not files:

        raise RuntimeError(
            f"No TXT files found in: {PDF_FOLDER}"
        )

    return files


# ======================================================
# MAIN INGESTION
# ======================================================

def ingest_pdfs(force=False):

    source_files = list_txt_sources()

    print("\n======================================================")
    print("MASSACIUCCOLI RAG INGESTION")
    print("======================================================")

    print(f"Sources directory: {PDF_FOLDER}")

    print(f"TXT files selected: {len(source_files)}")

    for filename in source_files:
        print(f"  - {filename}")

    if force:

        print(
            "\nWARNING: force=True will delete and rebuild "
            f"the '{COLLECTION_NAME}' Chroma collection."
        )

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    if force:

        try:

            client.delete_collection(
                COLLECTION_NAME
            )

            print(
                f"Deleted existing collection: {COLLECTION_NAME}"
            )

        except Exception:

            print(
                "No existing collection to delete."
            )

    collection = client.get_or_create_collection(
        COLLECTION_NAME
    )

    total_chunks = 0

    per_file_counts = {}

    # --------------------------------------------------
    # PROCESS EVERY TXT FILE
    # --------------------------------------------------

    for filename in source_files:

        filepath = os.path.join(
            PDF_FOLDER,
            filename
        )

        with open(
            filepath,
            "r",
            encoding="utf-8-sig"
        ) as file:

            document_text = file.read().strip()

        if not document_text:

            print(
                f"WARNING: empty TXT skipped: {filename}"
            )

            per_file_counts[filename] = 0

            continue

        chunks = []

        for section in split_sections(document_text):

            chunks.extend(
                split_large_section(section)
            )

        chunks = [
            chunk
            for chunk in chunks
            if chunk["text"].strip()
        ]

        per_file_counts[filename] = len(chunks)

        log_data(
            f"chunks::{filename}",
            len(chunks)
        )

        print(
            f"\nIngesting {filename}: "
            f"{len(chunks)} chunks"
        )

        # --------------------------------------------------
        # EMBED AND STORE CHUNKS
        # --------------------------------------------------

        for chunk in chunks:

            embedding = get_embedding(
                chunk["text"]
            )

            collection.add(
                ids=[str(uuid4())],

                embeddings=[embedding],

                documents=[chunk["text"]],

                metadatas=[{
                    "source": filename,
                    "document": os.path.splitext(
                        filename
                    )[0],
                    "section": chunk["title"]
                }]
            )

            total_chunks += 1

    # --------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------

    print("\n======================================================")
    print("INGESTION COMPLETED")
    print("======================================================")

    print(
        f"TXT files discovered: {len(source_files)}"
    )

    print(
        "TXT files with content: "
        f"{sum(1 for n in per_file_counts.values() if n > 0)}"
    )

    print(
        f"Total chunks added: {total_chunks}"
    )

    print(
        f"Chroma collection count: {collection.count()}"
    )

    print("\nChunks by source:")

    for filename, count in per_file_counts.items():

        print(
            f"  - {filename}: {count}"
        )

    print("======================================================\n")


# ======================================================
# KB CHECK
# ======================================================

def is_kb_empty():

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    collection = client.get_or_create_collection(
        COLLECTION_NAME
    )

    try:

        return collection.count() == 0

    except Exception:

        return True


# ======================================================
# AUTO INIT
# ======================================================

def ensure_kb_ready():

    if is_kb_empty():

        print(
            "\nKnowledge base empty -> "
            "running ingestion...\n"
        )

        ingest_pdfs(force=True)

    else:

        print(
            "\nKnowledge base already populated.\n"
        )


# ======================================================
# RUN
# ======================================================

if __name__ == "__main__":

    ingest_pdfs(force=True)
