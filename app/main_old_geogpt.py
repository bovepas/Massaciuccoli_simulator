import os
import time
import requests
from typing import List, Tuple

import pandas as pd

from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_community.vectorstores.utils import filter_complex_metadata
from langchain_huggingface import HuggingFaceEmbeddings

from geogpt_client import geogpt_call

# ======================================================
# CONFIG
# ======================================================

APP_ROOT = "/app"
DOCS_FOLDER = os.path.join(APP_ROOT, "docs")
CHROMA_DIR = os.path.join(APP_ROOT, "chroma_db")

TOP_K = 10
SIMILARITY_THRESHOLD = 0.10
DEBUG = True

# Bounding box Lago di Massaciuccoli
MASSACIUCCOLI_BBOX = (10.221, 10.280, 43.825, 43.860)

# ======================================================
# EMBEDDINGS (STABILI, OFFLINE)
# ======================================================

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ======================================================
# LOAD CSV (ROBUSTO)
# ======================================================

def load_csv(path: str, bbox: Tuple[float, float, float, float] | None = None) -> List[Document]:
    df = pd.read_csv(path)

    if df.shape[1] < 3:
        raise RuntimeError(f"CSV {path} non valido (meno di 3 colonne)")

    lon_col = df.columns[0]
    lat_col = df.columns[1]

    # 🔒 forza conversione numerica
    df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
    df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")

    df = df.dropna(subset=[lon_col, lat_col])

    if bbox:
        lon_min, lon_max, lat_min, lat_max = bbox
        df = df[
            (df[lon_col] >= lon_min) & (df[lon_col] <= lon_max) &
            (df[lat_col] >= lat_min) & (df[lat_col] <= lat_max)
        ]

    variables = df.columns[2:]

    stats = []
    for var in variables:
        col = pd.to_numeric(df[var], errors="coerce")
        stats.append(
            f"{var}: min={col.min()}, max={col.max()}, mean={col.mean():.2f}"
        )

    content = (
        f"CSV file: {os.path.basename(path)}\n"
        f"Rows after filter: {len(df)}\n"
        f"Lon range: {df[lon_col].min()} – {df[lon_col].max()}\n"
        f"Lat range: {df[lat_col].min()} – {df[lat_col].max()}\n\n"
        f"Statistics:\n" + "\n".join(stats)
    )

    return [
        Document(
            page_content=content,
            metadata={"source": os.path.basename(path), "type": "csv"}
        )
    ]

# ======================================================
# LOAD DOCUMENTS
# ======================================================

documents: List[Document] = []

for file in os.listdir(DOCS_FOLDER):
    if file.lower().endswith(".csv"):
        documents.extend(
            load_csv(os.path.join(DOCS_FOLDER, file), MASSACIUCCOLI_BBOX)
        )

if not documents:
    raise RuntimeError("❌ Nessun documento caricato")

documents = filter_complex_metadata(documents)

print(f"📄 Documenti caricati: {len(documents)}")

# ======================================================
# VECTOR DB
# ======================================================

vectordb = Chroma.from_documents(
    documents=documents,
    embedding=embeddings,
    persist_directory=CHROMA_DIR
)

# ======================================================
# ASK
# ======================================================

def ask(question: str) -> str:
    results = vectordb.similarity_search_with_score(question, k=TOP_K)

    if not results:
        return "⚠️ Nessun contenuto rilevante trovato."

    blocks = []
    for doc, score in results:
        blocks.append(
            f"[SOURCE: {doc.metadata['source']} | SIM: {1-score:.2f}]\n{doc.page_content}"
        )

    context = "\n\n".join(blocks)

    prompt = f"""
You are an environmental scientist analyzing data from Lake Massaciuccoli (Tuscany, Italy).

Use ONLY the information in the CONTEXT.

CONTEXT:
{context}

QUESTION:
{question}

ANSWER:
"""

    return geogpt_call(prompt)

# ======================================================
# INTERACTIVE LOOP
# ======================================================

print("\n🤖 Mini-assistente ecologico – Lago di Massaciuccoli")
print("Scrivi 'exit' per uscire\n")

while True:
    q = input("Tu: ").strip()
    if q.lower() in ("exit", "quit"):
        break

    print("\nBot:")
    print(ask(q))
    print()
