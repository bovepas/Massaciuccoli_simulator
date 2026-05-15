# -*- coding: utf-8 -*-

"""
Dependency Parser — v5 (semantic + directional fix)

# Adds robust handling for:
- "how does X affect Y"
- "how does X influence Y"
- More stable source/target detection
"""

import re
from utils.feature_mapping import FEATURE_MAPPING, SYNONYMS, normalize_feature_name


# ======================================================
# TEXT NORMALIZATION
# ======================================================

def normalize_text(text: str):
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return text


# ======================================================
# FEATURE DETECTION
# ======================================================

def find_features_in_text(text: str):

    text = normalize_text(text)

    found = []

    # direct mapping
    for key in FEATURE_MAPPING.keys():
        if key in text:
            canonical = normalize_feature_name(key)
            if canonical:
                found.append(canonical)

    # synonyms
    for syn, base in SYNONYMS.items():
        if syn in text:
            canonical = normalize_feature_name(base)
            if canonical:
                found.append(canonical)

    return list(dict.fromkeys(found))


# ======================================================
# ABSTRACT TARGET DETECTION
# ======================================================

def detect_abstract_target(text: str):

    text = text.lower()

    if "risk" in text:
        return "risk_score"

    if "stability" in text:
        return "risk_score"

    if "ecosystem" in text:
        return "risk_score"

    return None


# ======================================================
# DELTA
# ======================================================

def extract_delta(text: str):

    match = re.search(r"([-+]?\d+\.?\d*)", text)
    if match:
        return float(match.group(1))
    return None


def detect_directional_delta(text: str, delta):

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

    q = normalize_text(question)

    features = find_features_in_text(q)
    target = detect_abstract_target(q)

    print("Detected features:", features)
    print("Detected abstract target:", target)

    # ======================================================
    # CASE 1: conceptual (1 feature + abstract target)
    # ======================================================

    if len(features) == 1 and target is not None:

        return {
            "source": features[0],
            "target": target,
            "delta": None,
            "unknown": []
        }

    # ======================================================
    # CASE 2: not enough info
    # ======================================================

    if len(features) < 2:
        return {
            "source": None,
            "target": None,
            "delta": None,
            "unknown": []
        }

    # ======================================================
    # 🔥 NEW: how does X affect Y
    # ======================================================

    if "how does" in q and ("affect" in q or "influence" in q):

        parts = re.split(r"affect|influence", q)

        if len(parts) == 2:
            left = parts[0]
            right = parts[1]

            source_candidates = find_features_in_text(left)
            target_candidates = find_features_in_text(right)

            source = source_candidates[-1] if source_candidates else features[0]
            target = target_candidates[0] if target_candidates else features[1]

            return {
                "source": source,
                "target": target,
                "delta": None,
                "unknown": []
            }

    # ======================================================
    # PATTERN 1: effect of X on Y
    # ======================================================

    if "effect of" in q or "impact of" in q:

        parts = q.split(" on ")

        if len(parts) == 2:
            left = parts[0]
            right = parts[1]

            source_candidates = find_features_in_text(left)
            target_candidates = find_features_in_text(right)

            source = source_candidates[0] if source_candidates else features[0]
            target = target_candidates[0] if target_candidates else features[1]

        else:
            source = features[0]
            target = features[1]

    # ======================================================
    # PATTERN 2: how does Y change if X ...
    # ======================================================

    elif "if" in q:

        parts = q.split("if")

        if len(parts) == 2:
            left = parts[0]
            right = parts[1]

            target_candidates = find_features_in_text(left)
            source_candidates = find_features_in_text(right)

            target = target_candidates[0] if target_candidates else features[0]
            source = source_candidates[0] if source_candidates else features[1]

        else:
            source = features[0]
            target = features[1]

    # ======================================================
    # DEFAULT
    # ======================================================

    else:
        source = features[0]
        target = features[1]

    # ======================================================
    # DELTA
    # ======================================================

    delta = extract_delta(q)
    delta = detect_directional_delta(q, delta)

    return {
        "source": source,
        "target": target,
        "delta": delta,
        "unknown": []
    }