"""
Massaciuccoli Digital Twin
Orchestrator v22 — Safe Hybrid Explanation
"""

import re

from versions.v6_main import route_question
from versions.v7_dynamic_model import run_temporal_simulation
from knowledge.rag_pipeline import call_llm, generate_answer


# ======================================================
# CLEAN INPUT
# ======================================================

def clean_question(q: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s°%.,-]", "", q)


# ======================================================
# SCIENTIFIC CORE (NUMBERS LOCKED)
# ======================================================

def build_scientific_summary(delta, high_share, hotspot_share):

    trend = "increases" if delta > 0 else "decreases"

    return (
        f"Risk {trend} by {delta}, "
        f"with high-risk areas reaching {high_share*100:.1f}% "
        f"and hotspots covering {hotspot_share*100:.1f}%."
    )


# ======================================================
# SAFE NARRATIVE (NO NUMBERS)
# ======================================================

def generate_narrative_safe(delta):

    trend = "increasing" if delta > 0 else "decreasing"

    prompt = f"""
Write a short scientific interpretation.

CONTEXT:
- ecosystem risk is {trend}
- drivers: temperature increase and precipitation change
- risk is spatially concentrated (hotspots exist)

RULES:
- Do NOT use numbers
- Do NOT quantify anything
- Do NOT introduce new variables
- Do NOT add recommendations
- Max 3 sentences
- Explain:
  1. what is happening
  2. why (climate drivers)
  3. spatial concentration
"""

    return call_llm(prompt).strip()


# ======================================================
# SCENARIO PARSER
# ======================================================

def extract_time_scenario(question: str):

    q = question.lower()

    rcp = "rcp45"
    year = "2050"

    if "8.5" in q or "rcp85" in q:
        rcp = "rcp85"

    if "2100" in q:
        year = "2100"

    return rcp, year


# ======================================================
# MAIN
# ======================================================

def handle_question(question: str):

    print(f"\n❓ Question: {question}")

    question = clean_question(question)

    decision = route_question(question)
    route = decision["route"]

    print(f"➡️ ROUTE: {route}")

    if route == "dynamic_model":

        print("🌍 CLIMATE + SPATIAL + SAFE HYBRID")

        rcp, year = extract_time_scenario(question)

        base, future, hotspots = run_temporal_simulation(rcp, year)

        delta = round(future["mean_risk"] - base["mean_risk"], 3)

        summary = build_scientific_summary(
            delta,
            future["high_share"],
            hotspots["share"]
        )

        narrative = generate_narrative_safe(delta)

        return f"""
📈 Climate-driven Simulation

Scenario:
- RCP: {rcp.upper()}
- Year: {year}

Initial mean risk: {base["mean_risk"]}
Final mean risk: {future["mean_risk"]}

Δ Risk: {delta}

📍 Spatial Insight
High-risk areas: {future["high_share"]*100:.1f}%

🔥 Hotspots
Top 5% areas: {hotspots["share"]*100:.1f}%

📊 Scientific summary
{summary}

🧠 Interpretation
{narrative}
"""

    if route == "llm_only":
        return generate_answer(question)

    return "Route not handled."


# ======================================================
# CLI
# ======================================================

def run_cli():

    print("\n=== Digital Twin v22 — Safe Scientific AI ===\n")

    while True:
        q = input("Ask a question: ")

        if q.lower() in ["exit", "quit"]:
            break

        print("\nProcessing...\n")
        ans = handle_question(q)

        print("\n=== Final Answer ===\n")
        print(ans)
        print("\n---------------------------\n")


if __name__ == "__main__":
    run_cli()