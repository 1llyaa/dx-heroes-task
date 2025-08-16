from typing import Any
from uuid import UUID


class JSONSerializer:
    """Simple helper to convert objects to JSON-serializable format."""

    @staticmethod
    def to_jsonable(obj: Any) -> Any:
        """Convert object to JSON-serializable format."""
        # Handle Pydantic models
        if hasattr(obj, "model_dump"):
            try:
                return obj.model_dump(mode="json")
            except Exception:
                pass

        # Handle other models with dict() method
        if hasattr(obj, "dict") and callable(getattr(obj, "dict")):
            try:
                return obj.dict()
            except Exception:
                pass

        # Handle collections recursively
        if isinstance(obj, dict):
            return {k: JSONSerializer.to_jsonable(v) for k, v in obj.items()}

        if isinstance(obj, (list, tuple)):
            return [JSONSerializer.to_jsonable(item) for item in obj]

        # Handle UUID
        if isinstance(obj, UUID):
            return str(obj)

        # Return as-is for primitives
        return obj
