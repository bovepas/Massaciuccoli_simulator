# -*- coding: utf-8 -*-

"""
Massaciuccoli Digital Twin
Orchestrator v33 (TIMING INSTRUMENTATION)

✔ Request timing
✔ Routing timing
✔ Parsing timing
✔ Task timing
✔ Output timing
✔ Minimal invasive profiling
"""

import sys
import os
import pandas as pd

# ======================================================
# PATH SETUP
# ======================================================

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            ".."
        )
    )
)

# ======================================================
# LOGGER
# ======================================================

from utils.logger import (

    log_section,
    log_question,
    log_route,
    log_data,
    log_error,

    # 🔥 NEW
    start_timer,
    end_timer
)

# ======================================================
# TASKS
# ======================================================

from tasks.task_assessment import handle_assessment

from tasks.task_importance import handle_importance

from utils.importance_parser import parse_top_k

from tasks.task_delta import handle_delta

from tasks.task_dependency import handle_dependency

from tasks.task_drivers import handle_drivers

from tasks.task_chat import handle_chat

from tasks.task_data import handle_data

from tasks.task_comparison import handle_comparison

from tasks.task_enm import handle_enm

from tasks.task_importance_compare import handle_importance_compare


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
# MODEL + DATA LOADING
# ======================================================

from versions.v6_1_emulator import load_and_train_emulator

DATA_PATH = os.path.join(

    os.path.dirname(__file__),

    "..",

    "data",

    "massaciuccoli_data.csv"
)


# ======================================================
# LOAD RESOURCES
# ======================================================

def load_resources():

    print("# Loading model and dataset...")

    try:

        start_timer("resource_loading")

        dataset = pd.read_csv(
            DATA_PATH,
            skiprows=[1]
        )

        model = load_and_train_emulator(
            DATA_PATH
        )

        end_timer("resource_loading")

        print(
            "# Model trained and dataset loaded"
        )

        return model, dataset

    except Exception as e:

        log_error(
            "RESOURCE LOADING",
            e
        )

        return None, None


# ======================================================
# MAIN LOOP
# ======================================================

def run():

    print("# Loading ecosystem risk emulator...")

    model, dataset = load_resources()

    print("# Emulator ready.\n")

    print(
        "Massaciuccoli Digital Twin — v138\n"
    )

    while True:

        question = input(
            "Ask a question (type 'exit' to quit): "
        )

        if question.lower() in [
            "exit",
            "quit"
        ]:
            break

        if question.lower() == "cls":

            os.system(
                "cls" if os.name == "nt" else "clear"
            )

            continue

        # ==================================================
        # TOTAL REQUEST TIMER
        # ==================================================

        start_timer("total_request")

        log_section("NEW REQUEST")

        log_question(question)

        # ==================================================
        # ROUTING
        # ==================================================

        try:

            start_timer("routing")

            route = route_question(
                question
            )

            task_type = route.get("type")

            end_timer("routing")

            log_route(task_type)

        except Exception as e:

            log_error(
                "ROUTING",
                e
            )

            end_timer("routing")

            continue

        # ==================================================
        # PARSING
        # ==================================================

        parsed = None

        features = None

        range_info = None

        try:

            start_timer("parsing")

            if task_type in [
                "assessment",
                "importance",
                "delta"
            ]:

                log_section("PARSING")

                parsed = parse_features(

                    question,

                    return_metadata=True
                )

               
                
                features = parsed["features"]

                range_info = parse_range(
                    question
                )

                log_data(
                    "features",
                    features
                )

                log_data(
                    "range",
                    range_info
                )

            else:

                log_section("PARSING")

                log_data(

                    "skipped",

                    f"Task '{task_type}' "
                    f"does not require parsing"
                )

            end_timer("parsing")

        except Exception as e:

            log_error(
                "PARSING",
                e
            )

            end_timer("parsing")

            continue

        # ==================================================
        # TASK EXECUTION
        # ==================================================

        try:

            start_timer("task_execution")

            log_section("TASK EXECUTION")

            log_data(
                "task_type",
                task_type
            )

            # --------------------------------------------------
            # ASSESSMENT
            # --------------------------------------------------

            if task_type == "assessment":

                result = handle_assessment(

                    question=question,

                    features=features,

                    qualitative_changes=parsed.get(
                        "qualitative_changes",
                        []
                    ),

                    dataset=dataset,

                    model=model
                )

            # --------------------------------------------------
            # IMPORTANCE
            # --------------------------------------------------

            elif task_type == "importance":

                result = handle_importance(

                    question=question,

                    features=features,

                    model=model,

                    dataset=dataset,

                    top_k=parse_top_k(
                        question
                    )
                )

            # --------------------------------------------------
            # DELTA
            # --------------------------------------------------

            elif task_type == "delta":

                result = handle_delta(

                    question,

                    range_info,

                    features,
                    
                    parsed,

                    model
                )

            # --------------------------------------------------
            # DEPENDENCY
            # --------------------------------------------------

            elif task_type == "dependency":

                result = handle_dependency(
                    question,
                    route
                )

            # --------------------------------------------------
            # COMPARISON
            # --------------------------------------------------

            elif task_type == "comparison":

                result = handle_comparison(

                    question,

                    model,

                    dataset
                )

            # --------------------------------------------------
            # DATA
            # --------------------------------------------------

            elif task_type == "data":

                result = handle_data(

                    question,

                    dataset=dataset
                )

            # --------------------------------------------------
            # DRIVERS
            # --------------------------------------------------

            elif task_type == "drivers":

                result = handle_drivers(
                    question
                )
            # --------------------------------------------------
            # ENM
            # --------------------------------------------------

            elif task_type == "enm":

                result = handle_enm(
                    question
                )
            # --------------------------------------------------
            # IMPORTANCE COMPARE
            # --------------------------------------------------

            elif task_type == "importance_compare":

                result = handle_importance_compare(

                    question=question,

                    model=model,

                    dataset=dataset
                )   
                
            # --------------------------------------------------
            # CHAT
            # --------------------------------------------------

            elif task_type == "chat":

                result = handle_chat(
                    question
                )

            # --------------------------------------------------
            # UNKNOWN
            # --------------------------------------------------

            else:

                result = {

                    "summary":
                        "Unknown task",

                    "data":
                        {},

                    "drivers":
                        [],

                    "interpretation":
                        "Could not determine "
                        "the task type."
                }

            end_timer("task_execution")

        except Exception as e:

            log_error(
                "TASK EXECUTION",
                e
            )

            end_timer("task_execution")

            continue

        # ==================================================
        # OUTPUT
        # ==================================================

        log_section("OUTPUT")

        try:

            start_timer("output_rendering")

            print("\nSUMMARY:")

            print(
                result.get(
                    "summary",
                    ""
                )
            )

            data = result.get(
                "data",
                {}
            )

            if data:

                print("\nDATA:")

                print(data)

            if "drivers" in result:

                print("\nDRIVERS:")

                for d in result["drivers"]:

                    print("-", d)

            print("\nINTERPRETATION:")

            print(
                result.get(
                    "interpretation",
                    ""
                )
            )

            print("\n---------------------------\n")

            end_timer("output_rendering")

        except Exception as e:

            log_error(
                "OUTPUT",
                e
            )

            end_timer("output_rendering")

            continue

        # ==================================================
        # TOTAL REQUEST END
        # ==================================================

        end_timer("total_request")


# ======================================================
# ENTRY POINT
# ======================================================

if __name__ == "__main__":

    run()