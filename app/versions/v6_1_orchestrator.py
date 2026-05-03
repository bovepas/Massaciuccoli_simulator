# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Orchestrator v25 (router fix)
"""

import sys
import os

# ROOT PATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tasks.task_assessment import handle_assessment
from tasks.task_importance import handle_importance
from tasks.task_delta import handle_delta
from tasks.task_dependency import handle_dependency

# 🔥 FIX QUI
from versions.v6_main import route_question

from utils.feature_parser import parse_features
from utils.range_parser import parse_range


# ======================================================
# MAIN LOOP
# ======================================================

def run():

    print("🔧 Loading ecosystem risk emulator...")
    print("✅ Emulator ready.\n")

    print("Massaciuccoli Digital Twin — v134 (interactive)\n")

    while True:

        question = input("Ask a question (type 'exit' to quit): ")

        if question.lower() in ["exit", "quit"]:
            break

        # --------------------------------------------------
        # ROUTING
        # --------------------------------------------------

        print("\n================ ROUTING DEBUG ================")
        print("QUESTION:", question)

        route = route_question(question)

        print("ROUTER OUTPUT:", route)

        task_type = route.get("type")

        print("SELECTED TASK:", task_type)
        print("==============================================")

        # --------------------------------------------------
        # PARSING
        # --------------------------------------------------

        features = parse_features(question)
        range_info = parse_range(question)

        print("[ORCHESTRATOR DEBUG] FEATURES PARSED:", features)
        print("[ORCHESTRATOR DEBUG] RANGE PARSED:", range_info)

        # --------------------------------------------------
        # TASK EXECUTION
        # --------------------------------------------------

        try:

            if task_type == "assessment":
                result = handle_assessment(question, features)

            elif task_type == "importance":
                result = handle_importance(question, features)

            elif task_type == "delta":
                result = handle_delta(question, features, range_info)

            elif task_type == "dependency":
                result = handle_dependency(question, route)

            else:
                result = {
                    "summary": "Unknown task",
                    "data": {},
                    "drivers": [],
                    "interpretation": "Could not determine the task type."
                }

        except Exception as e:
            print("[ERROR]", e)
            continue

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        print("\n--- RESULT ---\n")

        print("SUMMARY:")
        print(result.get("summary", ""))

        print("\nDATA:")
        print(result.get("data", {}))

        if "drivers" in result:
            print("\nDRIVERS:")
            for d in result["drivers"]:
                print("-", d)

        print("\nINTERPRETATION:")
        print(result.get("interpretation", ""))

        print("\n---------------------------\n")


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":
    run()