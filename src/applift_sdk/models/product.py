from pydantic import BaseModel, Field
from uuid import UUID

class RegisterProductRequest(BaseModel):
    """Request to register a product."""
    id: UUID = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")


class RegisterProductResponse(BaseModel):
    """Response after registering a product."""
    id: UUID = Field(..., description="Product ID")
