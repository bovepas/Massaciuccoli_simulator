import re


def parse_top_k(question: str) -> int:

    q = question.lower()

    match = re.search(r"top\s+(\d+)", q)
    if match:
        return int(match.group(1))

    # default
    return 5