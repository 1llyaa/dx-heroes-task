from __future__ import annotations
from typing import Any, Optional, Tuple, Dict, Callable
import httpx
from applifting_sdk.exceptions import (
    APIError, AuthenticationError, PermissionDenied, NotFoundError,
    ConflictError, ValidationFailed, RateLimitError, ServerError,
)
from applifting_sdk.models import HTTPValidationError


class ErrorHandler:
    """Handles HTTP error response parsing and exception raising."""

    def __init__(self):
        """Initialize error handler with default status code mappings."""
        self._status_mappings: Dict[int, Callable[[int, Optional[dict], Optional[str]], Exception]] = {
            401: self._create_auth_error,
            403: self._create_permission_error,
            404: self._create_not_found_error,
            409: self._create_conflict_error,
            422: self._create_validation_error,
            429: self._create_rate_limit_error,
        }

    def parse_error_content(self, resp: httpx.Response) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
        """
        Parse error response content, prioritizing JSON payload over text.

        Args:
            resp: HTTP response object

        Returns:
            Tuple of (json_payload, text_content)
        """
        content_type = resp.headers.get("content-type", "")

        # Try JSON first if content type suggests it
        payload = None
        if self._is_json_content_type(content_type):
            payload = self._extract_json_payload(resp)

        # Fallback to text if no JSON payload
        text = None
        if payload is None:
            text = self._extract_text_content(resp)

        return payload, text

    def raise_api_error(self, resp: httpx.Response) -> None:
        """
        Parse response and raise appropriate API exception.

        Args:
            resp: HTTP response object

        Raises:
            APIError: Or one of its subclasses based on status code
        """
        status = resp.status_code
        payload, text = self.parse_error_content(resp)

        # Check for specific status code mappings
        if status in self._status_mappings:
            error_creator = self._status_mappings[status]
            raise error_creator(status, payload, text)

        # Handle server errors (5xx)
        if 500 <= status < 600:
            raise ServerError(status, "Server error", details=payload, response_text=text)

        # Default fallback
        raise APIError(status, "Unexpected API error", details=payload, response_text=text)

    def add_status_mapping(self, status_code: int, error_creator: Callable[[int, Optional[dict], Optional[str]], Exception]) -> None:
        """
        Add custom status code mapping.

        Args:
            status_code: HTTP status code
            error_creator: Function that creates the exception
        """
        self._status_mappings[status_code] = error_creator

    def _extract_json_payload(self, resp: httpx.Response) -> Optional[dict[str, Any]]:
        """Extract JSON payload from response if valid JSON dict."""
        try:
            obj = resp.json()
            if isinstance(obj, dict):
                return obj
            return None
        except Exception:
            return None

    def _extract_text_content(self, resp: httpx.Response) -> Optional[str]:
        """Extract text content from response."""
        try:
            return resp.text
        except Exception:
            return None

    def _is_json_content_type(self, content_type: str) -> bool:
        """Check if content type indicates JSON."""
        return "application/json" in content_type.lower()

    # Error creator methods
    def _create_auth_error(self, status: int, payload: Optional[dict], text: Optional[str]) -> AuthenticationError:
        return AuthenticationError(status, "Unauthorized", details=payload, response_text=text)

    def _create_permission_error(self, status: int, payload: Optional[dict], text: Optional[str]) -> PermissionDenied:
        return PermissionDenied(status, "Forbidden", details=payload, response_text=text)

    def _create_not_found_error(self, status: int, payload: Optional[dict], text: Optional[str]) -> NotFoundError:
        return NotFoundError(status, "Not Found", details=payload, response_text=text)

    def _create_conflict_error(self, status: int, payload: Optional[dict], text: Optional[str]) -> ConflictError:
        return ConflictError(status, "Conflict", details=payload, response_text=text)

    def _create_validation_error(self, status: int, payload: Optional[dict], text: Optional[str]) -> ValidationFailed:
        details: Optional[HTTPValidationError] = None
        if isinstance(payload, dict):
            try:
                details = HTTPValidationError(**payload)
            except Exception:
                pass
        return ValidationFailed(status, "Validation failed", details=details, response_text=text)

    def _create_rate_limit_error(self, status: int, payload: Optional[dict], text: Optional[str]) -> RateLimitError:
        return RateLimitError(status, "Too Many Requests", details=payload, response_text=text)


# Default instance for backwards compatibility
default_error_handler = ErrorHandler()

# Convenience functions that use the default handler
def parse_error_content(resp: httpx.Response) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
    """Parse error content using default error handler."""
    return default_error_handler.parse_error_content(resp)

def raise_api_error(resp: httpx.Response) -> None:
    """Raise API error using default error handler."""
    default_error_handler.raise_api_error(resp)