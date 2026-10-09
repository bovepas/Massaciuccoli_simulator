from typing import List, Literal
from pydantic import BaseModel, Field


class DataExtraction(BaseModel):
    intent: Literal["data_query"]

    variables: List[str] = Field(
        ...,
        min_length=1,
        description="Variables whose current value is requested by the user."
    )