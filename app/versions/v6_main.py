"""
Massaciuccoli Digital Twin
v6_main — ROUTER WRAPPER (uses v6_1_main)
"""

from versions.v6_1_main import route_question as core_router


def route_question(question: str):
    return core_router(question)