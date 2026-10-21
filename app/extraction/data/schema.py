from typing import List, Literal, Optional
from pydantic import BaseModel, Field


CatalogIntent = Literal[
    "dataset_inventory",
    "stressor_variables",
    "harmful_forces",
    "fragile_conditions",
    "anthropogenic_pressures",
    "climate_drivers",
    "ecological_indicators",
    "ecosystem_functioning",
    "ecological_dynamics",
]


class DataExtraction(BaseModel):
    intent: Literal["data_query"]

    # Empty only when the deterministic catalog classifier has identified a
    # catalog intent. The bridge enforces that at least one of the two paths
    # (variables or catalog_intent) is populated.
    variables: List[str] = Field(
        default_factory=list,
        description="Dataset variables explicitly requested by the user, if any."
    )

    catalog_intent: Optional[CatalogIntent] = Field(
        default=None,
        description="Recognized semantic catalog category, when the query asks for one."
    )
