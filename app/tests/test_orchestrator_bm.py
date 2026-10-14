# -*- coding: utf-8 -*-
"""End-to-end benchmark using tests.test_router_bm_cosin as the canonical question set.

Run inside the app container from the project root:
    python -m tests.test_orchestrator_bm

Writes tests/orchestrator_bm_results.json. Does not modify the production router
or orchestrator. The per-question pipeline mirrors v6_1_orchestrator.run().
"""

import contextlib
import io
import json
import os
import traceback
from datetime import datetime

from tests.test_router_bm_cosin import TESTS
from versions import v6_1_orchestrator as orch
from utils.model_input_builder import compute_feature_statistics


FAILURE_SUMMARIES = {
    "Assessment unavailable", "Model not available", "Comparison unavailable",
    "Comparison not recognized", "Range not recognized", "Feature not recognized",
    "Invalid scenario", "Drivers not computable", "Data not available",
    "ENM analysis failed", "Unknown task",
}
FAILURE_PREFIXES = (
    "Could not parse", "Could not identify", "Could not determine",
    "The model or dataset is missing", "Dataset not loaded",
    "Target variable not found",
)


def process_question(question, model, dataset, route):
    """Mirror extraction/bridge -> task handler after routing has been recorded."""
    task_type = route.get("type")

    parsed = features = range_info = None
    comparison_inputs = data_inputs = dependency_inputs = None
    drivers_inputs = importance_inputs = importance_compare_inputs = enm_inputs = None

    if task_type == "assessment":
        extraction = orch.extract_assessment(question)
        inputs = orch.assessment_extraction_to_inputs(extraction)
        parsed, features = inputs, inputs["features"]
    elif task_type == "importance":
        extraction = orch.extract_importance(question)
        importance_inputs = orch.importance_extraction_to_inputs(extraction)
        parsed = extraction
    elif task_type == "delta":
        extraction = orch.extract_delta(question)
        range_info = orch._delta_extraction_to_range_info(extraction)
    
    elif task_type == "comparison":
        extraction = orch.extract_comparison(question)

        feature_stats = compute_feature_statistics(dataset)

        comparison_inputs = orch.comparison_extraction_to_inputs(
            extraction,
            feature_stats=feature_stats,
        )
        parsed = extraction

    elif task_type == "data":
        extraction = orch.extract_data(question)
        data_inputs = orch.data_extraction_to_inputs(extraction)
        parsed = extraction
    elif task_type == "dependency":
        extraction = orch.extract_dependency(question)
        dependency_inputs = orch.dependency_extraction_to_inputs(extraction)
        parsed = extraction
    elif task_type == "drivers":
        extraction = orch.extract_drivers(question)
        drivers_inputs = orch.drivers_extraction_to_inputs(extraction)
        parsed = extraction
    elif task_type == "importance_compare":
        extraction = orch.extract_importance_compare(question)
        importance_compare_inputs = orch.importance_compare_extraction_to_inputs(extraction)
        parsed = extraction
    elif task_type == "enm":
        extraction = orch.extract_enm(question)
        enm_inputs = orch.enm_extraction_to_inputs(extraction)
        parsed = extraction

    # Execute the same category handler and pass the same bridge outputs as run().
    if task_type == "assessment":
        result = orch.handle_assessment(
            question=question, features=features,
            qualitative_changes=parsed.get("qualitative_changes", []),
            dataset=dataset, model=model,
        )
    elif task_type == "importance":
        result = orch.handle_importance(
            question=question, features=None, model=model, dataset=dataset,
            top_k=importance_inputs["top_k"], mode=importance_inputs["focus"],
        )
    elif task_type == "delta":
        result = orch.handle_delta(question, range_info, features, parsed, model)
    elif task_type == "dependency":
        result = orch.handle_dependency(question, route, dependency_inputs=dependency_inputs)
    elif task_type == "comparison":
        result = orch.handle_comparison(
            question, model, dataset, comparison_inputs=comparison_inputs
        )
    elif task_type == "data":
        result = orch.handle_data(question, dataset=dataset, data_inputs=data_inputs)
    elif task_type == "drivers":
        result = orch.handle_drivers(question, drivers_inputs=drivers_inputs)
    elif task_type == "enm":
        result = orch.handle_enm(question, enm_inputs=enm_inputs)
    elif task_type == "importance_compare":
        result = orch.handle_importance_compare(
            question=question, model=model, dataset=dataset,
            importance_compare_inputs=importance_compare_inputs,
        )
    elif task_type == "chat":
        result = orch.handle_chat(question)
    else:
        result = {
            "summary": "Unknown task", "data": {}, "drivers": [],
            "interpretation": f"Could not determine the task type: {task_type}",
        }

    return task_type, result


