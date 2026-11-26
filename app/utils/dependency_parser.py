# -*- coding: utf-8 -*-

"""
Dependency Parser — v7 (FIXED abstract targets + dual target system)

✔ Keeps all existing logic
✔ 🔥 NEW: dual target (raw + normalized)
✔ Fix water availability
✔ No regression
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

    for key in FEATURE_MAPPING.keys():
        if key in text:
            canonical = normalize_feature_name(key)
            if canonical:
                found.append(canonical)

    for syn, base in SYNONYMS.items():
        if syn in text:
            canonical = normalize_feature_name(base)
            if canonical:
                found.append(canonical)

    return list(dict.fromkeys(found))


# ======================================================
# 🔥 ABSTRACT TARGET NORMALIZATION
# ======================================================

def normalize_abstract_target(raw_target: str):

    if not raw_target:
        return None

    t = raw_target.lower()

    if "water availability" in t:
        return "hydrological dynamics"

    if "water" in t:
        return "hydrological dynamics"

    if "risk" in t or "ecosystem" in t:
        return "risk_score"

    if "productivity" in t:
        return "ecosystem productivity"

    if "biodiversity" in t:
        return "biodiversity"

    return raw_target  # fallback → keep raw


# ======================================================
# RAW TARGET EXTRACTION
# ======================================================

def extract_raw_target(text: str):

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

    print("Detected features:", features)

    # ======================================================
    # RAW TARGET
    # ======================================================

    raw_target = extract_raw_target(q)
    target = normalize_abstract_target(raw_target)

    print("Raw target:", raw_target)
    print("Normalized target:", target)

    # ======================================================
    # CASE 1: 1 feature + abstract target
    # ======================================================

    if len(features) == 1 and target:

        return {
            "source": features[0],
            "target": target,
            "target_raw": raw_target,
            "delta": None,
            "unknown": []
        }

    # ======================================================
    # CASE 2: not enough info
    # ======================================================

    if len(features) < 2:

        if len(features) == 1 and raw_target:
            return {
                "source": features[0],
                "target": target,
                "target_raw": raw_target,
                "delta": None,
                "unknown": []
            }

        return {
            "source": None,
            "target": None,
            "target_raw": None,
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
                raw_target = target
            else:
                raw_target = extract_raw_target(right)
                target = normalize_abstract_target(raw_target)

            return {
                "source": source,
                "target": target,
                "target_raw": raw_target,
                "delta": None,
                "unknown": []
            }

    # ======================================================
    # DEFAULT
    # ======================================================

    source = features[0]
    target = features[1] if len(features) > 1 else None

    delta = extract_delta(q)
    delta = detect_directional_delta(q, delta)

    return {
        "source": source,
        "target": target,
        "target_raw": target,
        "delta": delta,
        "unknown": []
    }