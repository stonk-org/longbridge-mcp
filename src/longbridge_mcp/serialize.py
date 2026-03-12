from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from decimal import Decimal
import inspect


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def _looks_like_enum_singleton(value: object) -> bool:
    value_type = type(value)
    public_names = [name for name in dir(value) if not name.startswith("_")]
    if not public_names:
        return False

    same_type_members = 0
    for name in public_names:
        try:
            attr = getattr(value, name)
        except Exception:
            return False
        if type(attr) is not value_type:
            return False
        same_type_members += 1

    return same_type_members > 0


def serialize(value: object, _seen: set[int] | None = None) -> object:
    if _seen is None:
        _seen = set()

    if _is_scalar(value):
        return value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if _looks_like_enum_singleton(value):
        return str(value)

    if isinstance(value, Mapping):
        return {str(key): serialize(item, _seen) for key, item in value.items()}

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [serialize(item, _seen) for item in value]

    if inspect.isclass(value):
        return value.__name__

    value_id = id(value)
    if value_id in _seen:
        return str(value)
    _seen.add(value_id)

    public_names = []
    for name in dir(value):
        if name.startswith("_"):
            continue
        try:
            attr = getattr(value, name)
        except Exception:
            continue
        if callable(attr):
            continue
        public_names.append(name)

    if public_names:
        return {name: serialize(getattr(value, name), _seen) for name in public_names}

    return str(value)
