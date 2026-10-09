from pathlib import Path


PROMPT_FILE = Path(__file__).with_name("assessment_extraction.txt")


def load_assessment_prompt() -> str:
    """
    Load the semantic extraction prompt used by the Assessment extractor.
    """
    return PROMPT_FILE.read_text(encoding="utf-8")