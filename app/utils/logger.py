import datetime


def _now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


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