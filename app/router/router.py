# -*- coding: utf-8 -*-

"""
Simple Router (fallback version)
"""

def route_question(question: str):

    q = question.lower()

    if "change" in q and "from" in q and "to" in q:
        return {"type": "delta"}

    if "depend" in q or "relationship" in q:
        return {"type": "dependency"}

    if "important" in q or "driver" in q:
        return {"type": "importance"}

    return {"type": "assessment"}