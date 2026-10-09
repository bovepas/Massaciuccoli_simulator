from typing import Literal
from pydantic import BaseModel, Field


class ImportanceExtraction(BaseModel):
    intent: Literal["importance_query"]
    top_k: int = Field(
        default=5,
        ge=1,
        description="Number of top factors requested by the user."
    )
    focus: Literal["increase", "decrease", "all"] = Field(
        default="all",
        description="Whether the user wants factors increasing risk, decreasing risk, or all factors."
    )