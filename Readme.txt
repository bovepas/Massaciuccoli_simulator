Massaciuccoli Digital Twin — AI Agent

An interactive AI-powered digital twin of the Massaciuccoli Lake ecosystem.

The system combines:

* environmental data
* statistical modeling
* rule-based reasoning
* LLM-based explanations (via Ollama)

to answer complex ecological questions.

---
Quick Start (Recommended)

### 1. Install prerequisites

Make sure you have installed:

* Docker Desktop
  https://www.docker.com/products/docker-desktop

---

### 2. Clone the repository

```bash
git clone https://github.com/bovepas/Massaciuccoli_simulator.git
cd Massaciuccoli_simulator
3. Start the system
docker compose up -d ollama
4. IMPORTANT — Start Ollama model service

The system requires a local LLM to generate explanations.

After starting Docker, run:

docker exec -it ollama ollama pull llama3:8b

⚠️ This step is required only the first time.
It downloads the language model used by the system.

5. Start interacting
docker compose run --rm massaciuccoli_app

Once running, you will see:

Massaciuccoli Digital Twin — interactive

You can now ask questions like:

Understanding drivers

Which environmental variables are most influential in increasing ecosystem risk?
What factors drive biodiversity loss in the lake system?

Understanding relationships (cause-effect)

How does temperature affect precipitation in the lake basin?
How does an increase in temperature influence ecosystem risk from 0 to 5?
What is the effect of evapotranspiration on water availability?

Comparing scenarios (IMPORTANT: you must specify both scenarios)

Compare ecosystem risk when temperature increases by 2°C versus when precipitation decreases by 10%.
Which scenario is worse: temperature +3°C or precipitation −20%?
Compare two scenarios: one with increased tree cover (70%) and one with reduced biodiversity (−30%).

Retrieving latest environmental data

Retrieve the latest average temperature data.
What is the latest precipitation change?
Show the latest environmental conditions of the system.

Notes:

When comparing scenarios, always specify both conditions clearly.
The system answers based on a scientific knowledge base of the Massaciuccoli lake ecosystem.

Type:

exit

to stop the system.

System Architecture

The system is composed of:

Router → detects question type
Tasks → specialized modules (drivers, dependency, delta, etc.)
RAG modules → generate explanations
Dummy ecological model → computes ecosystem risk
Ollama (LLM) → enhances explanations
Supported Question Types
Ecosystem risk assessment
Feature importance
Scenario comparison
Environmental dependencies
Drivers of change
Biodiversity analysis
Species habitat suitability (ENM)
Services
massaciuccoli_app

Main application container running the AI agent.

ollama

Local LLM service used for generating explanations.

Project Structure (simplified)
app/
 ├── versions/           # orchestrator + model
 ├── tasks/              # task handlers
 ├── knowledge/          # RAG modules
 ├── utils/              # parsers
 ├── data/               # environmental dataset
 └── enm/                # species models
Notes
The system requires the Ollama model (llama3:8b) to generate explanations.
Without it, fallback explanations will be used.
First startup may take several minutes (model download).
Demo Tips

For best results, try:

causal questions
"what drives..." questions
comparisons
scenario changes
Stop the system

Press CTRL + C or run:

docker compose down