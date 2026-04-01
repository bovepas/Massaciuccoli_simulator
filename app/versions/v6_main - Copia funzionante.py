import os
import json
from ollama import Client

# =========================
# Configurazione Ollama
# =========================
OLLAMA_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://ollama:11434"
)

client = Client(host=OLLAMA_URL)


# =========================
# ROUTER PROMPT (SYSTEM)
# =========================
ROUTER_SYSTEM_PROMPT = """
You are a QUESTION ROUTER for a digital twin of an ecosystem.

Your task is NOT to answer the question.
Your task is ONLY to classify the question and decide which type of tool
would be required to answer it correctly.

The question may be written in any language (e.g., English or Italian).

You must analyze the question and determine:
- whether it is conceptual or quantitative
- whether it involves hypothetical changes (what-if)
- whether it involves time or future scenarios
- whether it focuses on species, habitat, or ecological suitability
- whether it can be answered using reasoning only
- or whether it requires a predictive scientific model

IMPORTANT RULES ABOUT TIME:

- Do NOT assume temporal or dynamic behavior unless the question explicitly
  mentions time references such as years, decades, "by", "over time",
  "nel tempo", "entro", or similar expressions.

- References to "climate change" alone do NOT imply temporal dynamics.

IMPORTANT RULES ABOUT WHAT-IF:

- Hypothetical questions may be expressed as:
  "If ...", "Se ...", "Cosa succede se ...", "Nel caso in cui ..."

- A what-if question is QUANTITATIVE ONLY IF it explicitly contains
  numerical values, percentages, thresholds, or units of measure
  (e.g., %, °C, numeric values).

- What-if questions WITHOUT explicit numbers are ALWAYS qualitative.

CRITICAL DISTINCTIONS ABOUT MODELS:

1. CONCEPTUAL INTERPRETATION (llm_only)
- Questions that ask to EXPLAIN or DESCRIBE relationships
  between variables or stressors.
- These questions do NOT require predictive models.

2. WHAT-IF QUALITATIVE (llm_only)
- Hypothetical questions without explicit numerical values.
- These questions explore conceptual changes and relationships.
- These questions MUST NOT use regression, emulators, or ENM.

3. WHAT-IF QUANTITATIVE ON STRESSORS (regression_or_emulator)
- Questions that describe numerical changes (percentages, degrees, values)
  in environmental, climatic, or anthropogenic stressors
  and ask how ecosystem risk responds.
- These questions are static and scenario-based.
- These questions MUST NOT use ENM.

4. ECOLOGICAL NICHE / SPECIES DISTRIBUTION MODELS (enm)
- ENM MUST be selected ONLY when the question explicitly refers to:
  species, birds, animals, habitat suitability, idoneità dell’habitat,
  suitability, species distribution, or ecological niches.

5. TEMPORAL DYNAMIC MODELS (dynamic_model)
- Dynamic models must be selected ONLY when explicit temporal evolution
  is requested.

6. NORMATIVE / PRESCRIPTIVE QUESTIONS (refuse)
- Questions that ask for strategies, best actions, management decisions,
  policies, recommendations, or value judgments MUST be refused.

You must NOT:
- Answer the question
- Explain ecosystem processes
- Perform reasoning about outcomes
- Add suggestions, opinions, or interpretations

You must output ONLY a JSON object that follows this schema:

{
  "question_type": "interpretation | what_if_qualitative | what_if_quantitative | ecological_model | temporal_dynamic | normative",
  "is_what_if": true | false,
  "is_quantitative": true | false,
  "has_time_reference": true | false,
  "domain_focus": ["climate", "biodiversity", "land_use", "ecosystem_risk", "hydrology"],
  "recommended_tool": "llm_only | regression_or_emulator | enm | dynamic_model | refuse",
  "confidence": 0.0-1.0
}

No additional text is allowed.
"""


# =========================
# ROUTER FUNCTION
# =========================
def route_question(user_question: str) -> dict:

    prompt = f"""
SYSTEM:
{ROUTER_SYSTEM_PROMPT}

USER QUESTION:
{user_question}
"""

    try:
        response = client.generate(
            model="llama3:8b",
            prompt=prompt,
            options={"temperature": 0}
        )
    except Exception as e:
        return {
            "route": "error",
            "message": f"Ollama connection failed: {str(e)}"
        }

    raw_output = response.get("response", "").strip()

    try:
        classification = json.loads(raw_output)
    except json.JSONDecodeError:
        return {
            "route": "error",
            "message": "Router failed to produce valid JSON.",
            "raw_output": raw_output
        }

    tool = classification.get("recommended_tool", "refuse")

    # ======================================================
    # 🔥 OVERRIDE LOGICO (CRITICO)
    # ======================================================

    q = user_question.lower()

    # 1. Numeric stressor → forza emulator
    if (
        any(k in q for k in ["temperature", "precipitation", "species"])
        and (
            any(char.isdigit() for char in q)
            or "%" in q
            or "°c" in q
        )
    ):
        tool = "regression_or_emulator"
        classification["is_quantitative"] = True
        classification["question_type"] = "what_if_quantitative"

    # 2. ENM detection hard rule
    if any(k in q for k in ["habitat", "suitability", "distribution", "where"]):
        tool = "enm"

    return {
        "route": tool,
        "classification": classification
    }


# =========================
# MAIN — ROUTER LOOP
# =========================
if __name__ == "__main__":

    print("=== Massaciuccoli Digital Twin — Question Router (v6.1) ===\n")
    print("This module ONLY classifies questions and decides which tool is required.")
    print("It does NOT answer questions.\n")
    print("Type 'exit' to quit.\n")

    while True:

        user_question = input("Enter a question to route: ")

        if user_question.lower() in ["exit", "quit"]:
            print("Exiting question router.")
            break

        print("\n🧭 Routing question...\n")

        decision = route_question(user_question)

        if decision["route"] == "error":
            print("❌ Router error:")
            print(decision["message"])
            if "raw_output" in decision:
                print("Raw output:")
                print(decision["raw_output"])
            print("\n" + "-" * 60 + "\n")
            continue

        classification = decision["classification"]

        print("✅ Classification result:\n")
        print(json.dumps(classification, indent=2, ensure_ascii=False))

        print("\n📌 Routing decision:")
        print(f"→ Recommended tool: {decision['route']}")

        print("\n" + "-" * 60 + "\n")