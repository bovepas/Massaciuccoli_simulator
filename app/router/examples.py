# app/router/examples.py

from pathlib import Path


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

#EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"
#EXAMPLES_DIR = Path(__file__).resolve().parent / "examples_java"
EXAMPLES_DIR = Path(__file__).resolve().parent / "examples_full"


# ---------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------

TASKS = [
    "assessment",
    "importance",
    "delta",
    "dependency",
    "comparison",
    "data",
    "drivers",
    "enm",
    "importance_compare",
    "chat",
]


# ---------------------------------------------------------------------
# Load examples
# ---------------------------------------------------------------------

def load_examples(task: str) -> list[str]:
    """
    Load all example questions for a task.

    Each non-empty line in the corresponding .txt file
    is treated as one example.
    """

    if task not in TASKS:
        raise ValueError(f"Unknown task: {task}")

    path = EXAMPLES_DIR / f"{task}.txt"

    if not path.exists():
        raise FileNotFoundError(
            f"Examples file not found for task '{task}': {path}"
        )

    examples = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            examples.append(line)

    return examples


# ---------------------------------------------------------------------
# Load all tasks
# ---------------------------------------------------------------------

def load_all_examples() -> dict[str, list[str]]:
    """
    Load examples for all tasks.
    """

    return {
        task: load_examples(task)
        for task in TASKS
    }