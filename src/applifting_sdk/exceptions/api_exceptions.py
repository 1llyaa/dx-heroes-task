class AppliftSDKError(Exception):
    """Base exception for the SDK."""

class AuthenticationError(AppliftSDKError):
    """Raised when authentication fails."""

class NotFoundError(AppliftSDKError):
    """Raised when a resource is not found."""

class ConflictError(AppliftSDKError):
    """Raised when there is a conflict (e.g., product already exists)."""

class ValidationError(AppliftSDKError):
    """Raised when the API returns validation errors."""

class BadRequestError(AppliftSDKError):
    """Raised when there is bad request"""