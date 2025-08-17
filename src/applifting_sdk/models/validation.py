
from pydantic import BaseModel, Field


class ValidationError(BaseModel):
    """Single validation error."""

    loc: list[str | int] = Field(..., description="Location of the error")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Type of the error")


class HTTPValidationError(BaseModel):
    """Validation errors wrapper."""

    detail: list[ValidationError] = Field(default_factory=list)
