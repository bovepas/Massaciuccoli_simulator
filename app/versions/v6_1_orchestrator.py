# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Orchestrator v32 (MODEL + DATA INJECTION)

# Tasks still decoupled
# Model + dataset injected only where needed
# Stable for demo
"""

import sys
import os
import pandas as pd

# ======================================================
# PATH SETUP
# ======================================================

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ======================================================
# LOGGER
# ======================================================

from utils.logger import (
    log_section,
    log_question,
    log_route,
    log_data,
    log_error
)

# ======================================================
# TASKS
# ======================================================

from tasks.task_assessment import handle_assessment
from tasks.task_importance import handle_importance
from tasks.task_delta import handle_delta
from tasks.task_dependency import handle_dependency
from tasks.task_drivers import handle_drivers
from tasks.task_chat import handle_chat
from tasks.task_data import handle_data

# ======================================================
# ROUTER
# ======================================================

from versions.v6_1_main import route_question

# ======================================================
# PARSERS
# ======================================================

from utils.feature_parser import parse_features
from utils.range_parser import parse_range

# ======================================================
# 🔥 MODEL + DATA LOADING (FIXED)
# ======================================================

from versions.v6_1_emulator import load_and_train_emulator

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "massaciuccoli_data.csv")


def load_resources():

    print("# Loading model and dataset...")

    try:
        # dataset coerente con training
        dataset = pd.read_csv(DATA_PATH, skiprows=[1])

        # modello allenato al volo
        model = load_and_train_emulator(DATA_PATH)

        print("# Model trained and dataset loaded")
        return model, dataset

    except Exception as e:
        print("# ERROR loading resources:", e)
        return None, None


# ======================================================
# MAIN LOOP
# ======================================================

def run():

    print("# Loading ecosystem risk emulator...")

    model, dataset = load_resources()

    print("# Emulator ready.\n")
    print("Massaciuccoli Digital Twin — v138\n")

    while True:

        question = input("Ask a question (type 'exit' to quit): ")

        if question.lower() in ["exit", "quit"]:
            break

        # ==================================================
        # REQUEST
        # ==================================================

        log_section("NEW REQUEST")
        log_question(question)

        # ==================================================
        # ROUTING
        # ==================================================

        try:
            route = route_question(question)
            task_type = route.get("type")
            log_route(task_type)

        except Exception as e:
            log_error("ROUTING", e)
            continue

        # ==================================================
        # PARSING
        # ==================================================

        features = None
        range_info = None

        try:
            if task_type in ["assessment", "importance", "delta"]:
                log_section("PARSING")

                features = parse_features(question)
                range_info = parse_range(question)

                log_data("features", features)
                log_data("range", range_info)

            else:
                log_section("PARSING")
                log_data("skipped", f"Task '{task_type}' does not require parsing")

        except Exception as e:
            log_error("PARSING", e)
            continue

        # ==================================================
        # TASK EXECUTION
        # ==================================================

        try:
            log_section("TASK EXECUTION")
            log_data("task_type", task_type)

            # ----------------------------------------------
            # ASSESSMENT
            # ----------------------------------------------
            if task_type == "assessment":
                result = handle_assessment(question, features)

            # ----------------------------------------------
            # IMPORTANCE (FIXED)
            # ----------------------------------------------
            elif task_type == "importance":
                result = handle_importance(
                    question=question,
                    features=features,
                    model=model,
                    dataset=dataset
                )

            # ----------------------------------------------
            # DELTA
            # ----------------------------------------------
            elif task_type == "delta":
                result = handle_delta(question, features, range_info)

            # ----------------------------------------------
            # DEPENDENCY
            # ----------------------------------------------
            elif task_type == "dependency":
                result = handle_dependency(question, route)

            # ----------------------------------------------
            # DATA
            # ----------------------------------------------
            elif task_type == "data":
                result = handle_data(question, dataset=dataset)

            # ----------------------------------------------
            # DRIVERS
            # ----------------------------------------------
            elif task_type == "drivers":
                result = handle_drivers(question)

            # ----------------------------------------------
            # CHAT
            # ----------------------------------------------
            elif task_type == "chat":
                result = handle_chat(question)

            # ----------------------------------------------
            # UNKNOWN
            # ----------------------------------------------
            else:
                result = {
                    "summary": "Unknown task",
                    "data": {},
                    "drivers": [],
                    "interpretation": "Could not determine the task type."
                }

        except Exception as e:
            log_error("TASK EXECUTION", e)
            continue

        # ==================================================
        # OUTPUT
        # ==================================================

        log_section("OUTPUT")

        try:
            print("\nSUMMARY:")
            print(result.get("summary", ""))

            data = result.get("data", {})
            if data:
                print("\nDATA:")
                print(data)

            if "drivers" in result:
                print("\nDRIVERS:")
                for d in result["drivers"]:
                    print("-", d)

            print("\nINTERPRETATION:")
            print(result.get("interpretation", ""))

            print("\n---------------------------\n")

        except Exception as e:
            log_error("OUTPUT", e)
            continue


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    run()