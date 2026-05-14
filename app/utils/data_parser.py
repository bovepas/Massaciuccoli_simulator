# -*- coding: utf-8 -*-

def parse_data_request(question: str):

    q = question.lower()

    if "temperature" in q:
        return {"variable": "temperature change"}

    if "precipitation" in q or "rain" in q:
        return {"variable": "water from rain"}

    if "evaporation" in q:
        return {"variable": "evaporation change"}

    if "tree" in q:
        return {"variable": "tree"}

    if "grass" in q:
        return {"variable": "grassland"}

    if "species" in q or "biodiversity" in q:
        return {"variable": "species richness"}

    # 🔥 fallback: tutto
    return {"variable": None}