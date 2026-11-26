# app/router/embedding.py

import os
import pickle
from pathlib import Path

import requests


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

EMBED_MODEL = "nomic-embed-text"

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434"
)

OLLAMA_EMBED_URL = f"{OLLAMA_BASE_URL}/api/embeddings"


# ---------------------------------------------------------------------
# Persistent cache
# ---------------------------------------------------------------------

CACHE_FILE = Path(__file__).resolve().parent / "embedding_cache.pkl"


def _load_cache() -> dict[str, list[float]]:
    """
    Load the persistent embedding cache.

    If the cache does not exist or cannot be loaded,
    start with an empty cache.
    """

    if not CACHE_FILE.exists():
        return {}

    try:
        with CACHE_FILE.open("rb") as f:
            cache = pickle.load(f)

        if isinstance(cache, dict):
            return cache

    except Exception:
        pass

    return {}


def _save_cache(cache: dict[str, list[float]]) -> None:
    """
    Save the embedding cache to disk.
    """

    temporary_file = CACHE_FILE.with_suffix(".tmp")

    with temporary_file.open("wb") as f:
        pickle.dump(cache, f)

    temporary_file.replace(CACHE_FILE)


# Load once when the module is imported.
_embedding_cache = _load_cache()


# ---------------------------------------------------------------------
# Embedding
# ---------------------------------------------------------------------

def get_embedding(text: str) -> list[float]:
    """
    Return the embedding for the given text.

    If the text is already present in the persistent cache,
    return the cached embedding.

    Otherwise calculate the embedding using Ollama,
    save it to the cache and return it.
    """

    text = text.strip()

    if not text:
        return []

    # -------------------------------------------------------------
    # 1. Check cache
    # -------------------------------------------------------------

    if text in _embedding_cache:
        return _embedding_cache[text]

    # -------------------------------------------------------------
    # 2. Calculate embedding
    # -------------------------------------------------------------

    response = requests.post(
        OLLAMA_EMBED_URL,
        json={
            "model": EMBED_MODEL,
            "prompt": text,
        },
        timeout=300,
    )

    response.raise_for_status()

    data = response.json()

    embedding = data.get("embedding")

    if not embedding:
        raise RuntimeError(
            "Ollama returned no embedding for the requested text."
        )

    # -------------------------------------------------------------
    # 3. Save in persistent cache
    # -------------------------------------------------------------

    embedding = list(embedding)

    _embedding_cache[text] = embedding

    _save_cache(_embedding_cache)

    return embedding