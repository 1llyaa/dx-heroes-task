from __future__ import annotations

from collections.abc import Callable
from typing import Any, Union

import httpx
import requests

from applifting_sdk.exceptions import (
    APIError,
    AuthenticationError,
    BadRequestError,
    ConflictError,
    NotFoundError,
    PermissionDenied,
    RateLimitError,
    ServerError,
    ValidationFailed,
)
from applifting_sdk.models import HTTPValidationError

# Type alias for supported response types
ResponseType = Union[httpx.Response, requests.Response]


class ErrorHandler:
    """Handles HTTP error response parsing and exception raising for both httpx and requests."""

    def __init__(self):
        """Initialize error handler with default status code mappings."""
        self._status_mappings: dict[int, Callable[[int, dict | None, str | None], Exception]] = {
            400: self._create_bad_request_error,
            401: self._create_auth_error,
            403: self._create_permission_error,
            404: self._create_not_found_error,
            409: self._create_conflict_error,
            422: self._create_validation_error,
            429: self._create_rate_limit_error,
        }

    def parse_error_content(self, resp: ResponseType) -> tuple[dict[str, Any] | None, str | None]:
        """
        Parse error response content, prioritizing JSON payload over text.
        Works with both httpx.Response and requests.Response.

        Args:
            resp: HTTP response object (httpx or requests)

        Returns:
            Tuple of (json_payload, text_content)
        """
        content_type = self._get_content_type(resp)

        # Try JSON first if content type suggests it
        payload = None
        if self._is_json_content_type(content_type):
            payload = self._extract_json_payload(resp)

        # Fallback to text if no JSON payload
        text = None
        if payload is None:
            text = self._extract_text_content(resp)

        return payload, text

    def raise_api_error(self, resp: ResponseType) -> None:
        """
        Parse response and raise appropriate API exception.
        Works with both httpx.Response and requests.Response.

        Args:
            resp: HTTP response object (httpx or requests)

        Raises:
            APIError: Or one of its subclasses based on status code
        """
        status = self._get_status_code(resp)
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

    def add_status_mapping(
        self, status_code: int, error_creator: Callable[[int, dict | None, str | None], Exception]
    ) -> None:
        """
        Add custom status code mapping.

        Args:
            status_code: HTTP status code
            error_creator: Function that creates the exception
        """
        self._status_mappings[status_code] = error_creator

    def _get_status_code(self, resp: ResponseType) -> int:
        """Get status code from response object."""
        return resp.status_code

    def _get_content_type(self, resp: ResponseType) -> str:
        """Get content type from response headers."""
        return resp.headers.get("content-type", "")

    def _extract_json_payload(self, resp: ResponseType) -> dict[str, Any] | None:
        """Extract JSON payload from response if valid JSON dict."""
        try:
            obj = resp.json()
            if isinstance(obj, dict):
                return obj
            return None
        except Exception:
            return None

    def _extract_text_content(self, resp: ResponseType) -> str | None:
        """Extract text content from response."""
        try:
            return resp.text
        except Exception:
            return None

    def _is_json_content_type(self, content_type: str) -> bool:
        """Check if content type indicates JSON."""
        return "application/json" in content_type.lower()

    # Error creator methods
    def _create_bad_request_error(self, status: int, payload: dict | None, text: str | None) -> BadRequestError:
        return BadRequestError(status, "Bad request", details=payload, response_text=text)

    def _create_auth_error(self, status: int, payload: dict | None, text: str | None) -> AuthenticationError:
        return AuthenticationError(status, "Unauthorized", details=payload, response_text=text)

    def _create_permission_error(self, status: int, payload: dict | None, text: str | None) -> PermissionDenied:
        return PermissionDenied(status, "Forbidden", details=payload, response_text=text)

    def _create_not_found_error(self, status: int, payload: dict | None, text: str | None) -> NotFoundError:
        return NotFoundError(status, "Not Found", details=payload, response_text=text)

    def _create_conflict_error(self, status: int, payload: dict | None, text: str | None) -> ConflictError:
        return ConflictError(status, "Conflict", details=payload, response_text=text)

    def _create_validation_error(self, status: int, payload: dict | None, text: str | None) -> ValidationFailed:
        details: HTTPValidationError | None = None
        if isinstance(payload, dict):
            try:
                details = HTTPValidationError(**payload)
            except Exception:
                pass
        return ValidationFailed(status, "Validation failed", details=details, response_text=text)

    def _create_rate_limit_error(self, status: int, payload: dict | None, text: str | None) -> RateLimitError:
        return RateLimitError(status, "Too Many Requests", details=payload, response_text=text)


# Default instance for backwards compatibility
default_error_handler = ErrorHandler()


# Convenience functions that use the default handler
def parse_error_content(resp: ResponseType) -> tuple[dict[str, Any] | None, str | None]:
    """Parse error content using default error handler."""
    return default_error_handler.parse_error_content(resp)


def raise_api_error(resp: ResponseType) -> None:
    """Raise API error using default error handler."""
    default_error_handler.raise_api_error(resp)
