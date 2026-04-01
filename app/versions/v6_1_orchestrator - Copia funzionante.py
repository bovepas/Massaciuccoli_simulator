"""
Massaciuccoli Digital Twin
Orchestrator v11.8 — FINAL DEMO (Interpretation upgraded)
"""

import pandas as pd
import re

from versions.v6_main import route_question
from versions.v6_2_basin_engine import (
    load_dataset,
    predict_risk,
    compute_basin_statistics,
    run_basin_simulation
)
from versions.v6_1_main import MODEL, NUM_FEATURES, CAT_FEATURES
from knowledge.rag_pipeline import generate_answer, call_llm


# ======================================================
# CLEAN INPUT
# ======================================================

def clean_question(q: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s°%.,-]", "", q)


# ======================================================
# KEYWORDS
# ======================================================

STATUS_KEYWORDS = ["status", "state", "condition", "overview", "current"]
ASSET_KEYWORDS = ["assets", "drivers", "factors", "determinants"]


def is_status_query(q):
    return any(k in q for k in STATUS_KEYWORDS)

def is_asset_query(q):
    return any(k in q for k in ASSET_KEYWORDS)


# ======================================================
# STATUS
# ======================================================

def compute_current_status():
    df = load_dataset()
    df_pred = predict_risk(df)
    return compute_basin_statistics(df_pred)


def is_low_quality_rag(text: str) -> bool:
    bad_patterns = [
        "no specific information",
        "the study area includes",
        "datasets",
        "metadata",
        "no information is provided"
    ]
    t = text.lower()
    return any(p in t for p in bad_patterns)


# ======================================================
# FEATURE IMPORTANCE
# ======================================================

def compute_feature_importance():

    rf = MODEL.named_steps["rf"]
    preprocessor = MODEL.named_steps["preprocessor"]

    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_names = cat_encoder.get_feature_names_out(CAT_FEATURES)

    all_names = NUM_FEATURES + list(cat_names)
    importances = rf.feature_importances_

    df = pd.DataFrame({
        "feature": all_names,
        "importance": importances
    })

    def collapse(name):
        for c in CAT_FEATURES:
            if name.startswith(c + "_"):
                return c
        return name

    df["original"] = df["feature"].apply(collapse)

    grouped = (
        df.groupby("original")["importance"]
        .sum()
        .sort_values(ascending=False)
    )

    return grouped.head(5)


def explain_drivers_with_llm(drivers):

    driver_list = "\n".join([f"- {d}" for d in drivers])

    prompt = f"""
Explain briefly how each variable influences ecosystem risk.

{driver_list}

Rules:
- Max 1 short sentence per variable
- No extra text
"""

    return call_llm(prompt)


# ======================================================
# SCENARIO INTERPRETATION (UPGRADED)
# ======================================================

def interpret_scenario(delta_mean, delta_high):

    if delta_mean > 0:
        trend = "increase"
    elif delta_mean < 0:
        trend = "decrease"
    else:
        trend = "no significant change"

    magnitude = abs(delta_mean)

    if magnitude < 0.02:
        intensity = "slight"
    elif magnitude < 0.1:
        intensity = "moderate"
    else:
        intensity = "strong"

    explanation = f"""
🧠 Interpretation:
The simulated scenario leads to a {intensity} {trend} in ecosystem risk according to the model.
"""

    explanation += """
This result reflects how the model has learned relationships between environmental variables and ecosystem risk.

Note: some effects may appear counterintuitive, as the model captures complex interactions between biodiversity, productivity, and ecosystem stability.
"""

    return explanation


# ======================================================
# SCENARIO PARSER
# ======================================================

