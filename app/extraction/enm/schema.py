from typing import Literal, Optional
from pydantic import BaseModel


class ENMExtraction(BaseModel):
    intent: Literal[
        "suitability_conditions",
        "influencing_variables",
        "future_suitability",
        "hypothetical_effect",
        "limiting_factor",
        "favorable_factor",
        "climate_influence",
        "distribution",
        "model_accuracy",
    ]

    target: str

    target_type: Literal[
        "species",
        "category",
    ]

    year: Optional[int] = None
    rcp: Optional[str] = None

    variable: Optional[str] = None
    variation: Optional[str] = None
    variation_type: Optional[Literal[
        "absolute",
        "percentage",
        "relative",
        "qualitative",
    ]] = None