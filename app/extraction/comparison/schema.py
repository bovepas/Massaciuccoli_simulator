from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ComparisonModification(BaseModel):
    """
    Semantic description of one modification inside a comparison scenario.

    The extractor identifies what the user means.
    Numeric interpretation and model application are handled downstream.
    """

    variable: str

    original_expression: str

    interpretation: str

    modification_type: Literal[
        "delta",
        "percentage",
        "target",
        "qualitative",
        "state_change",
    ]

    value: Optional[float] = None

    unit: Optional[Literal[
        "percent",
        "degC",
        "days",
        "count",
        "unknown",
    ]] = None

    
    @field_validator("unit", mode="before")
    @classmethod
    def normalize_unit(cls, value):
        if not isinstance(value, str):
            return value

        normalized = {
            "%": "percent",
            "percentage": "percent",
            "°C": "degC",
            "°c": "degC",
            "celsius": "degC",
        }

        return normalized.get(value.strip(), value.strip())

    from_value: Optional[float] = None

    to_value: Optional[float] = None

    direction: Optional[Literal[
        "increase",
        "decrease",
        "change",
    ]] = None

    magnitude: Optional[str] = None

    confidence: Optional[float] = None


class ComparisonExtraction(BaseModel):
    """
    Complete semantic extraction of a comparison request.

    A comparison always contains two distinct scenarios.
    Each scenario may contain one or more modifications.
    """

    intent: Literal[
        "scenario_comparison",
    ]

    target: Literal[
        "ecosystem_risk",
        "ecosystem_resilience",
        "ecosystem_health",
    ]

    scenario_a: List[ComparisonModification] = Field(
        ...,
        min_length=1,
    )

    scenario_b: List[ComparisonModification] = Field(
        ...,
        min_length=1,
    )