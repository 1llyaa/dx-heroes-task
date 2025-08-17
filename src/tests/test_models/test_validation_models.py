"""
Tests for validation models.
"""

from applifting_sdk.models.validation import HTTPValidationError, ValidationError


class TestValidationError:
    """Test ValidationError model."""

    def test_valid_validation_error(self):
        """Test creating ValidationError with valid data."""
        error = ValidationError(loc=["body", "field_name"], msg="Field is required", type="missing")
        assert error.loc == ["body", "field_name"]
        assert error.msg == "Field is required"
        assert error.type == "missing"

    def test_empty_location(self):
        """Test creating ValidationError with empty location."""
        error = ValidationError(loc=[], msg="No location specified", type="value_error")
        assert error.loc == []

    def test_model_serialization(self):
        """Test model serialization to dict."""
        error = ValidationError(loc=["query", "param"], msg="Invalid parameter", type="type_error")
        data = error.model_dump()
        assert data["loc"] == ["query", "param"]
        assert data["msg"] == "Invalid parameter"
        assert data["type"] == "type_error"


class TestHTTPValidationError:
    """Test HTTPValidationError model."""

    def test_valid_http_validation_error(self):
        """Test creating HTTPValidationError with valid data."""
        validation_errors = [ValidationError(loc=["body", "name"], msg="Name is required", type="missing")]
        error = HTTPValidationError(detail=validation_errors)
        assert len(error.detail) == 1
        assert error.detail[0].msg == "Name is required"

    def test_empty_detail(self):
        """Test creating HTTPValidationError with empty detail."""
        error = HTTPValidationError(detail=[])
        assert error.detail == []

    def test_model_serialization(self):
        """Test model serialization to dict."""
        validation_errors = [ValidationError(loc=["body", "email"], msg="Invalid email format", type="value_error")]
        error = HTTPValidationError(detail=validation_errors)
        data = error.model_dump()
        assert "detail" in data
        assert len(data["detail"]) == 1
