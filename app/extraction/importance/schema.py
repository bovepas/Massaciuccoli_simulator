from typing import Literal

from pydantic import BaseModel, Field


class ImportanceExtraction(BaseModel):
    intent: Literal["importance_query"]

    top_k: int = Field(
        default=5,
        ge=1,
        description="Number of top factors requested by the user.",
    )

    focus: Literal["all", "climate", "biodiversity", "land_use"] = Field(
        default="all",
        description=(
            "Environmental-variable subset requested by the user: "
            "all, climate, biodiversity, or land_use."
        ),
    )

    direction: Literal["all", "increase", "decrease"] = Field(
        default="all",
        description=(
            "Requested direction of association with ecosystem risk: "
            "all, increase, or decrease."
        ),
    )
