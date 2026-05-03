"""
Range Parser — v8 (safe unit handling, no wrong assumptions)
"""

import re


# ======================================================
# FEATURE DETECTION
# ======================================================

def detect_feature(text, unit=None):

    # --- explicit keywords (HIGH PRIORITY) ---
    if "temperature" in text:
        return "Change in average temperature compared to a recent past"

    if "precipitation" in text:
        return "Cumulative change in precipitation compared to a recent past"

    if "evapotranspiration" in text:
        return "Relative change in the potential evapotranspiration compared to a recent past"

    # --- safe unit inference ---
    if unit == "°c":
        return "Change in average temperature compared to a recent past"

    # ❗ DO NOT infer from % alone
    # it's ambiguous (temperature %, vegetation %, etc.)

    return None


# ======================================================
# MAIN PARSER
# ======================================================

def parse_range(question: str):

    q = question.lower()

    pattern = r"from\s+([+-]?\d+\.?\d*)\s*(°c|%)?\s+to\s+([+-]?\d+\.?\d*)\s*(°c|%)?"

    match = re.search(pattern, q)

    if match:

        v_from = float(match.group(1))
        v_to = float(match.group(3))

        unit = match.group(2) or match.group(4)

        feature = detect_feature(q, unit)

        print("[PARSER v8 DEBUG]")
        print("Detected FROM→TO pattern")
        print("Unit:", unit)
        print("Feature:", feature)
        print("From:", v_from)
        print("To:", v_to)

        # ❗ safety check
        if feature is None:
            print("[WARNING] Feature not recognized from range")

        return {
            "feature": feature,
            "from": v_from,
            "to": v_to
        }

    return None