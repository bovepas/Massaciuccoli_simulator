# -*- coding: utf-8 -*-

import datetime


# ======================================================
# TIME
# ======================================================

def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


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
    print(f"[{_now()}] [ERROR] [{step}] {str(error)}")


# ======================================================
# 🔥 NEW: KB LOGS
# ======================================================

def log_kb_status(status: str):
    print(f"[{_now()}] [KB] {status}")


def log_ingestion_triggered():
    print(f"[{_now()}] [KB] Knowledge base empty → running ingestion...")


def log_ingestion_skipped():
    print(f"[{_now()}] [KB] Knowledge base already populated")


# ======================================================
# 🔥 NEW: RAG LOGS
# ======================================================

def log_retrieval(count: int):
    print(f"[{_now()}] [RAG] Retrieved documents: {count}")


def log_fallback(reason: str):
    print(f"[{_now()}] [RAG] FALLBACK → {reason}")


def log_llm_failure():
    print(f"[{_now()}] [RAG] LLM output rejected (invalid or hallucinated)")


# ======================================================
# 🔥 OPTIONAL: DEBUG FLAG
# ======================================================

DEBUG = True

def debug(*args):
    if DEBUG:
        print("[DEBUG]", *args)