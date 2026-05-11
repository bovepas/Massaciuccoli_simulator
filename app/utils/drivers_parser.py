# -*- coding: utf-8 -*-

"""
Drivers Parser — v3 (robust goal detection)

✔ Detects target variable
✔ Detects intent: increase / decrease / degrade
✔ Handles more linguistic variants
"""

from utils.feature_mapping import FEATURE_MAPPING


# ======================================================
# GOAL KEYWORDS
# ======================================================

DEGRADE_KEYWORDS = [
    "degrade",
    "degradation",
    "decrease",
    "reduce",
    "reduction",
    "decline",
    "loss",
    "losing",
    "worsen",
    "drop"
]

INCREASE_KEYWORDS = [
    "increase",
    "increasing",
    "improve",
    "improvement",
    "enhance",
    "growth",
    "grow",
    "rise"
]


# ======================================================
# TARGET DETECTION
# ======================================================

def parse_drivers_target(question: str):

    q = question.lower()

    for key in FEATURE_MAPPING.keys():
        if key in q:
            return key

    return None


# ======================================================
# GOAL DETECTION
# ======================================================

def parse_drivers_goal(question: str):

    q = question.lower()

    if any(k in q for k in DEGRADE_KEYWORDS):
        return "decrease"

    if any(k in q for k in INCREASE_KEYWORDS):
        return "increase"

    return "neutral"