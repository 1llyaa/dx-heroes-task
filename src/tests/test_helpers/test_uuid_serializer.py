"""
Tests for UUID serializer helper.
"""

import pytest
from uuid import uuid4
from applifting_sdk.helpers.uuid_serializer import _to_jsonable


class TestUUIDSerializer:
    """Test UUID serializer helper."""

    def test_uuid_in_dict(self):
        """Test UUID serialization in dictionary."""
        test_uuid = uuid4()
        data = {"id": test_uuid, "name": "test"}

        result = _to_jsonable(data)
        assert result["id"] == str(test_uuid)
        assert result["name"] == "test"

    def test_uuid_in_list(self):
        """Test UUID serialization in list."""
        test_uuid = uuid4()
        data = [test_uuid, "test", 42]

        result = _to_jsonable(data)
        assert result[0] == str(test_uuid)
        assert result[1] == "test"
        assert result[2] == 42

    def test_primitive_values(self):
        """Test primitive values are unchanged."""
        data = {"string": "test", "number": 42, "boolean": True, "none": None}

        result = _to_jsonable(data)
        assert result == data

    def test_empty_structures(self):
        """Test empty structures are unchanged."""
        data = {"empty_dict": {}, "empty_list": [], "empty_string": ""}

        result = _to_jsonable(data)
        assert result == data

    def test_nested_dict_with_uuid(self):
        """Test nested dictionary with UUID."""
        test_uuid = uuid4()
        data = {"user": {"id": test_uuid, "profile": {"avatar_id": uuid4()}}}

        result = _to_jsonable(data)
        assert result["user"]["id"] == str(test_uuid)
        assert isinstance(result["user"]["profile"]["avatar_id"], str)

    def test_list_of_dicts_with_uuid(self):
        """Test list of dictionaries with UUIDs."""
        test_uuid = uuid4()
        data = [{"id": test_uuid, "name": "item1"}, {"id": uuid4(), "name": "item2"}]

        result = _to_jsonable(data)
        assert result[0]["id"] == str(test_uuid)
        assert result[1]["id"] != str(test_uuid)  # Different UUID

    def test_mixed_types_with_uuid(self):
        """Test mixed types including UUIDs."""
        test_uuid = uuid4()
        data = {
            "string": "test",
            "number": 42,
            "uuid": test_uuid,
            "list": [test_uuid, "string", 123],
            "dict": {"nested_uuid": uuid4()},
        }

        result = _to_jsonable(data)
        assert result["uuid"] == str(test_uuid)
        assert result["list"][0] == str(test_uuid)
        assert isinstance(result["dict"]["nested_uuid"], str)

    def test_no_uuid_data(self):
        """Test data without UUIDs is unchanged."""
        data = {
            "name": "John Doe",
            "age": 30,
            "active": True,
            "tags": ["developer", "python"],
            "metadata": {"department": "engineering"},
        }

        result = _to_jsonable(data)
        assert result == data
