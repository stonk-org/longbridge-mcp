import pytest

from longbridge_mcp.validation import HistoryCandlesticksInput, OrdersQueryInput, SymbolListInput


def test_history_candlesticks_requires_date_range_for_by_date():
    with pytest.raises(ValueError):
        HistoryCandlesticksInput(
            symbol="AAPL.US",
            period="1m",
            adjust_type="no_adjust",
            query_type="by_date",
        )


def test_history_candlesticks_accepts_aliases():
    payload = HistoryCandlesticksInput(
        symbol="AAPL.US",
        period="1m",
        adjust_type="forward_adjust",
        query_type="by_offset",
        forward=True,
    )

    assert str(payload.sdk_period()) == "Period.Min_1"
    assert str(payload.sdk_adjust_type()) == "AdjustType.ForwardAdjust"


def test_symbol_list_limit_is_enforced():
    with pytest.raises(ValueError):
        SymbolListInput(symbols=["AAPL.US"] * 501)


def test_orders_query_maps_enum_filters():
    payload = OrdersQueryInput(statuses=["filled"], side="buy", market="us")
    assert str(payload.sdk_statuses()[0]) == "OrderStatus.Filled"
    assert str(payload.sdk_side()) == "OrderSide.Buy"
    assert str(payload.sdk_market()) == "Market.US"
