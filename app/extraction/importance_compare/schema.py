from typing import Literal, Optional
from pydantic import BaseModel


Direction = Literal[
    "increase",
    "decrease",
    "unspecified"
]


class ImportanceCompareExtraction(BaseModel):

    intent: Literal["importance_compare_query"]

    entity_a: str
    direction_a: Direction = "unspecified"

    entity_b: Optional[str] = None
    direction_b: Direction = "unspecified"