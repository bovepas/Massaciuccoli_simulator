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
```

---

### 3. Start the system

```bash
docker compose up -d ollama



---

### 4. Download the LLM model (first time only)

Open a new terminal and run:

```bash
docker exec -it ollama ollama pull llama3:8b

This downloads the language model used for explanations.

---

### 5. Start interacting

```bash
docker compose run --rm massaciuccoli_app

Once running, you will see:

```
Massaciuccoli Digital Twin — interactive
```

You can now ask questions like:

* Which factors drive biodiversity loss?
* What drives ecosystem productivity?
* How does temperature affect precipitation?
* Compare two environmental scenarios

Type:

```bash
exit
```

to stop the system.

---

## System Architecture

The system is composed of:

* **Router** → detects question type
* **Tasks** → specialized modules (drivers, dependency, delta, etc.)
* **RAG modules** → generate explanations
* **Dummy ecological model** → computes ecosystem risk
* **Ollama (LLM)** → enhances explanations

---

## Supported Question Types

* Ecosystem risk assessment
* Feature importance
* Scenario comparison
* Environmental dependencies
* Drivers of change
* Biodiversity analysis
* Species habitat suitability (ENM)

---

## Services

### `massaciuccoli_app`

Main application container running the AI agent.

### `ollama`

Local LLM service used for generating explanations.

---

## Project Structure (simplified)

```
app/
 ├── versions/           # orchestrator + model
 ├── tasks/              # task handlers
 ├── knowledge/          # RAG modules
 ├── utils/              # parsers
 ├── data/               # environmental dataset
 └── enm/                # species models
```

---

##  Notes

* The system requires the Ollama model (`llama3:8b`) to generate explanations.
* Without it, fallback explanations will be used.
* First startup may take several minutes (model download).

---

##  Demo Tips

For best results, try:

* causal questions
* "what drives..." questions
* comparisons
* scenario changes

---

##  Stop the system

Press `CTRL + C` or run:

```bash
docker compose down
```

---
