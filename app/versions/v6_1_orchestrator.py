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

#from versions.v6_1_main import route_question
from router.semantic_router import route_question

# ======================================================
# PARSERS
# ======================================================

from utils.feature_parser import parse_features

from utils.range_parser import parse_range

from extraction.delta.extractor import extract_delta
from extraction.assessment.extractor import extract_assessment
from extraction.assessment.bridge import assessment_extraction_to_inputs
from extraction.comparison.extractor import extract_comparison
from extraction.comparison.bridge import comparison_extraction_to_inputs
from extraction.data.extractor import extract_data
from extraction.data.bridge import data_extraction_to_inputs
from extraction.dependency.extractor import extract_dependency
from extraction.dependency.bridge import dependency_extraction_to_inputs
from utils.feature_mapping import normalize_feature_name
from extraction.drivers.extractor import extract_drivers
from extraction.drivers.bridge import drivers_extraction_to_inputs
from extraction.importance.extractor import extract_importance
from extraction.importance.bridge import importance_extraction_to_inputs
from extraction.importance_compare.extractor import extract_importance_compare
from extraction.enm.extractor import extract_enm
from extraction.enm.bridge import enm_extraction_to_inputs
from extraction.importance_compare.bridge import importance_compare_extraction_to_inputs

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
# DELTA EXTRACTION → LEGACY RANGE INFO
# ======================================================

