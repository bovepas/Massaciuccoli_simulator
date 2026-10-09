from typing import Literal, Optional
from pydantic import BaseModel


class ImportanceCompareExtraction(BaseModel):
    intent: Literal["importance_compare_query"]
    entity_a: str
    entity_b: Optional[str] = None