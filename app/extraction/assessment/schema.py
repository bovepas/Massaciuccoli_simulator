from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ======================================================
# MODIFICATION
# ======================================================

class AssessmentModification(BaseModel):
    """
    Semantic representation of a single modification
    requested by the user.

    The LLM extracts what the user means.
    Python is responsible for validation and application
    to the actual dataset.
    """

    variable: str

    original_expression: str

    interpretation: str

    modification_type: Literal[
        "delta",
        "percentage",
        "target",
        "range",
        "qualitative",
        "state_change",
    ]

    # --------------------------------------------------
    # Quantitative modifications
    # --------------------------------------------------

    value: Optional[float] = None

    unit: Optional[Literal[
        "percent",
        "degC",
        "days",
        "count",
        "unknown",
    ]] = None

    # --------------------------------------------------
    # Range / state transition
    # --------------------------------------------------

    from_value: Optional[float] = None

    to_value: Optional[float] = None

    # --------------------------------------------------
    # Qualitative modification
    # --------------------------------------------------

    direction: Optional[Literal[
        "increase",
        "decrease",
        "change",
    ]] = None

    magnitude: Optional[str] = None

    # --------------------------------------------------
    # Optional confidence
    # --------------------------------------------------

    confidence: Optional[float] = None


# ======================================================
# EXTRACTION
# ======================================================

class AssessmentExtraction(BaseModel):
    """
    Complete semantic extraction of an Assessment question.
    """

    intent: Literal[
        "scenario_simulation",
        "dataset_inventory",
    ]

    target: Literal[
        "ecosystem_risk",
        "dataset_variables",
    ]

    scenario: List[AssessmentModification] = Field(
        default_factory=list
    )