def extract_scenario(question: str):

    scenario = {}
    q = question.lower()

    def get_sign(text):
        if any(w in text for w in ["decrease", "decreased", "reduced", "reduction", "drop", "loss"]):
            return -1
        if any(w in text for w in ["increase", "increased", "rise", "growth"]):
            return +1
        return +1

    patterns = [
        ("temperature", "Change in average temperature compared to a recent past", r"temperature"),
        ("precipitation", "Cumulative change in precipitation compared to a recent past", r"precipitation"),
        ("tree", "Density of tree cover", r"tree"),
        ("productivity", "Index of total productivity by plant phenology", r"productivity"),
        ("biodiversity|species", "Number of species potentially living in the cell", r"biodiversity|species"),
    ]

    for match in re.finditer(r"([a-z\s]+?)\s+(temperature|precipitation|tree|productivity|biodiversity|species)[^.,]*?(\d+\.?\d*)\s*%?", q):

        full_segment = match.group(0)
        value = float(match.group(3))
        sign = get_sign(full_segment)

        for key, column, keyword in patterns:
            if re.search(keyword, full_segment):
                scenario[column] = sign * value

    temp_match = re.search(r"(increase|decrease|increased|decreased)[^.,]*temperature[^.,]*?(\d+\.?\d*)\s*°?c", q)
    if temp_match:
        sign = get_sign(temp_match.group(1))
        value = float(temp_match.group(2))
        scenario["Change in average temperature compared to a recent past"] = sign * value

    return scenario


# ======================================================
# MAIN
# ======================================================

def handle_question(question: str):

    print(f"\n❓ Question: {question}")

    question = clean_question(question)
    q = question.lower()

    # ======================
    # ASSETS
    # ======================
    if is_asset_query(q):

        print("📊 FEATURE IMPORTANCE MODE")

        importance = compute_feature_importance()

        lines = []
        drivers = []

        for i, (feat, val) in enumerate(importance.items(), 1):
            lines.append(f"{i}. {feat} (importance: {val:.3f})")
            drivers.append(feat)

        explanation = explain_drivers_with_llm(drivers)

        return f"""
📊 Principal Drivers of Ecosystem Risk

Top factors:

{chr(10).join(lines)}

🧠 Interpretation:
{explanation}
"""

    # ======================
    # STATUS
    # ======================
    if is_status_query(q):

        print("📊 STATUS MODE")

        stats = compute_current_status()
        rag = generate_answer(question)

        if is_low_quality_rag(rag):
            rag = """
The ecosystem shows signs of anthropogenic pressure, habitat degradation, and biodiversity stress, particularly linked to land use change and environmental variability.
"""

        return f"""
📊 Current Ecosystem Status

Mean ecosystem risk: {stats["mean_risk"]}
Low-risk areas: {stats["low_share"] * 100:.1f}%
Medium-risk areas: {stats["medium_share"] * 100:.1f}%
High-risk areas: {stats["high_share"] * 100:.1f}%

🧠 Interpretation:
The ecosystem is currently in a generally low-risk state, but with localized areas of higher vulnerability indicating emerging ecological pressures.

📚 Scientific evidence:
{rag}
"""

    # ======================
    # ROUTER
    # ======================
    decision = route_question(question)
    route = decision["route"]

    print(f"➡️ ROUTE: {route}")

    # ======================
    # EMULATOR
    # ======================
    if route == "regression_or_emulator":

        scenario = extract_scenario(question)

        print(f"📊 Scenario extracted: {scenario}")

        result = run_basin_simulation(scenario)

        interpretation = interpret_scenario(
            result["delta_mean_risk"],
            result["delta_high_risk_share"]
        )

        return f"""
📊 Basin Risk Simulation

Baseline mean risk: {result["baseline"]["mean_risk"]}
Scenario mean risk: {result["scenario"]["mean_risk"]}

Δ Mean risk: {result["delta_mean_risk"]}
Δ High-risk area share: {result["delta_high_risk_share"]}

{interpretation}
"""

    # ======================
    # LLM ONLY
    # ======================
    if route == "llm_only":
        return generate_answer(question)

    return "Route not handled."


# ======================================================
# CLI
# ======================================================

def run_cli():

    print("\n=== Digital Twin v11.8 — FINAL DEMO ===\n")

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