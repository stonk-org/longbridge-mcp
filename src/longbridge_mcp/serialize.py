from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from decimal import Decimal
import inspect


def _is_scalar(value: object) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def serialize(value: object) -> object:
    if _is_scalar(value):
        return value

    if isinstance(value, Decimal):
        return str(value)

    if isinstance(value, (datetime, date, time)):
        return value.isoformat()

    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [serialize(item) for item in value]

    if inspect.isclass(value):
        return value.__name__

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
        return {name: serialize(getattr(value, name)) for name in public_names}

    return str(value)
