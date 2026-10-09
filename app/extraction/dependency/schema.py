from typing import Literal
from pydantic import BaseModel


class DependencyExtraction(BaseModel):
    intent: Literal["dependency_query"]

    driver: str
    target: str