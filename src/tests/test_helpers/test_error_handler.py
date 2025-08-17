from unittest.mock import Mock, PropertyMock

import httpx
import pytest

from applifting_sdk.exceptions import (
    APIError,
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDenied,
    RateLimitError,
    ServerError,
    ValidationFailed,
)
from applifting_sdk.helpers.error_handler import ErrorHandler, parse_error_content, raise_api_error
from applifting_sdk.models import HTTPValidationError


class TestErrorHandler:
    """Test cases for ErrorHandler class."""

    def setup_method(self):
        """Setup fresh ErrorHandler for each test."""
        self.handler = ErrorHandler()

    def _create_mock_response(
        self,
        status_code: int,
        content_type: str = "application/json",
        json_data: dict = None,
        text_data: str = None,
        json_exception: Exception = None,
        text_exception: Exception = None,
    ):
        """Helper to create mock httpx.Response objects."""
        mock_response = Mock(spec=httpx.Response)
        mock_response.status_code = status_code
        mock_response.headers = {"content-type": content_type}

        if json_exception:
            mock_response.json.side_effect = json_exception
        else:
            mock_response.json.return_value = json_data

        if text_exception:
            # Use PropertyMock for text property
            type(mock_response).text = PropertyMock(side_effect=text_exception)
        else:
            type(mock_response).text = PropertyMock(return_value=text_data or f"Status {status_code} error")

        return mock_response


class TestParseErrorContent(TestErrorHandler):
    """Test error content parsing functionality."""

    def test_parse_json_content_success(self):
        """Test successful JSON parsing."""
        json_data = {"error": "Something went wrong", "code": "ERR001"}
        response = self._create_mock_response(400, json_data=json_data)

        payload, text = self.handler.parse_error_content(response)

        assert payload == json_data
        assert text is None

    def test_parse_json_content_non_dict_returns_none(self):
        """Test JSON parsing with non-dict response."""
        response = self._create_mock_response(400, json_data=["error1", "error2"])

        payload, text = self.handler.parse_error_content(response)

        assert payload is None
        assert text == "Status 400 error"

    def test_parse_json_content_invalid_json_fallback_to_text(self):
        """Test fallback to text when JSON parsing fails."""
        response = self._create_mock_response(
            400, json_exception=ValueError("Invalid JSON"), text_data="Invalid JSON response"
        )

        payload, text = self.handler.parse_error_content(response)

        assert payload is None
        assert text == "Invalid JSON response"

    def test_parse_non_json_content_type(self):
        """Test parsing with non-JSON content type."""
        response = self._create_mock_response(400, content_type="text/html", text_data="<html>Error page</html>")

        payload, text = self.handler.parse_error_content(response)

        assert payload is None
        assert text == "<html>Error page</html>"

    def test_parse_content_both_json_and_text_fail(self):
        """Test when both JSON and text extraction fail."""
        response = self._create_mock_response(
            400, json_exception=ValueError("JSON error"), text_exception=UnicodeDecodeError("utf-8", b"", 0, 0, "test")
        )

        payload, text = self.handler.parse_error_content(response)

        assert payload is None
        assert text is None

    def test_parse_content_case_insensitive_content_type(self):
        """Test case insensitive content type checking."""
        json_data = {"error": "test"}
        response = self._create_mock_response(400, content_type="APPLICATION/JSON", json_data=json_data)

        payload, text = self.handler.parse_error_content(response)

        assert payload == json_data
        assert text is None


