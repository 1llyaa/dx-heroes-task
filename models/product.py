from pydantic import BaseModel
from uuid import UUID

class RegisterProductRequest(BaseModel):
    id: UUID
    name: str
    description: str

class RegisterProductResponse(BaseModel):
    id: UUID