def _delta_extraction_to_range_info(extraction):
    """
    Convert the new DeltaExtraction result into the
    range_info structure expected by handle_delta().

    - Explicit range:
        preserves the original from/to values.

    - Implicit delta:
        converts the extracted change into the
        baseline_delta structure already supported
        by handle_delta().

    The semantic variable name returned by the LLM
    is normalized to the actual dataset feature name.
    """

    if not extraction:
        return None

    if not extraction.scenario:
        return None

    scenario = extraction.scenario[0]

    # --------------------------------------------------
    # Normalize semantic variable name
    # --------------------------------------------------

    feature = normalize_feature_name(
        scenario.variable
    )

    if not feature:
        return None

    # --------------------------------------------------
    # Explicit range
    # --------------------------------------------------

    if scenario.range is not None:

        return {
            "feature": feature,
            "from": scenario.range.from_value,
            "to": scenario.range.to_value,
        }

    # --------------------------------------------------
    # Implicit delta / absolute target
    # --------------------------------------------------

    if scenario.change is not None:

        if scenario.change_type == "absolute_target":

            return {
                "feature": feature,
                "mode": "baseline_delta",
                "delta": scenario.change.value,
                "delta_type": "absolute_target",
            }

        return {
            "feature": feature,
            "mode": "baseline_delta",
            "delta": scenario.change.value,
            "delta_type": "absolute_delta",
        }

    return None

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
        comparison_inputs = None
        data_inputs = None
        dependency_inputs = None
        drivers_inputs = None
        importance_inputs = None
        importance_compare_inputs = None
        enm_inputs = None
        try:

            start_timer("parsing")

            if task_type == "assessment":

                log_section("PARSING")

                assessment_extraction = extract_assessment(
                    question
                )

                assessment_inputs = assessment_extraction_to_inputs(
                    assessment_extraction
                )

                parsed = assessment_inputs
                features = assessment_inputs["features"]

                log_data(
                    "assessment_extraction",
                    assessment_extraction
                )

                log_data(
                    "features",
                    features
                )

                log_data(
                    "qualitative_changes",
                    assessment_inputs["qualitative_changes"]
                )


            elif task_type == "importance":

                log_section("PARSING")

                importance_extraction = extract_importance(
                    question
                )

                importance_inputs = importance_extraction_to_inputs(
                    importance_extraction
                )

                parsed = importance_extraction
                features = None
                range_info = None

                log_data(
                    "importance_extraction",
                    importance_extraction
                )

                log_data(
                    "importance_inputs",
                    importance_inputs
                )


            elif task_type == "delta":

                log_section("PARSING")

                delta_extraction = extract_delta(
                    question
                )

                range_info = _delta_extraction_to_range_info(
                    delta_extraction
                )

                # Temporary compatibility layer for handle_delta().
                # The old parser remains untouched.
                parsed = None
                features = None

                log_data(
                    "delta_extraction",
                    delta_extraction
                )

                log_data(
                    "range",
                    range_info
                )
            elif task_type == "comparison":

                log_section("PARSING")

                comparison_extraction = extract_comparison(
                    question
                )

                comparison_inputs = comparison_extraction_to_inputs(
                    comparison_extraction
                )

                parsed = comparison_extraction
                features = None

                log_data(
                    "comparison_extraction",
                    comparison_extraction
                )

                log_data(
                    "comparison_inputs",
                    comparison_inputs
                )
            elif task_type == "data":

                log_section("PARSING")

                data_extraction = extract_data(
                    question
                )

                data_inputs = data_extraction_to_inputs(
                    data_extraction
                )

                parsed = data_extraction
                features = None

                log_data(
                    "data_extraction",
                    data_extraction
                )

                log_data(
                    "data_inputs",
                    data_inputs
                )
            elif task_type == "dependency":

                log_section("PARSING")

                dependency_extraction = extract_dependency(
                    question
                )

                dependency_inputs = (
                    dependency_extraction_to_inputs(
                        dependency_extraction
                    )
                )

                parsed = dependency_extraction
                features = None

                log_data(
                    "dependency_extraction",
                    dependency_extraction
                )

                log_data(
                    "dependency_inputs",
                    dependency_inputs
                )
            elif task_type == "drivers":
                log_section("PARSING")
                drivers_extraction = extract_drivers(question)
                drivers_inputs = drivers_extraction_to_inputs(
                    drivers_extraction
                )
                parsed = drivers_extraction
                features = None
                log_data("drivers_extraction", drivers_extraction)
                log_data("drivers_inputs", drivers_inputs)

            elif task_type == "importance_compare":

                extraction = extract_importance_compare(
                    question
                )

                importance_compare_inputs = (
                    importance_compare_extraction_to_inputs(
                        extraction
                    )
                )
            
            
            elif task_type == "enm":

                log_section("PARSING")

                enm_extraction = extract_enm(
                    question
                )

                enm_inputs = enm_extraction_to_inputs(
                    enm_extraction
                )

                parsed = enm_extraction
                features = None

                log_data(
                    "enm_extraction",
                    enm_extraction
                )

                log_data(
                    "enm_inputs",
                    enm_inputs
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

                    top_k=importance_inputs["top_k"],

                    mode=importance_inputs["focus"]
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
                    route,
                    dependency_inputs=dependency_inputs
                )

            # --------------------------------------------------
            # COMPARISON
            # --------------------------------------------------

            elif task_type == "comparison":

                result = handle_comparison(

                    question,

                    model,

                    dataset,
        
                    comparison_inputs=comparison_inputs
                )

            # --------------------------------------------------
            # DATA
            # --------------------------------------------------

            elif task_type == "data":

                result = handle_data(

                    question,

                    dataset=dataset,
                    data_inputs=data_inputs
                )

            # --------------------------------------------------
            # DRIVERS
            # --------------------------------------------------

            elif task_type == "drivers":

                result = handle_drivers(
                    question,
                    drivers_inputs=drivers_inputs
                )
            # --------------------------------------------------
            # ENM
            # --------------------------------------------------

            elif task_type == "enm":

                result = handle_enm(
                    question,
                    enm_inputs=enm_inputs
                )
            # --------------------------------------------------
            # IMPORTANCE COMPARE
            # --------------------------------------------------

            elif task_type == "importance_compare":

                result = handle_importance_compare(

                    question=question,

                    model=model,

                    dataset=dataset,

                    importance_compare_inputs=importance_compare_inputs
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