from typing import Any
from uuid import UUID

# TODO Look into this helper more


def _to_jsonable(obj: Any) -> Any:
    try:
        from pydantic import BaseModel

        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json")
    except Exception:
        pass

    try:
        if hasattr(obj, "dict"):
            return obj.model_dump()
    except Exception:
        pass

    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, UUID):
        return str(obj)
    return obj
