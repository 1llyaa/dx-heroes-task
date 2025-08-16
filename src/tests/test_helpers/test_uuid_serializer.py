from uuid import uuid4, UUID
from unittest.mock import Mock
from applifting_sdk.helpers.uuid_serializer import JSONSerializer


class TestJSONSerializerAdditional:
    """Additional test cases for JSON serializer helper."""

    def test_class_method_directly(self):
        """Test calling JSONSerializer.to_jsonable directly."""
        test_uuid = uuid4()
        data = {"id": test_uuid, "name": "test"}

        result = JSONSerializer.to_jsonable(data)
        assert result["id"] == str(test_uuid)
        assert result["name"] == "test"

    def test_pydantic_model_dump_exception(self):
        """Test Pydantic model where model_dump raises exception."""
        mock_model = Mock()
        mock_model.model_dump = Mock(side_effect=ValueError("Serialization failed"))
        mock_model.dict = Mock(return_value={"fallback": "success"})

        result = JSONSerializer.to_jsonable(mock_model)
        assert result == {"fallback": "success"}

    def test_pydantic_import_error_simulation(self):
        """Test behavior when pydantic import fails completely."""

        class FakeModel:
            def model_dump(self, mode=None):
                return {"fake": "model"}

            def dict(self):
                return {"dict": "method"}

        # The actual implementation will try model_dump first, which succeeds
        # So this test should expect the model_dump result, not dict result
        obj = FakeModel()
        result = JSONSerializer.to_jsonable(obj)
        assert result == {"fake": "model"}

    def test_object_with_both_methods_pydantic_fails(self):
        """Test object with both model_dump and dict when pydantic check fails."""

        class BothMethods:
            def model_dump(self, mode=None):
                if mode == "json":
                    raise AttributeError("Not a real pydantic model")
                return {"model_dump": "result"}

            def dict(self):
                return {"dict_method": "result"}

        obj = BothMethods()
        result = JSONSerializer.to_jsonable(obj)
        # Should fall back to dict method since pydantic handling fails
        assert result == {"dict_method": "result"}

    def test_uuid_string_conversion_edge_cases(self):
        """Test UUID string conversion with edge cases."""
        # Test with UUID object directly
        test_uuid = UUID("12345678-1234-5678-1234-123456789abc")
        result = JSONSerializer.to_jsonable(test_uuid)
        assert result == "12345678-1234-5678-1234-123456789abc"

        # Test UUID in various nested positions
        data = {"start": test_uuid, "middle": {"uuid": test_uuid, "other": "value"}, "end": [1, 2, test_uuid]}
        result = JSONSerializer.to_jsonable(data)
        assert all(isinstance(val, str) for val in [result["start"], result["middle"]["uuid"], result["end"][2]])

    def test_none_and_falsy_values(self):
        """Test handling of None and other falsy values."""
        data = {
            "none_val": None,
            "empty_string": "",
            "zero": 0,
            "false": False,
            "empty_list": [],
            "empty_dict": {},
            "uuid_with_falsy": {"id": uuid4(), "active": False, "count": 0},
        }

        result = JSONSerializer.to_jsonable(data)

        assert result["none_val"] is None
        assert result["empty_string"] == ""
        assert result["zero"] == 0
        assert result["false"] is False
        assert result["empty_list"] == []
        assert result["empty_dict"] == {}
        assert isinstance(result["uuid_with_falsy"]["id"], str)
        assert result["uuid_with_falsy"]["active"] is False

    def test_large_nested_structure_performance(self):
        """Test performance with large nested structures."""
        # Create a reasonably large structure
        large_data = {}
        test_uuid = uuid4()

        for i in range(100):
            large_data[f"item_{i}"] = {
                "id": test_uuid,
                "nested": {"values": [uuid4() for _ in range(10)], "metadata": {"uuid": uuid4(), "index": i}},
            }

        result = JSONSerializer.to_jsonable(large_data)

        # Verify some random items were processed correctly
        assert isinstance(result["item_0"]["id"], str)
        assert isinstance(result["item_50"]["nested"]["values"][0], str)
        assert isinstance(result["item_99"]["nested"]["metadata"]["uuid"], str)

    def test_object_with_callable_dict_but_not_method(self):
        """Test object where dict is callable but not a method."""

        class WeirdObject:
            def __init__(self):
                self.dict = lambda: {"callable": "dict"}

        obj = WeirdObject()
        result = JSONSerializer.to_jsonable(obj)

        # Should call the callable dict
        assert result == {"callable": "dict"}

    def test_object_with_non_callable_dict_attribute(self):
        """Test object with dict attribute that's not callable."""

        class NonCallableDict:
            def __init__(self):
                self.dict = {"not": "callable"}

        obj = NonCallableDict()
        result = JSONSerializer.to_jsonable(obj)

        # Should return object unchanged since dict is not callable
        assert result is obj

    def test_mixed_tuple_and_list_nesting(self):
        """Test mixed tuple and list nesting with UUIDs."""
        test_uuid = uuid4()
        data = [(test_uuid, {"nested": [uuid4(), (uuid4(), "deep")]}), {"tuple_in_dict": (uuid4(), [uuid4()])}]

        result = JSONSerializer.to_jsonable(data)

        # Check structure conversion and UUID serialization
        assert isinstance(result[0], list)  # Tuple becomes list
        assert isinstance(result[0][0], str)  # UUID converted
        assert isinstance(result[0][1]["nested"][0], str)  # Nested UUID
        assert isinstance(result[0][1]["nested"][1], list)  # Nested tuple becomes list
        assert isinstance(result[0][1]["nested"][1][0], str)  # Deep UUID

        assert isinstance(result[1]["tuple_in_dict"], list)  # Tuple in dict
        assert isinstance(result[1]["tuple_in_dict"][0], str)  # UUID in tuple
        assert isinstance(result[1]["tuple_in_dict"][1][0], str)  # UUID in nested list

    def test_exception_in_dict_access(self):
        """Test handling when dict() method raises exception."""

        class ExceptionOnDict:
            def dict(self):
                raise RuntimeError("Dict method failed")

        obj = ExceptionOnDict()

        # Based on your implementation, if dict() raises an exception,
        # the object should be returned unchanged
        result = JSONSerializer.to_jsonable(obj)
        assert result is obj

    def test_model_dump_with_different_modes(self):
        """Test model_dump with different mode parameters."""

        class FlexibleModel:
            def model_dump(self, mode=None):
                if mode == "json":
                    return {"mode": "json", "uuid": str(uuid4())}
                elif mode == "dict":
                    return {"mode": "dict", "uuid": uuid4()}
                else:
                    return {"mode": "default", "uuid": uuid4()}

        obj = FlexibleModel()
        result = JSONSerializer.to_jsonable(obj)

        # Should use json mode and have string UUID
        assert result["mode"] == "json"
        assert isinstance(result["uuid"], str)

    def test_set_type_handling(self):
        """Test how sets are handled (should remain unchanged)."""
        test_uuid = uuid4()
        data = {"uuid_set": {test_uuid, "string", 123}}

        result = JSONSerializer.to_jsonable(data)

        # Sets should remain as sets (not converted to lists)
        assert isinstance(result["uuid_set"], set)
        # But we can't easily test UUID conversion in sets due to order
