from typing import Literal
from pydantic import BaseModel


class DriversExtraction(BaseModel):
    intent: Literal["drivers_query"]
    target: str
    direction: Literal["increase", "decrease", "unspecified"]