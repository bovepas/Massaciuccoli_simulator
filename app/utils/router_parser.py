# -*- coding: utf-8 -*-
# router_parser.py

import json
import re


VARIABLES = [
    "temperature",
    "precipitation",
    "biodiversity",
    "tree cover",
    "grassland",
    "evapotranspiration",
    "productivity"
]


def simple_parse(q: str):

    # ======================================================
    # NORMALIZATION
    # ======================================================

    original_q = q
    q = q.lower()

    # ======================================================
    # 🔥 STABILITY → RISK MAPPING (SAFE)
    # ======================================================

    if "stability" in q:
        print("[ROUTER PARSER] 'stability' interpreted as 'risk'")
        q = q.replace("stability", "risk")

    # ======================================================
    # TARGET DETECTION
    # ======================================================

    target = "unknown"
    variables = []

    if "risk" in q or "ecosystem" in q:
        target = "risk"

    for v in VARIABLES:
        if v in q:
            variables.append(v)

    if target == "unknown" and variables:
        target = variables[-1]

    # ======================================================
    # STRUCTURE DETECTION
    # ======================================================

    structure = "generic"

    if "from" in q and "to" in q:
        structure = "delta"

    elif "vs" in q or "versus" in q or "compare" in q:
        structure = "comparison"

    elif "if" in q or "given" in q or "when" in q:
        structure = "scenario"

    elif any(w in q for w in ["affect", "influence", "effect"]):
        structure = "dependency"

    # ======================================================
    # INTENT DETECTION
    # ======================================================

    intent = "generic"

    if any(w in q for w in ["top", "most", "important"]):
        intent = "importance"

    if "drive" in q or "drivers" in q:
        intent = "drivers"

    # ======================================================
    # OUTPUT
    # ======================================================

    return {
        "target": target,
        "variables": variables,
        "structure": structure,
        "intent": intent
    }