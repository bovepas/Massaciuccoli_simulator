# -*- coding: utf-8 -*-

import re
from utils.logger import log_section, log_question, log_route


# ======================================================
# NORMALIZATION
# ======================================================

def normalize(q: str) -> str:
    return q.lower().strip()


# ======================================================
# PARSER
# ======================================================

VARIABLE_KEYWORDS = [
    "temperature",
    "precipitation",
    "biodiversity",
    "tree cover",
    "grassland",
    "evapotranspiration",
    "productivity"
]


def detect_target(q: str):
    if "risk" in q or "ecosystem" in q:
        return "risk"
    if any(v in q for v in VARIABLE_KEYWORDS):
        return "variable"
    return "unknown"


def parse_semantics(q: str):

    # ==========================================
    # 🔥 STABILITY → RISK (semantic mapping)
    # ==========================================
    mentions_stability = False

    if "stability" in q:
        print("[ROUTER] 'stability' interpreted as 'risk'")
        q = q.replace("stability", "risk")
        mentions_stability = True

    return {
        "target": detect_target(q),
        "has_range": bool(re.search(r"\bfrom\b.*\bto\b", q)),
        "has_comparison": any(k in q for k in [" vs ", " versus ", "compare"]),
        "has_condition": any(k in q for k in ["if", "given", "when"]),
        "asks_influence": any(k in q for k in ["affect", "influence", "effect", "impact"]),
        "asks_importance": any(k in q for k in ["most", "top", "important", "influential"]),
        "asks_drivers": any(k in q for k in ["drivers", "drive"]),
        "mentions_habitat": any(k in q for k in ["habitat", "suitability"]),
        "mentions_stability": mentions_stability
    }


# ======================================================
# ROUTER
# ======================================================

def route_question(question: str):

    q = normalize(question)

    log_section("ROUTER V10 NO-CHAT FINAL")
    log_question(question)

    parsed = parse_semantics(q)

    # ---------------- 🔥 DATA (NEW) ----------------
    if any(k in q for k in ["latest", "retrieve", "data"]):
        log_route("DATA")
        return {"type": "data"}

    # ---------------- ENM ----------------
    if parsed["mentions_habitat"]:
        log_route("ENM")
        return {"type": "enm"}

    # ---------------- DELTA ----------------
    if parsed["has_range"]:
        log_route("DELTA")
        return {"type": "delta"}

    # ---------------- COMPARISON ----------------
    if parsed["has_comparison"] or re.search(r"\bor\b.*\d", q):
        log_route("COMPARISON")
        return {"type": "comparison"}

    # ---------------- DRIVERS (strong pattern) ----------------
    if "drive" in q and ("which factors" in q or "which variables" in q):
        log_route("DRIVERS (pattern)")
        return {"type": "drivers"}

    # ---------------- IMPORTANCE ----------------
    if (
        "which factors" in q or
        "which variables" in q or
        "main factors" in q
    ):
        log_route("IMPORTANCE (pattern)")
        return {"type": "importance"}

    if parsed["asks_importance"] and parsed["target"] == "risk":
        log_route("IMPORTANCE")
        return {"type": "importance"}

    # ---------------- DRIVERS ----------------
    if parsed["asks_drivers"]:

        if parsed["has_condition"]:
            log_route("IMPORTANCE (drivers+condition)")
            return {"type": "importance"}

        if parsed["target"] == "risk":
            log_route("IMPORTANCE (drivers->risk)")
            return {"type": "importance"}

        log_route("DRIVERS")
        return {"type": "drivers"}

    # ---------------- INTERACTION → ASSESSMENT ----------------
    if parsed["asks_influence"] and (" and " in q or "interact" in q):
        log_route("ASSESSMENT (interaction)")
        return {"type": "assessment"}

    # ---------------- DEPENDENCY ----------------
    if parsed["asks_influence"]:

        # 🔥 PRIORITÀ: spiegazioni causali → dependency
        if not parsed["has_condition"] and not parsed["has_range"]:
            log_route("DEPENDENCY (influence)")
            return {"type": "dependency"}

        # 🔥 solo se c'è scenario → assessment
        log_route("ASSESSMENT (influence+scenario)")
        return {"type": "assessment"}

    if parsed["has_condition"] and parsed["target"] != "risk":
        log_route("DEPENDENCY (fallback)")
        return {"type": "dependency"}

    # ---------------- ASSESSMENT ----------------
    if parsed["target"] == "risk":
        log_route("ASSESSMENT")
        return {"type": "assessment"}

    # ---------------- HARD DEFAULT ----------------
    log_route("ASSESSMENT (default)")
    return {"type": "assessment"}


# ======================================================
# STUB (evita crash SHAP)
# ======================================================

def explain_with_shap(*args, **kwargs):
    return None