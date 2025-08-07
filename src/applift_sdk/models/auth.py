from pydantic import BaseModel, Field

class AuthResponse(BaseModel):
    """Authentication response with access token."""
    access_token: str = Field(..., description="JWT access token")
