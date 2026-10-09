from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DeltaChange(BaseModel):
    """
    Represents the final deterministic change applied to a variable.

    The value is calculated by the extractor when an explicit
    range is present.
    """

    value: float
    unit: Literal["percent", "degC"]


class DeltaRange(BaseModel):
    """
    Represents an explicit from/to range extracted from the query.

    The endpoints are extracted semantically by the LLM.
    No arithmetic is performed here.
    """

    from_value: float
    to_value: float
    unit: Literal["percent", "degC"]


class DeltaVariable(BaseModel):
    """
    Structured representation of one variable involved in
    a delta scenario.
    """

    variable: str
    original_expression: str
    interpretation: str
    confidence: Optional[float] = None
    change_type: Literal["delta", "absolute_target"]
    change: DeltaChange
    range: Optional[DeltaRange] = None


class DeltaExtraction(BaseModel):
    """
    Complete structured representation of a delta request.
    """

    intent: Literal[
        "scenario_simulation",
        "dataset_inventory",
    ]

    target: Literal[
        "ecosystem_risk",
        "dataset_variables",
    ]

    scenario: List[DeltaVariable] = Field(
        default_factory=list
    )