def classify_result(result):
    if not isinstance(result, dict):
        return "invalid_result"
    summary = str(result.get("summary", "")).strip()
    interpretation = str(result.get("interpretation", "")).strip()
    if summary in FAILURE_SUMMARIES:
        return "application_failure"
    if any(interpretation.startswith(prefix) for prefix in FAILURE_PREFIXES):
        return "application_failure"
    if not summary and not interpretation and not result.get("data"):
        return "empty_result"
    return "response_returned"


def main():
    print("=" * 72)
    print("ORCHESTRATOR END-TO-END BENCHMARK")
    print(f"Canonical question set: tests.test_router_bm_cosin ({len(TESTS)} questions)")
    print("Loading model and dataset once...")
    model, dataset = orch.load_resources()
    if model is None or dataset is None:
        raise SystemExit("FATAL: model/dataset loading failed; benchmark aborted.")

    records = []
    counts = {
        "route_correct": 0, "route_wrong": 0, "response_returned": 0,
        "application_failure": 0, "empty_result": 0, "invalid_result": 0,
        "execution_exception": 0,
    }

    for index, (question, expected_type) in enumerate(TESTS, 1):
        print(f"\n[{index:02d}/{len(TESTS)}] {question}")
        captured = io.StringIO()
        record = {
            "index": index, "question": question, "expected_type": expected_type,
            "predicted_type": None, "route_correct": False, "status": None,
            "summary": "", "interpretation": "", "data": None, "drivers": None,
            "error": None,
        }
        try:
            # Count routing independently, before extraction/execution can fail.
            with contextlib.redirect_stdout(captured):
                route = orch.route_question(question)
            predicted_type = route.get("type")
            record["predicted_type"] = predicted_type
            record["route_correct"] = predicted_type == expected_type
            counts["route_correct" if record["route_correct"] else "route_wrong"] += 1

            with contextlib.redirect_stdout(captured):
                _, result = process_question(question, model, dataset, route)
            record["summary"] = str(result.get("summary", "")) if isinstance(result, dict) else ""
            record["interpretation"] = (
                str(result.get("interpretation", "")) if isinstance(result, dict) else ""
            )
            record["data"] = result.get("data") if isinstance(result, dict) else None
            record["drivers"] = result.get("drivers") if isinstance(result, dict) else None
            record["status"] = classify_result(result)
            counts[record["status"]] += 1
            print(
                f"  route={predicted_type} (expected={expected_type}) | "
                f"status={record['status']} | {record['summary']}"
            )
            if record["status"] != "response_returned":
                print(f"  interpretation: {record['interpretation'][:300]}")
        except Exception as exc:
            record["status"] = "execution_exception"
            record["error"] = f"{type(exc).__name__}: {exc}"
            counts["execution_exception"] += 1
            print(f"  EXCEPTION: {record['error']}")
            print(traceback.format_exc(limit=2))
            diagnostic = captured.getvalue()
            if diagnostic:
                print("  Last captured diagnostics:")
                print("\n".join(diagnostic.splitlines()[-8:]))

        records.append(record)

    report = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "benchmark_module": "tests.test_router_bm_cosin",
        "total_questions": len(TESTS),
        "counts": counts,
        "results": records,
    }
    output_path = os.path.join(os.path.dirname(__file__), "orchestrator_bm_results.json")
    with open(output_path, "w", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, default=str)

    print("\n" + "=" * 72)
    print("SUMMARY")
    print(f"Questions:          {len(TESTS)}")
    print(f"Routing correct:    {counts['route_correct']}/{len(TESTS)}")
    print(f"Responses returned: {counts['response_returned']}")
    print(f"Application errors: {counts['application_failure']}")
    print(f"Empty/invalid:      {counts['empty_result'] + counts['invalid_result']}")
    print(f"Exceptions:         {counts['execution_exception']}")
    print(f"JSON report:        {output_path}")
    print("A returned response is not, by itself, proof of scientific correctness.")
    print("=" * 72)


if __name__ == "__main__":
    main()
