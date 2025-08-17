from uuid import UUID

from pydantic import BaseModel, Field


class OfferResponse(BaseModel):
    """Single offer response."""

    id: UUID = Field(..., description="Offer ID")
    price: int = Field(..., description="Price in cents")
    items_in_stock: int = Field(..., description="Items in stock")
