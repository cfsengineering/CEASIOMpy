# Imports

from pydantic import BaseModel


# Classes
class Parameter(BaseModel):
    name: str
    min_value: float
    max_value: float
