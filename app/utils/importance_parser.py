import re


def parse_top_k(question: str) -> int:

    q = question.lower()

    # ----------------------------------------------
    # explicit "top N"
    # ----------------------------------------------

    match = re.search(r"top\s+(\d+)", q)

    if match:
        return int(match.group(1))

    # ----------------------------------------------
    # generic numeric ranking
    # e.g. "What are the 3 variables..."
    # ----------------------------------------------

    match = re.search(
        r"""
        \b(\d+)\s+
        (
            environmental\s+
        )?
        (
            variables|
            factors|
            drivers|
            indicators|
            pressures|
            features
        )
        """,
        q,
        flags=re.VERBOSE
    )

    if match:
        return int(match.group(1))

    # ----------------------------------------------
    # default
    # ----------------------------------------------

    return 5