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
I'm going to give you a table in CSV format that describes ecosystem, anthropogenic, climatic,
and environmental variables with coordinate values associated.

This dataset is meant to support ecosystem risk assessment for the basin of the Massaciuccoli Lake
in Tuscany, Italy.

The table is structured as follows:
- The first row contains long names for the variables associated with the columns.
- The second row contains a long description and explanation of the meaning of each column.
- From the third row to the end, the variables' values are reported.
- Values may include "NA", meaning undefined, as explained in the column description.

The first two columns contain coordinate values associated with geospatial cells
at 0.0005 degree resolution (approximately 55 m).

All variables represent annual aggregations.
Some variables refer to differences with respect to the reference period 1971–2010 ("recent past").
Some variables refer to changes over the past decade (2015–2025).

This contextual description MUST be used to interpret the dataset.
"""


# =========================
# PROMPT 2 — BACKGROUND TERRITORIALE
# =========================
PROMPT_2_BACKGROUND = """
The Massaciuccoli Lake basin is a complex socio-ecological system characterized by interactions
between biodiversity, land use, climate, and hydrological processes.

Human activities coexist with areas of high ecological value, particularly wetlands and habitats
relevant for bird populations. Climate change affects temperature and water availability, influencing
habitat suitability and ecosystem functioning.

This background information provides contextual understanding only and does NOT introduce
additional evidence beyond the dataset variables.
"""


# =========================
# PROMPT 3 — RUOLO Q&A (DIGITAL TWIN — FASE CONCETTUALE)
# =========================
PROMPT_3_QA_ROLE = """
You are an ecosystem interpreter chatbot for the Massaciuccoli Lake basin.

Your role is to help users understand the ecosystem status and the ecosystem risk classification
using ONLY the dataset structure, variables, and conceptual relationships.

You can answer questions that:
- Clarify the meaning of variables or risk classes
- Explain qualitative relationships between stressor TYPES
- Compare ecosystem conditions conceptually (e.g., more stressed vs less stressed)
- Explain what a "critical ecosystem condition" means in qualitative terms

You must refuse or reframe questions that:
- Ask for numerical predictions or simulations
- Ask for future projections, dates, or timelines
- Ask quantitative "what-if" scenarios (e.g., percentage increases)
- Ask for management, policy, or intervention decisions

When refusing a question:
- Clearly explain why it cannot be answered
- Explain what type of scientific model or data would be required
- Stay neutral and informative
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
# METADATI → TESTO
# =========================
def metadata_to_text(metadata):
    return "\n".join(f"{k}: {v}" for k, v in metadata.items())


# =========================
# PROMPT Q&A
# =========================
def ask_ecosystem_question(metadata, user_question):
    schema_text = metadata_to_text(metadata)

    prompt = f"""
CONTEXT 1 – DATASET AND METHODOLOGY (authoritative):
{PROMPT_1_CONTEXT}

DATASET SCHEMA (authoritative reference):
{schema_text}

CONTEXT 2 – STUDY AREA BACKGROUND (contextual only):
{PROMPT_2_BACKGROUND}

ROLE:
{PROMPT_3_QA_ROLE}

USER QUESTION:
{user_question}

INSTRUCTIONS:
Answer the question if it is allowed by the ROLE.
If it is not allowed, refuse politely and explain why,
and state what would be needed to answer it scientifically.
"""

    response = client.generate(
        model="llama3",
        prompt=prompt,
        options={"temperature": 0}
    )

    return response.get("response", "")


# =========================
# MAIN — Q&A LOOP
# =========================
if __name__ == "__main__":
    print("=== Massaciuccoli Lake Ecosystem Q&A (Conceptual Digital Twin) ===\n")

    df, metadata = leggi_csv_con_metadati(CSV_PATH)

    print("Esempi di DOMANDE LECITE:")
    print("- What does a high ecosystem risk classification represent?")
    print("- How do climatic and anthropogenic stressors interact conceptually?")
    print("- Why might areas with high biodiversity also be considered fragile?\n")

    print("Esempi di DOMANDE NON LECITE:")
    print("- What will happen to the ecosystem in 2050?")
    print("- If temperature increases by 2°C, what happens?")
    print("- Which management actions should be taken?\n")

    while True:
        user_question = input("Ask a question (or type 'exit'): ")

        if user_question.lower() in ["exit", "quit"]:
            print("Exiting ecosystem Q&A.")
            break

        answer = ask_ecosystem_question(metadata, user_question)
        print("\nAnswer:\n")
        print(answer)
        print("\n" + "-" * 60 + "\n")
