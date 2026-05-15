# -*- coding: utf-8 -*-

"""
Dependency Parser — v6 (semantic + directional + abstract target fix)

✔ Keeps all existing logic
✔ Adds support for non-feature targets (e.g. water availability)
✔ No regression risk
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
# 🆕 ABSTRACT TARGET DETECTION (IMPROVED)
# ======================================================

def detect_abstract_target(text: str):

    text = text.lower()

    if "risk" in text:
        return "risk_score"

    if "stability" in text:
        return "risk_score"

    if "ecosystem" in text:
        return "risk_score"

    # 🔥 NEW
    if "water availability" in text:
        return "hydrological dynamics"

    if "water" in text:
        return "hydrological dynamics"

    if "nutrient" in text:
        return "nutrient loading"

    return None


# ======================================================
# 🆕 RAW TARGET EXTRACTION (NEW CORE FIX)
# ======================================================

def extract_raw_target(text: str):

    # pattern: "on something"
    match = re.search(r"on (.+)", text)
    if match:
        return match.group(1).strip()

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

        # 🔥 NEW: fallback for "effect of X on Y"
        raw_target = extract_raw_target(q)

        if len(features) == 1 and raw_target:
            return {
                "source": features[0],
                "target": raw_target,
                "delta": None,
                "unknown": []
            }

        return {
            "source": None,
            "target": None,
            "delta": None,
            "unknown": []
        }

    # ======================================================
    # HOW DOES X AFFECT Y
    # ======================================================

    if "how does" in q and ("affect" in q or "influence" in q):

        parts = re.split(r"affect|influence", q)

        if len(parts) == 2:
            left = parts[0]
            right = parts[1]

            source_candidates = find_features_in_text(left)
            target_candidates = find_features_in_text(right)

            source = source_candidates[-1] if source_candidates else features[0]

            if target_candidates:
                target = target_candidates[0]
            else:
                target = extract_raw_target(right) or features[1]

            return {
                "source": source,
                "target": target,
                "delta": None,
                "unknown": []
            }

    # ======================================================
    # EFFECT OF X ON Y
    # ======================================================

    if "effect of" in q or "impact of" in q:

        parts = q.split(" on ")

        if len(parts) == 2:
            left = parts[0]
            right = parts[1]

            source_candidates = find_features_in_text(left)
            target_candidates = find_features_in_text(right)

            source = source_candidates[0] if source_candidates else features[0]

            if target_candidates:
                target = target_candidates[0]
            else:
                target = right.strip()

        else:
            source = features[0]
            target = features[1]

    # ======================================================
    # IF CONDITION
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