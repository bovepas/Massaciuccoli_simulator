# -*- coding: utf-8 -*-
"""Batch benchmark runner for the historical v33 orchestrator.

Run from app root inside the container:
    python -m tests.test_orchestrator_v33_bm
    python -m tests.test_orchestrator_v33_bm --task dependency
    python -m tests.test_orchestrator_v33_bm --task all

This executes the task predicted by the v33 router (not the expected benchmark
label), and stores question, expected/predicted task, intermediate parsing,
result, errors and timing in a JSON file.
"""
import argparse
import ast
import json
import os
import sys
import time
from datetime import datetime

import pandas as pd

# Ensure app root is importable when run as a module or script.
APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

# Load only the benchmark data assignments from the benchmark source file.
# This avoids executing its imports (which target a newer router unavailable in v33).
def load_benchmark_data():
    benchmark_path = os.path.join(APP_ROOT, "tests", "test_router_bm_cosin_2.py")
    with open(benchmark_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=benchmark_path)
    extracted = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in {"TESTS", "SOURCE_INTENTS"}:
                    extracted[target.id] = ast.literal_eval(node.value)
    if "TESTS" not in extracted or "SOURCE_INTENTS" not in extracted:
        raise RuntimeError("Could not extract TESTS and SOURCE_INTENTS from benchmark file")
    return extracted["TESTS"], extracted["SOURCE_INTENTS"]

TESTS, SOURCE_INTENTS = load_benchmark_data()
from versions.v6_1_main import route_question
from versions.v6_1_emulator import load_and_train_emulator
from utils.feature_parser import parse_features
from utils.range_parser import parse_range
from utils.importance_parser import parse_top_k
from tasks.task_assessment import handle_assessment
from tasks.task_importance import handle_importance
from tasks.task_delta import handle_delta
from tasks.task_dependency import handle_dependency
from tasks.task_drivers import handle_drivers
from tasks.task_chat import handle_chat
from tasks.task_data import handle_data
from tasks.task_comparison import handle_comparison
from tasks.task_enm import handle_enm
from tasks.task_importance_compare import handle_importance_compare

DATA_PATH = os.path.join(APP_ROOT, "data", "massaciuccoli_data.csv")
OUTPUT_DIR = os.path.join(APP_ROOT, "tests", "benchmark_results")


def json_safe(value):
    """Convert common Python/numpy objects to JSON-compatible structures."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if hasattr(value, "item"):
        try:
            return json_safe(value.item())
        except Exception:
            pass
    if hasattr(value, "to_dict"):
        try:
            return json_safe(value.to_dict())
        except Exception:
            pass
    return repr(value)


def execute_task(task_type, question, route, parsed, features, range_info, model, dataset):
    if task_type == "assessment":
        return handle_assessment(question=question, features=features,
            qualitative_changes=parsed.get("qualitative_changes", []),
            dataset=dataset, model=model)
    if task_type == "importance":
        return handle_importance(question=question, features=features, model=model,
            dataset=dataset, top_k=parse_top_k(question))
    if task_type == "delta":
        return handle_delta(question, range_info, features, parsed, model)
    if task_type == "dependency":
        return handle_dependency(question, route)
    if task_type == "comparison":
        return handle_comparison(question, model, dataset)
    if task_type == "data":
        return handle_data(question, dataset=dataset)
    if task_type == "drivers":
        return handle_drivers(question)
    if task_type == "enm":
        return handle_enm(question)
    if task_type == "importance_compare":
        return handle_importance_compare(question=question, model=model, dataset=dataset)
    if task_type == "chat":
        return handle_chat(question)
    return {"summary": "Unknown task", "interpretation": f"Unknown routed task: {task_type}"}


def run(task_filter="all", limit=None):
    print("Loading dataset and emulator...")
    dataset = pd.read_csv(DATA_PATH, skiprows=[1])
    model = load_and_train_emulator(DATA_PATH)
    print("Resources loaded. Starting benchmark.\n")

    selected = [(i, q, expected) for i, (q, expected) in enumerate(TESTS, 1)
                if task_filter == "all" or expected == task_filter]
    if limit is not None:
        selected = selected[:limit]

    records = []
    overall_start = time.time()
    for ordinal, (benchmark_index, question, expected) in enumerate(selected, 1):
        print(f"[{ordinal}/{len(selected)}] ({benchmark_index}) {question}")
        record = {
            "benchmark_index": benchmark_index,
            "question": question,
            "source_intent": SOURCE_INTENTS[benchmark_index - 1],
            "expected_task": expected,
            "predicted_task": None,
            "route": None,
            "parsed": None,
            "features": None,
            "range_info": None,
            "result": None,
            "error_stage": None,
            "error": None,
            "timing_seconds": {},
        }
        try:
            t0 = time.time()
            route = route_question(question)
            record["timing_seconds"]["routing"] = round(time.time() - t0, 4)
            record["route"] = json_safe(route)
            task_type = route.get("type")
            record["predicted_task"] = task_type

            parsed = None
            features = None
            range_info = None
            if task_type in ["assessment", "importance", "delta"]:
                t0 = time.time()
                parsed = parse_features(question, return_metadata=True)
                features = parsed.get("features")
                range_info = parse_range(question)
                record["timing_seconds"]["parsing"] = round(time.time() - t0, 4)
                record["parsed"] = json_safe(parsed)
                record["features"] = json_safe(features)
                record["range_info"] = json_safe(range_info)

            t0 = time.time()
            result = execute_task(task_type, question, route, parsed, features,
                                 range_info, model, dataset)
            record["timing_seconds"]["task_execution"] = round(time.time() - t0, 4)
            record["result"] = json_safe(result)
        except Exception as exc:
            record["error_stage"] = record["error_stage"] or (
                "task_execution" if record["predicted_task"] else "routing_or_parsing")
            record["error"] = f"{type(exc).__name__}: {exc}"
            print(f"  ERROR: {record['error']}")
        record["routing_correct"] = record["predicted_task"] == expected
        records.append(record)

    elapsed = round(time.time() - overall_start, 3)
    correct = sum(r["routing_correct"] for r in records)
    summary = {
        "benchmark": "Massaciuccoli benchmark 2 - v33 orchestrator",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "task_filter": task_filter,
        "questions_selected": len(records),
        "routing_correct": correct,
        "routing_accuracy_percent": round(100 * correct / len(records), 2) if records else 0,
        "execution_errors": sum(r["error"] is not None for r in records),
        "elapsed_seconds": elapsed,
        "results": records,
    }
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = os.path.join(OUTPUT_DIR, f"orchestrator_v33_bm_{task_filter}_{stamp}.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\n================ SUMMARY ================")
    print(f"Questions: {len(records)}")
    print(f"Routing correct: {correct}/{len(records)} ({summary['routing_accuracy_percent']}%)")
    print(f"Execution errors: {summary['execution_errors']}")
    print(f"Elapsed: {elapsed}s")
    print(f"JSON saved: {outfile}")
    print("======================================")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the 110-question v33 orchestrator benchmark")
    parser.add_argument("--task", default="all", help="Expected task filter or 'all'")
    parser.add_argument("--limit", type=int, default=None, help="Optional limit on selected questions")
    args = parser.parse_args()
    valid_tasks = {task for _, task in TESTS} | {"all"}
    if args.task not in valid_tasks:
        parser.error(f"Unknown task '{args.task}'. Valid values: {sorted(valid_tasks)}")
    run(args.task, args.limit)