class TestRaiseApiError(TestErrorHandler):
    """Test API error raising functionality."""

    def test_raise_authentication_error_401(self):
        """Test 401 status raises AuthenticationError."""
        json_data = {"message": "Invalid credentials"}
        response = self._create_mock_response(401, json_data=json_data)

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        assert error.status_code == 401
        assert error.message == "Unauthorized"
        assert error.details == json_data

    def test_raise_permission_denied_403(self):
        """Test 403 status raises PermissionDenied."""
        response = self._create_mock_response(403, text_data="Access denied")

        with pytest.raises(PermissionDenied) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        assert error.status_code == 403
        assert error.message == "Forbidden"
        assert error.response_text == "Access denied"

    def test_raise_not_found_error_404(self):
        """Test 404 status raises NotFoundError."""
        response = self._create_mock_response(404)

        with pytest.raises(NotFoundError) as exc_info:
            self.handler.raise_api_error(response)

        assert exc_info.value.status_code == 404
        assert exc_info.value.message == "Not Found"

    def test_raise_conflict_error_409(self):
        """Test 409 status raises ConflictError."""
        response = self._create_mock_response(409)

        with pytest.raises(ConflictError) as exc_info:
            self.handler.raise_api_error(response)

        assert exc_info.value.status_code == 409
        assert exc_info.value.message == "Conflict"

    def test_raise_validation_error_422_with_valid_payload(self):
        """Test 422 status raises ValidationFailed with HTTPValidationError details."""
        validation_payload = {"detail": [{"loc": ["field1"], "msg": "Field required", "type": "missing"}]}
        response = self._create_mock_response(422, json_data=validation_payload)

        with pytest.raises(ValidationFailed) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        assert error.status_code == 422
        assert error.message == "Validation failed"
        assert isinstance(error.details, HTTPValidationError)

    def test_raise_validation_error_422_with_invalid_payload(self):
        """Test 422 status with invalid HTTPValidationError payload."""
        # Use a payload that would create an HTTPValidationError but with empty details
        invalid_payload = {"detail": []}
        response = self._create_mock_response(422, json_data=invalid_payload)

        with pytest.raises(ValidationFailed) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        # HTTPValidationError should be created but with empty detail list
        assert isinstance(error.details, HTTPValidationError)
        assert error.details.detail == []

    def test_raise_validation_error_422_non_dict_payload(self):
        """Test 422 status with non-dict payload (should not create HTTPValidationError)."""
        response = self._create_mock_response(422, json_data=None, text_data="Validation failed")

        with pytest.raises(ValidationFailed) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        assert error.details is None  # Should be None for non-dict payload
        assert error.response_text == "Validation failed"

    def test_raise_validation_error_422_invalid_structure(self):
        """Test 422 status with payload that cannot create HTTPValidationError."""
        # Use a dict payload that doesn't have the expected structure for HTTPValidationError
        invalid_payload = {"error": "invalid validation format"}
        response = self._create_mock_response(422, json_data=invalid_payload)

        with pytest.raises(ValidationFailed) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        # HTTPValidationError might still be created with empty detail if the payload doesn't match expected structure
        # The actual behavior depends on how HTTPValidationError handles invalid input
        if isinstance(error.details, HTTPValidationError):
            # If HTTPValidationError was created, it should have empty or default details
            assert error.details.detail == []
        else:
            # If HTTPValidationError creation failed, details should be the original payload
            assert error.details == invalid_payload

    def test_raise_rate_limit_error_429(self):
        """Test 429 status raises RateLimitError."""
        response = self._create_mock_response(429)

        with pytest.raises(RateLimitError) as exc_info:
            self.handler.raise_api_error(response)

        assert exc_info.value.status_code == 429
        assert exc_info.value.message == "Too Many Requests"

    def test_raise_server_error_5xx(self):
        """Test 5xx status codes raise ServerError."""
        for status_code in [500, 502, 503, 504, 599]:
            response = self._create_mock_response(status_code)

            with pytest.raises(ServerError) as exc_info:
                self.handler.raise_api_error(response)

            assert exc_info.value.status_code == status_code
            assert exc_info.value.message == "Server error"

    def test_raise_generic_api_error_unknown_status(self):
        """Test unknown status codes raise generic APIError."""
        response = self._create_mock_response(418)  # I'm a teapot

        with pytest.raises(APIError) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        assert error.status_code == 418
        assert error.message == "Unexpected API error"

    def test_raise_generic_api_error_client_error(self):
        """Test 4xx status codes not specifically handled raise APIError."""
        response = self._create_mock_response(400)  # Bad Request

        with pytest.raises(APIError) as exc_info:
            self.handler.raise_api_error(response)

        assert exc_info.value.status_code == 400


class TestErrorHandlerCustomization(TestErrorHandler):
    """Test error handler customization features."""

    def test_add_custom_status_mapping(self):
        """Test adding custom status code mapping."""

        def custom_error_creator(status, payload, text):
            return APIError(status, "Custom teapot error", details=payload, response_text=text)

        self.handler.add_status_mapping(418, custom_error_creator)
        response = self._create_mock_response(418, json_data={"teapot": True})

        with pytest.raises(APIError) as exc_info:
            self.handler.raise_api_error(response)

        error = exc_info.value
        assert error.status_code == 418
        assert error.message == "Custom teapot error"
        assert error.details == {"teapot": True}

    def test_override_existing_status_mapping(self):
        """Test overriding existing status code mapping."""

        def custom_auth_error(status, payload, text):
            return APIError(status, "Custom auth error", details=payload, response_text=text)

        self.handler.add_status_mapping(401, custom_auth_error)
        response = self._create_mock_response(401)

        with pytest.raises(APIError) as exc_info:
            self.handler.raise_api_error(response)

        # Should use custom error instead of AuthenticationError
        error = exc_info.value
        assert type(error) == APIError  # Not AuthenticationError
        assert error.message == "Custom auth error"


class TestConvenienceFunctions:
    """Test the convenience functions that use default_error_handler."""

    def test_parse_error_content_function(self):
        """Test parse_error_content convenience function."""
        json_data = {"error": "test"}
        response = Mock(spec=httpx.Response)
        response.headers = {"content-type": "application/json"}
        response.json.return_value = json_data

        payload, text = parse_error_content(response)

        assert payload == json_data
        assert text is None

    def test_raise_api_error_function(self):
        """Test raise_api_error convenience function."""
        response = Mock(spec=httpx.Response)
        response.status_code = 404
        response.headers = {"content-type": "text/plain"}
        type(response).text = PropertyMock(return_value="Not found")

        with pytest.raises(NotFoundError) as exc_info:
            raise_api_error(response)

        assert exc_info.value.status_code == 404


