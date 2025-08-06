from pydantic import BaseModel
from uuid import UUID

class OfferResponse(BaseModel):
    id: UUID
    price: int
    items_in_stock: int