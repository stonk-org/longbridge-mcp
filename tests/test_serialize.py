from datetime import date, datetime
from decimal import Decimal

from longbridge_mcp.serialize import serialize


class SampleObject:
    foo = "bar"
    amount = Decimal("1.23")
    created = date(2026, 3, 12)


def test_serialize_nested_values():
    result = serialize(
        {
            "value": Decimal("3.14"),
            "items": [datetime(2026, 3, 12, 9, 30), SampleObject()],
        }
    )

    assert result == {
        "value": "3.14",
        "items": [
            "2026-03-12T09:30:00",
            {"amount": "1.23", "created": "2026-03-12", "foo": "bar"},
        ],
    }
