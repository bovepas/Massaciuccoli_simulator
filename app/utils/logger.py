# -*- coding: utf-8 -*-

import datetime
import time


# ======================================================
# INTERNAL TIMER STORAGE
# ======================================================

_TIMERS = {}


# ======================================================
# TIME
# ======================================================

def _now():

    return datetime.datetime.utcnow().strftime(
        "%Y-%m-%d %H:%M:%S"
    )


# ======================================================
# BASE LOGS
# ======================================================

def log_section(title: str):

    print(f"\n========== {title.upper()} ==========")


def log_question(question: str):

    print(f"[{_now()}] QUESTION: {question}")


def log_route(decision: str):

    print(f"[{_now()}] ROUTER → {decision}")


def log_data(label: str, data):

    print(f"    {label}: {data}")


def log_error(step: str, error: Exception):

    print(
        f"[{_now()}] "
        f"[ERROR] "
        f"[{step}] "
        f"{str(error)}"
    )


# ======================================================
# 🔥 TIMING LOGS
# ======================================================

def start_timer(name: str):

    _TIMERS[name] = time.perf_counter()


def end_timer(name: str):

    if name not in _TIMERS:
        return

    elapsed = time.perf_counter() - _TIMERS[name]

    print(
        f"[{_now()}] "
        f"[TIMING] "
        f"{name}: "
        f"{elapsed:.2f}s"
    )

    del _TIMERS[name]


# ======================================================
# 🔥 KB LOGS
# ======================================================

def log_kb_status(status: str):

    print(f"[{_now()}] [KB] {status}")


def log_ingestion_triggered():

    print(
        f"[{_now()}] "
        f"[KB] "
        f"Knowledge base empty → running ingestion..."
    )


def log_ingestion_skipped():

    print(
        f"[{_now()}] "
        f"[KB] "
        f"Knowledge base already populated"
    )


# ======================================================
# 🔥 RAG LOGS
# ======================================================

def log_retrieval(count: int):

    print(
        f"[{_now()}] "
        f"[RAG] "
        f"Retrieved documents: {count}"
    )


def log_fallback(reason: str):

    print(
        f"[{_now()}] "
        f"[RAG] "
        f"FALLBACK → {reason}"
    )


def log_llm_failure():

    print(
        f"[{_now()}] "
        f"[RAG] "
        f"LLM output rejected "
        f"(invalid or hallucinated)"
    )


# ======================================================
# OPTIONAL DEBUG FLAG
# ======================================================

DEBUG = True


def debug(*args):

    if DEBUG:
        print("[DEBUG]", *args)