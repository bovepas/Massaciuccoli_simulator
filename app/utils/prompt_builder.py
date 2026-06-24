# -*- coding: utf-8 -*-

"""
Prompt Builder

Composes prompts from modular components:

    base
  + model
  + style
  + task

A legacy mode is also available to preserve
backward compatibility during migration.
"""

from pathlib import Path

from config.llm_profiles import (
    LLM_PROFILE,
    LLM_STYLE
)


# ======================================================
# CONFIG
# ======================================================

PROMPT_ROOT = Path("prompts")

USE_LEGACY_PROMPTS = False
DEBUG_PROMPTS = True

# ======================================================
# LOAD FILE
# ======================================================

def load_prompt_file(path: Path):

    if not path.exists():

        raise FileNotFoundError(path)

    return path.read_text(
        encoding="utf-8"
    ).strip()


# ======================================================
# LOAD COMPONENTS
# ======================================================

def load_base_prompt():

    return load_prompt_file(
        PROMPT_ROOT /
        "models" /
        "base.txt"
    )


def load_model_prompt():

    filename = f"{LLM_PROFILE}.txt"

    return load_prompt_file(

        PROMPT_ROOT /
        "models" /
        filename
    )


def load_style_prompt():

    filename = f"{LLM_STYLE}.txt"

    return load_prompt_file(

        PROMPT_ROOT /
        "styles" /
        filename
    )


def load_task_prompt(task):

    filename = f"{task}.txt"

    return load_prompt_file(

        PROMPT_ROOT /
        "tasks" /
        filename
    )


# ======================================================
# BUILD PROMPT
# ======================================================

def build_prompt(task):

    parts = [

        load_base_prompt(),

        load_model_prompt(),

        load_style_prompt(),

        load_task_prompt(task)
    ]
    if DEBUG_PROMPTS:

        print("\n========== COMPOSED PROMPT ==========\n")

        print("[BASE]\n")
        print(parts[0])

        print("\n[MODEL]\n")
        print(parts[1])

        print("\n[STYLE]\n")
        print(parts[2])

        print("\n[TASK]\n")
        print(parts[3])

        print("\n=====================================\n")

    return "\n\n".join(parts)