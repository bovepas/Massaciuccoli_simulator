from pathlib import Path


PROMPT_FILE = Path(__file__).with_name("risk_variation_extraction_v4.txt")


def load_delta_prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")