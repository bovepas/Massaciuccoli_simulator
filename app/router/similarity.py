# app/router/similarity.py

import numpy as np

from router.embedding import get_embedding
from router.examples import load_all_examples


def cosine_similarity(vector_a, vector_b) -> float:
    """
    Calculate cosine similarity between two vectors.
    """

    a = np.asarray(vector_a, dtype=np.float32)
    b = np.asarray(vector_b, dtype=np.float32)

    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(np.dot(a, b) / (norm_a * norm_b))


def score_task(question_embedding, examples: list[str]) -> float:
    """
    Return the highest cosine similarity between the question
    embedding and all examples belonging to a task.
    """

    best_score = 0.0

    for example in examples:
        example_embedding = get_embedding(example)

        score = cosine_similarity(
            question_embedding,
            example_embedding
        )

        if score > best_score:
            best_score = score

    return best_score


def score_question(question: str) -> dict[str, float]:
    """
    Calculate the best similarity score for every task.

    The question is embedded only once.
    For each task, the maximum similarity among all its
    examples is returned.
    """

    question_embedding = get_embedding(question)

    all_examples = load_all_examples()

    scores = {}

    for task, examples in all_examples.items():
        if not examples:
            scores[task] = 0.0
            continue

        scores[task] = score_task(
            question_embedding,
            examples
        )

    return scores