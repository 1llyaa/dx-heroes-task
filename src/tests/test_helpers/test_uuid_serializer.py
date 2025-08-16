"""
Tests for UUID serializer helper.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock
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

    def test_pydantic_model_with_model_dump_json_mode(self):
        """Test Pydantic model with model_dump(mode='json') - lines 9-11."""
        try:
            from pydantic import BaseModel

            class TestModel(BaseModel):
                id: str
                value: int

                def model_dump(self, mode=None):
                    if mode == "json":
                        return {"id": self.id, "value": self.value, "serialized": True}
                    return {"id": self.id, "value": self.value}

            model = TestModel(id="test", value=42)
            result = _to_jsonable(model)

            assert result == {"id": "test", "value": 42, "serialized": True}

        except ImportError:
            pytest.skip("Pydantic not available")

    def test_pydantic_import_error_fallback(self):
        """Test fallback when pydantic import/usage fails - lines 12-13."""
        # Create a mock object that looks like it might be a BaseModel but isn't
        mock_obj = Mock()
        mock_obj.model_dump = Mock(return_value={"fallback": "data"})

        # Add the dict attribute so hasattr(obj, "dict") returns True
        mock_obj.dict = Mock()

        # This should fall through to the dict() method test since pydantic handling will fail
        result = _to_jsonable(mock_obj)
        assert result == {"fallback": "data"}

    def test_object_with_dict_method(self):
        """Test object with dict() method - lines 15-18."""
        class CustomObject:
            def __init__(self, data):
                self.data = data

            def model_dump(self):
                return {"custom": self.data, "from_dict": True}

            # Also add dict for the hasattr check
            def dict(self):
                return self.model_dump()

        obj = CustomObject("test_data")
        result = _to_jsonable(obj)

        assert result == {"custom": "test_data", "from_dict": True}

    def test_dict_method_exception_fallback(self):
        """Test fallback when dict() method raises exception - lines 19-20."""
        class FailingDictObject:
            def __init__(self):
                pass

            def model_dump(self):
                raise RuntimeError("Dict method failed")

            def dict(self):
                return self.model_dump()

            # Add hasattr dict to pass the check
            @property
            def dict(self):
                raise RuntimeError("Dict method failed")

        obj = FailingDictObject()
        # Should return the object unchanged since dict() method failed
        result = _to_jsonable(obj)

        assert result is obj

    def test_object_without_dict_method(self):
        """Test object without dict() method returns unchanged."""
        class SimpleObject:
            def __init__(self, value):
                self.value = value

        obj = SimpleObject("test")
        result = _to_jsonable(obj)

        assert result is obj

    def test_tuple_serialization(self):
        """Test tuple serialization with UUIDs."""
        test_uuid = uuid4()
        data = (test_uuid, "test", 42, {"nested_uuid": uuid4()})

        result = _to_jsonable(data)

        assert isinstance(result, list)  # Tuples become lists
        assert result[0] == str(test_uuid)
        assert result[1] == "test"
        assert result[2] == 42
        assert isinstance(result[3]["nested_uuid"], str)

    def test_complex_nested_structure(self):
        """Test complex nested structure with mixed types."""
        test_uuid = uuid4()

        # Create an object with dict method
        class DataObject:
            def model_dump(self):
                return {"object_uuid": uuid4(), "type": "data_object"}

            # Add hasattr check for dict
            @property
            def dict(self):
                return True

        # Create the object and get its expected result first
        data_obj = DataObject()
        expected_obj_result = data_obj.model_dump()

        data = {
            "users": [
                {"id": test_uuid, "name": "user1"},
                {"id": uuid4(), "name": "user2"}
            ],
            "metadata": (test_uuid, "tuple_data", {"nested": uuid4()}),
            "custom_object": data_obj,
            "simple_uuid": test_uuid
        }

        result = _to_jsonable(data)

        # Check all UUIDs are converted to strings
        assert result["users"][0]["id"] == str(test_uuid)
        assert isinstance(result["users"][1]["id"], str)
        assert result["metadata"][0] == str(test_uuid)
        assert isinstance(result["metadata"][2]["nested"], str)
        assert result["custom_object"]["type"] == "data_object"
        assert result["simple_uuid"] == str(test_uuid)

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Empty structures with nested empty structures
        data = {"empty": {}, "nested_empty": {"inner": []}}
        result = _to_jsonable(data)
        assert result == data

        # Single UUID
        test_uuid = uuid4()
        result = _to_jsonable(test_uuid)
        assert result == str(test_uuid)

        # Deeply nested structure
        deep_uuid = uuid4()
        deep_data = {"a": {"b": {"c": {"d": {"uuid": deep_uuid}}}}}
        result = _to_jsonable(deep_data)
        assert result["a"]["b"]["c"]["d"]["uuid"] == str(deep_uuid)