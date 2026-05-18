# -*- coding: utf-8 -*-

"""
Scenario Parser — v7 (comparison + delta unified + ONE/AND support)

Supporta:
- comparison (vs / versus / first-second / one-and-one)
- delta (from X to Y)
- implicit numeric comparisons
"""

import re


# ======================================================
# HELPERS
# ======================================================

def extract_numbers(text):
    return [float(x) for x in re.findall(r"[+-]?\d+(?:\.\d+)?", text)]


def detect_feature(text):

    text = text.lower()

    # 🔥 PRIORITÀ: keyword esplicite
    if "precipitation" in text:
        return "precipitation"

    if "temperature" in text:
        return "temperature"

    if "evapotranspiration" in text:
        return "evapotranspiration"

    if "biodiversity" in text or "species" in text:
        return "biodiversity"

    if "tree cover" in text:
        return "tree_cover"

    if "impervious" in text:
        return "imperviousness"

    # --------------------------------------------------
    # fallback su unità
    # --------------------------------------------------

    if "°c" in text:
        return "temperature"

    if "%" in text:
        return "precipitation"

    return None


# ======================================================
# SPLIT STANDARD (vs / versus / or)
# ======================================================

def split_vs(q):

    parts = re.split(r"\bvs\b|\bversus\b|\bor\b", q)

    if len(parts) >= 2:
        return parts[0], parts[1]

    return None, None


# ======================================================
# SPLIT FIRST / SECOND
# ======================================================

def split_first_second(q):

    pattern = r"(?:first[^:,.]*[:,-]?)(.*?)(?:second[^:,.]*[:,-]?)(.*)"
    match = re.search(pattern, q)

    if match:
        return match.group(1), match.group(2)

    return None, None


# ======================================================
# 🔥 NEW: SPLIT ONE / AND ONE
# ======================================================

def split_one_and_one(q):

    pattern = r"one\s+with\s+(.*?)\s+and\s+one\s+with\s+(.*)"

    match = re.search(pattern, q)

    if match:
        return match.group(1), match.group(2)

    return None, None


# ======================================================
# PARSE SIMPLE SCENARIO
# ======================================================

def parse_simple(text):

    feature = detect_feature(text)
    numbers = extract_numbers(text)

    if not feature or not numbers:
        return None

    value = numbers[0]

    # 🔥 SIGN DETECTION
    if "decrease" in text or "decreases" in text or "-" in text:
        value = -abs(value)

    elif "increase" in text or "increases" in text or "+" in text:
        value = abs(value)

    return {feature: value}


# ======================================================
# PARSE "FROM X TO Y"
# ======================================================

def parse_from_to(q):

    match = re.search(r"from\s+([+-]?\d+\.?\d*)\s*(?:°c|%)?\s+to\s+([+-]?\d+\.?\d*)", q)

    if not match:
        return None, None

    v1 = float(match.group(1))
    v2 = float(match.group(2))

    feature = detect_feature(q)

    if not feature:
        return None, None

    scen_A = {feature: v1}
    scen_B = {feature: v2}

    return scen_A, scen_B


# ======================================================
# MAIN
# ======================================================

def parse_comparison_scenarios(question: str):

    q = question.lower()

    # 🔥 FIX UNICODE MINUS
    q = q.replace("−", "-")

    print("[PARSER v7 DEBUG]")

    # --------------------------------------------------
    # 1. FROM → TO (DELTA)
    # --------------------------------------------------

    scen_A, scen_B = parse_from_to(q)

    if scen_A and scen_B:
        print("Detected FROM→TO pattern")
        print("Parsed A:", scen_A)
        print("Parsed B:", scen_B)
        return scen_A, scen_B

    # --------------------------------------------------
    # 2. FIRST / SECOND
    # --------------------------------------------------

    a, b = split_first_second(q)

    if a and b:
        scen_A = parse_simple(a)
        scen_B = parse_simple(b)

        print("Detected FIRST/SECOND")
        print("Parsed A:", scen_A)
        print("Parsed B:", scen_B)

        if scen_A and scen_B:
            return scen_A, scen_B

    # --------------------------------------------------
    # 2.5 ONE / AND ONE 🔥
    # --------------------------------------------------

    a, b = split_one_and_one(q)

    if a and b:
        scen_A = parse_simple(a)
        scen_B = parse_simple(b)

        print("Detected ONE/AND")
        print("Parsed A:", scen_A)
        print("Parsed B:", scen_B)

        if scen_A and scen_B:
            return scen_A, scen_B

    # --------------------------------------------------
    # 3. VS / OR
    # --------------------------------------------------

    a, b = split_vs(q)

    if a and b:
        scen_A = parse_simple(a)
        scen_B = parse_simple(b)

        print("Detected VS")
        print("Parsed A:", scen_A)
        print("Parsed B:", scen_B)

        if scen_A and scen_B:
            return scen_A, scen_B

    # --------------------------------------------------
    # FAIL
    # --------------------------------------------------

    print("A text:", a)
    print("B text:", b)

    return None, None