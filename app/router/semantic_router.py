# app/router/semantic_router.py

from router.similarity import score_question


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

ROUTER_THRESHOLD = 0.60


# ---------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------

def route_question(question: str) -> dict[str, str]:
    """
    Route a question using semantic similarity.

    The question is compared against all examples of all tasks.
    The task with the highest similarity score wins.

    If the best score is below ROUTER_THRESHOLD, the question
    is routed to chat.
    """

    scores = score_question(question)

    if not scores:
        return {"type": "chat"}

    # Find task with highest score
    best_task = max(scores, key=scores.get)
    best_score = scores[best_task]

    # Global safety threshold
    if best_score < ROUTER_THRESHOLD:
        best_task = "chat"

    return {
        "type": best_task,
        "scores": scores
    }