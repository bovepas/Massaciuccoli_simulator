"""
Dependency Parser — v2 (robust, rule-based)

✔ Detects source → target
✔ Supports:
   - "how does X affect Y"
   - "how does Y change if X increases by N"
   - "effect of X on Y"
✔ Extracts delta if present
✔ Uses FEATURE_MAPPING (single source of truth)
"""

import re
from utils.feature_mapping import FEATURE_MAPPING, normalize_feature_name


# ======================================================
# HELPERS
# ======================================================

def find_features_in_text(text: str):
    """
    Detect all features mentioned in text (canonical names)
    """
    found = []

    q = text.lower()

    for key in FEATURE_MAPPING.keys():
        if key in q:
            canonical = normalize_feature_name(key)
            if canonical:
                found.append(canonical)

    return list(dict.fromkeys(found))


def extract_delta(text: str):
    """
    Extract numeric delta (e.g. +2°C, -10%, increase by 5)
    """
    match = re.search(r"([-+]?\d+\.?\d*)", text)
    if match:
        return float(match.group(1))
    return None


def detect_directional_delta(text: str, delta):
    """
    Apply sign based on words like increase/decrease
    """
    if delta is None:
        return None

    q = text.lower()

    if "decrease" in q or "reduce" in q:
        return -abs(delta)

    if "increase" in q or "rise" in q:
        return abs(delta)

    return delta


# ======================================================
# MAIN PARSER
# ======================================================

def parse_dependency(question: str):

    print("[DEPENDENCY PARSER DEBUG]")

    q = question.lower()

    features = find_features_in_text(q)

    print("Detected:", features)

    if len(features) < 2:
        return {
            "source": None,
            "target": None,
            "delta": None
        }

    # --------------------------------------------------
    # PATTERN 1:
    # "how does X affect Y"
    # --------------------------------------------------
    if "affect" in q or "impact" in q or "influence" in q:

        source = features[0]
        target = features[1]

    # --------------------------------------------------
    # PATTERN 2:
    # "how does Y change if X increases"
    # --------------------------------------------------
    elif "if" in q and "change" in q:

        # heuristic:
        # after "if" → source
        # before → target

        parts = q.split("if")

        before = parts[0]
        after = parts[1]

        source_candidates = find_features_in_text(after)
        target_candidates = find_features_in_text(before)

        source = source_candidates[0] if source_candidates else features[0]
        target = target_candidates[0] if target_candidates else features[1]

    # --------------------------------------------------
    # DEFAULT
    # --------------------------------------------------
    else:
        source = features[0]
        target = features[1]

    # --------------------------------------------------
    # DELTA
    # --------------------------------------------------

    delta = extract_delta(q)
    delta = detect_directional_delta(q, delta)

    print("Source:", source)
    print("Target:", target)
    print("Delta:", delta)

    return {
        "source": source,
        "target": target,
        "delta": delta
    }