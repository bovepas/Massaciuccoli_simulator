# prompts/tasks/dependency.py

# ======================================================
# DEPENDENCY → ECOSYSTEM RISK
# ======================================================

DEPENDENCY_RISK_TASK = """
QUESTION:
How does {source} affect ecosystem risk?

MODEL RESULTS:
{dependency_block}

TASK

Explain the relationship between the source variable
and ecosystem risk using the provided evidence.
"""


# ======================================================
# DEPENDENCY → FEATURE
# ======================================================

DEPENDENCY_FEATURE_TASK = """
QUESTION:
How does {source} influence {target}?

MODEL RESULTS:
{dependency_block}

TASK

Report the observed association using the provided evidence.

Do not explain underlying mechanisms.

Do not hypothesize ecological processes.

Summarize only:
- strength
- direction
- interaction type
- confidence
"""