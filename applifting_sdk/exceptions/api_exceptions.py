from typing import Any, Optional


class AppliftingSDKError(Exception):
    """Base exception for the SDK."""


class AppliftingSDKNetworkError(AppliftingSDKError):
    """Network connectivity error (DNS, connection refused, etc.)."""


class AppliftingSDKTimeoutError(AppliftingSDKError):
    """Request timed out."""


class APIError(AppliftingSDKError):
    """Generic non-success HTTP response from the API."""

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        code: Optional[str] = None,
        details: Any = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(f"{status_code} {message}")
        self.status_code = status_code
        self.message = message
        self.code = code
        self.details = details
        self.response_text = response_text


class BadRequestError(APIError):
    """400 BadRequest."""


class AuthenticationError(APIError):
    """401 Unauthorized."""


class PermissionDenied(APIError):
    """403 Forbidden."""


class NotFoundError(APIError):
    """404 Not Found."""


class ConflictError(APIError):
    """409 Conflict (e.g., product already exists)."""


class ValidationFailed(APIError):
    """422 Unprocessable Entity (validation errors)."""


class RateLimitError(APIError):
    """429 Too Many Requests."""


class ServerError(APIError):
    """5xx responses."""
