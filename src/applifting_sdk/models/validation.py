from pydantic import BaseModel, Field
from typing import List, Union


class ValidationError(BaseModel):
    """Single validation error."""

    loc: List[Union[str, int]] = Field(..., description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Type of the error")


class HTTPValidationError(BaseModel):
    """Validation errors wrapper."""

    detail: List[ValidationError] = Field(default_factory=list)