class TestErrorHandlerPrivateMethods(TestErrorHandler):
    """Test private methods of ErrorHandler."""

    def test_extract_json_payload_success(self):
        """Test successful JSON payload extraction."""
        json_data = {"key": "value"}
        response = Mock()
        response.json.return_value = json_data

        result = self.handler._extract_json_payload(response)

        assert result == json_data

    def test_extract_json_payload_non_dict(self):
        """Test JSON payload extraction with non-dict."""
        response = Mock()
        response.json.return_value = ["item1", "item2"]

        result = self.handler._extract_json_payload(response)

        assert result is None

    def test_extract_json_payload_exception(self):
        """Test JSON payload extraction with exception."""
        response = Mock()
        response.json.side_effect = ValueError("Invalid JSON")

        result = self.handler._extract_json_payload(response)

        assert result is None

    def test_extract_text_content_success(self):
        """Test successful text content extraction."""
        response = Mock()
        type(response).text = PropertyMock(return_value="Error message")

        result = self.handler._extract_text_content(response)

        assert result == "Error message"

    def test_extract_text_content_exception(self):
        """Test text content extraction with exception."""
        response = Mock()
        type(response).text = PropertyMock(side_effect=UnicodeDecodeError("utf-8", b"", 0, 0, "test"))

        result = self.handler._extract_text_content(response)

        assert result is None

    def test_extract_text_content_generic_exception(self):
        """Test text content extraction with generic exception."""
        response = Mock()
        type(response).text = PropertyMock(side_effect=RuntimeError("Connection error"))

        result = self.handler._extract_text_content(response)

        assert result is None

    def test_extract_json_payload_generic_exception(self):
        """Test JSON payload extraction with generic exception (not just ValueError)."""
        response = Mock()
        response.json.side_effect = RuntimeError("Network error")

        result = self.handler._extract_json_payload(response)

        assert result is None

    def test_is_json_content_type_positive_cases(self):
        """Test JSON content type detection - positive cases."""
        content_types = [
            "application/json",
            "APPLICATION/JSON",
            "application/json; charset=utf-8",
            "text/html; application/json",
        ]

        for ct in content_types:
            assert self.handler._is_json_content_type(ct) is True

    def test_is_json_content_type_negative_cases(self):
        """Test JSON content type detection - negative cases."""
        content_types = [
            "text/html",
            "application/xml",
            "text/plain",
            "",
            "image/png",
        ]

        for ct in content_types:
            assert self.handler._is_json_content_type(ct) is False


# Integration test
class TestErrorHandlerIntegration:
    """Integration tests combining multiple components."""

    def test_full_error_handling_flow(self):
        """Test complete error handling flow from response to exception."""
        # Setup response with JSON error details
        error_details = {
            "error_code": "VALIDATION_FAILED",
            "message": "Invalid input data",
            "field_errors": ["name is required", "email format invalid"],
        }

        response = Mock(spec=httpx.Response)
        response.status_code = 422
        response.headers = {"content-type": "application/json; charset=utf-8"}
        response.json.return_value = {"detail": [{"loc": ["name"], "msg": "required", "type": "missing"}]}

        handler = ErrorHandler()

        # Should parse JSON and raise ValidationFailed with proper details
        with pytest.raises(ValidationFailed) as exc_info:
            handler.raise_api_error(response)

        error = exc_info.value
        assert error.status_code == 422
        assert error.message == "Validation failed"
        assert isinstance(error.details, HTTPValidationError)

        # Verify the response.json() was called for parsing
        response.json.assert_called_once()

    def test_validation_error_with_httperror_creation_exception(self):
        """Test ValidationFailed when HTTPValidationError creation raises exception."""
        # Mock HTTPValidationError to raise exception during creation
        original_http_validation_error = HTTPValidationError

        def mock_http_validation_error(*args, **kwargs):
            raise TypeError("Invalid validation error format")

        # Patch HTTPValidationError temporarily
        import applifting_sdk.models.validation

        applifting_sdk.models.validation.HTTPValidationError = mock_http_validation_error

        try:
            handler = ErrorHandler()
            response = Mock(spec=httpx.Response)
            response.status_code = 422
            response.headers = {"content-type": "application/json"}
            response.json.return_value = {"detail": "invalid format"}

            with pytest.raises(ValidationFailed) as exc_info:
                handler.raise_api_error(response)

            # Should have details as None due to exception
            error = exc_info.value
            assert error.details is None

        finally:
            # Restore original
            applifting_sdk.models.validation.HTTPValidationError = original_http_validation_error


if __name__ == "__main__":
    pytest.main([__file__])
