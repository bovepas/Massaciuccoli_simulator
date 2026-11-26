import os
import pandas as pd
from ollama import Client

# =========================
# Configurazione Ollama
# =========================
client = Client(host=os.getenv("OLLAMA_URL", "http://ollama:11434"))
CSV_PATH = "massaciuccoli_data.csv"


# =========================
# PROMPT 1 — CONTESTO METODOLOGICO
# =========================
PROMPT_1_CONTEXT = """
This dataset describes ecosystem, anthropogenic, climatic, and environmental variables
used for ecosystem risk assessment in the Massaciuccoli Lake basin (Tuscany, Italy).

The dataset structure, variable meanings, and risk classification methodology
are authoritative references.
"""


# =========================
# PROMPT 2 — BACKGROUND TERRITORIALE
# =========================
PROMPT_2_BACKGROUND = """
The Massaciuccoli Lake basin is a complex socio-ecological system where climate,
land use, biodiversity, and environmental processes interact.

This background provides context only and does not introduce new evidence.
"""


# =========================
# PROMPT 3 — RUOLO WHAT-IF QUALITATIVO
# =========================
PROMPT_3_WHATIF_ROLE = """
You are a qualitative ecosystem reasoning agent.

You explore conceptual "what-if" hypotheses without numbers, timelines,
predictions, or decisions.

You explain how relationships between TYPES of stressors and ecosystem risk
would conceptually change under the given hypothesis.

You must NOT:
- Use numerical values or thresholds
- Introduce years or timelines
- Predict outcomes
- Propose management or policy actions
"""


# =========================
# LETTURA CSV CON METADATI
# =========================
def leggi_csv_con_metadati(path):
    raw = pd.read_csv(path, header=None)

    columns = raw.iloc[0].tolist()
    descriptions = raw.iloc[1].tolist()
    metadata = dict(zip(columns, descriptions))

    df = raw.iloc[2:].reset_index(drop=True)
    df.columns = columns

    return df, metadata


# =========================
# VALIDAZIONE WHAT-IF
# =========================
def validate_whatif(user_input: str) -> bool:
    forbidden_tokens = ["%", "°", "year", "years", "2050", "2100", "should", "manage", "policy"]
    if not user_input.strip().lower().startswith("if"):
        return False
    for token in forbidden_tokens:
        if token in user_input.lower():
            return False
    return True


# =========================
# METADATI → TESTO
# =========================
def metadata_to_text(metadata):
    return "\n".join(f"{k}: {v}" for k, v in metadata.items())


# =========================
# WHAT-IF Q&A
# =========================
def ask_whatif_question(metadata, user_question):
    schema_text = metadata_to_text(metadata)

    prompt = f"""
CONTEXT 1 – DATASET AND METHODOLOGY:
{PROMPT_1_CONTEXT}

DATASET SCHEMA:
{schema_text}

CONTEXT 2 – STUDY AREA BACKGROUND:
{PROMPT_2_BACKGROUND}

ROLE:
{PROMPT_3_WHATIF_ROLE}

QUALITATIVE WHAT-IF HYPOTHESIS:
{user_question}

INSTRUCTIONS:
- Treat the hypothesis as purely conceptual
- Describe how relationships between stressor TYPES and ecosystem risk
  would change qualitatively
- Do NOT use numbers, timelines, or actions
"""

    response = client.generate(
        model="llama3",
        prompt=prompt,
        options={"temperature": 0}
    )

    return response.get("response", "")


# =========================
# MAIN — WHAT-IF LOOP CON FEEDBACK
# =========================
if __name__ == "__main__":
    print("=== Massaciuccoli Lake Ecosystem — Qualitative What-If Mode (v5) ===\n")

    _, metadata = leggi_csv_con_metadati(CSV_PATH)

    print("✔️ Esempi di WHAT-IF VALIDI:")
    print("  - If anthropogenic pressure increases conceptually")
    print("  - If climatic stressors become more dominant")
    print("  - If ecological fragility increases\n")

    print("❌ Esempi di WHAT-IF NON VALIDI:")
    print("  - funzioni?")
    print("  - If temperature increases by 2°C")
    print("  - What will happen by 2050?\n")

    while True:
        user_question = input("Enter a qualitative what-if hypothesis (or type 'exit'): ")

        if user_question.lower() in ["exit", "quit"]:
            print("Exiting qualitative what-if mode.")
            break

        if not validate_whatif(user_question):
            print("\n⚠️ Invalid what-if hypothesis.")
            print("Please start with 'If' and describe a CONCEPTUAL change.")
            print("Example: If anthropogenic pressure increases conceptually\n")
            continue

        print("\n🧠 Processing qualitative what-if hypothesis...\n")

        answer = ask_whatif_question(metadata, user_question)

        print("Answer:\n")
        print(answer)
        print("\n" + "-" * 60 + "\n")
