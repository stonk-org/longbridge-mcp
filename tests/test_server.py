import asyncio
import os

import pytest

from longbridge_mcp.server import build_server


class FakeQuoteContext:
    def static_info(self, symbols):
        return [{"symbols": symbols, "kind": "static"}]

    def quote(self, symbols):
        return [{"symbols": symbols, "kind": "quote"}]

    def depth(self, symbol):
        return {"symbol": symbol, "kind": "depth"}

    def trades(self, symbol, count):
        return [{"symbol": symbol, "count": count}]

    def intraday(self, symbol):
        return {"symbol": symbol, "kind": "intraday"}

    def history_candlesticks_by_date(self, symbol, period, adjust_type, start_date, end_date):
        return {
            "mode": "date",
            "symbol": symbol,
            "period": period.__name__,
            "adjust_type": adjust_type.__name__,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    def history_candlesticks_by_offset(self, symbol, period, adjust_type, forward, count, anchor_datetime=None):
        return {
            "mode": "offset",
            "symbol": symbol,
            "period": period.__name__,
            "adjust_type": adjust_type.__name__,
            "forward": forward,
            "count": count,
            "anchor_datetime": anchor_datetime.isoformat() if anchor_datetime else None,
        }

    def capital_flow(self, symbol):
        return {"symbol": symbol}

    def capital_distribution(self, symbol):
        return {"symbol": symbol}

    def calc_indexes(self, symbols, indexes):
        return {"symbols": symbols, "indexes": [item.__name__ for item in indexes]}

    def watchlist(self):
        return [{"id": 1, "name": "watch"}]

    def security_list(self, market, category=None):
        return {"market": str(market).split(".")[-1], "category": None if category is None else str(category).split(".")[-1]}

    def market_temperature(self, market):
        return {"market": str(market).split(".")[-1]}

    def history_market_temperature(self, market, start_date, end_date):
        return {"market": str(market).split(".")[-1], "start_date": start_date.isoformat(), "end_date": end_date.isoformat()}

    def trading_days(self, market, begin, end):
        return {"market": str(market).split(".")[-1], "begin": begin.isoformat(), "end": end.isoformat()}

    def option_chain_expiry_date_list(self, symbol):
        return [{"symbol": symbol}]

    def option_chain_info_by_date(self, symbol, expiry_date):
        return [{"symbol": symbol, "expiry_date": expiry_date.isoformat()}]

    def option_quote(self, symbols):
        return [{"symbols": symbols}]

    def warrant_quote(self, symbols):
        return [{"symbols": symbols}]

    def warrant_list(self, symbol, sort_by, sort_order, warrant_types, issuer_ids, expiry_dates, price_types, statuses):
        return {
            "symbol": symbol,
            "sort_by": str(sort_by).split(".")[-1],
            "sort_order": str(sort_order).split(".")[-1],
            "statuses": None if statuses is None else [str(item).split(".")[-1] for item in statuses],
        }

    def brokers(self, symbol):
        return {"symbol": symbol}

    def participants(self):
        return [{"id": 1}]

    def quote_level(self):
        return "LV1"

    def quote_package_details(self):
        return [{"package": "basic"}]

    def create_watchlist_group(self, name, securities=None):
        return {"name": name, "securities": securities}

    def update_watchlist_group(self, id, name=None, securities=None, mode=None):
        return {"id": id, "name": name, "securities": securities, "mode": None if mode is None else mode.__name__}

    def delete_watchlist_group(self, id, purge=False):
        return {"id": id, "purge": purge}


class FakeTradeContext:
    def history_executions(self, symbol=None, start_at=None, end_at=None):
        return [{"symbol": symbol, "start_at": None if start_at is None else start_at.isoformat()}]

    def today_executions(self, symbol=None, order_id=None):
        return [{"symbol": symbol, "order_id": order_id}]

    def account_balance(self, currency=None):
        return [{"currency": currency or "USD"}]

    def stock_positions(self, symbols=None):
        return {"symbols": symbols}

    def cash_flow(self, start_at, end_at, business_type=None, symbol=None, page=None, size=None):
        return {
            "start_at": start_at.isoformat(),
            "end_at": end_at.isoformat(),
            "business_type": None if business_type is None else business_type.__name__,
            "symbol": symbol,
            "page": page,
            "size": size,
        }

    def fund_positions(self, symbols=None):
        return {"symbols": symbols}

    def history_orders(self, symbol=None, status=None, side=None, market=None, start_at=None, end_at=None):
        return {
            "symbol": symbol,
            "status": None if status is None else [str(item).split(".")[-1] for item in status],
            "side": None if side is None else str(side).split(".")[-1],
            "market": None if market is None else str(market).split(".")[-1],
        }

    def today_orders(self, symbol=None, status=None, side=None, market=None, order_id=None):
        return {
            "symbol": symbol,
            "status": None if status is None else [str(item).split(".")[-1] for item in status],
            "side": None if side is None else str(side).split(".")[-1],
            "market": None if market is None else str(market).split(".")[-1],
            "order_id": order_id,
        }

    def order_detail(self, order_id):
        return {"order_id": order_id}

    def margin_ratio(self, symbol):
        return {"symbol": symbol}

    def submit_order(self, *args):
        return {"args": list(args)}

    def cancel_order(self, order_id):
        return {"order_id": order_id}

    def replace_order(self, *args):
        return {"args": list(args)}


class FakeService:
    def __init__(self):
        self.quote_context = FakeQuoteContext()
        self.trade_context = FakeTradeContext()

    def call(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


def tool_names(server):
    return {tool.name for tool in asyncio.run(server.list_tools())}


def call_result(server, name, arguments):
    content, structured = asyncio.run(server.call_tool(name, arguments))
    assert content
    return structured["result"]


def test_default_server_is_read_only(monkeypatch):
    monkeypatch.delenv("LONGBRIDGE_MCP_READ_ONLY", raising=False)
    server = build_server(FakeService())
    names = tool_names(server)
    assert "quote-static-info" in names
    assert "trade-history-orders" in names
    assert "trade-submit-order" not in names


def test_read_only_false_registers_write_tools(monkeypatch):
    monkeypatch.setenv("LONGBRIDGE_MCP_READ_ONLY", "false")
    server = build_server(FakeService())
    names = tool_names(server)
    assert "trade-history-orders" in names
    assert "trade-submit-order" in names
    assert "quote-watch-list-delete-group" in names


def test_call_legacy_quote_tool(monkeypatch):
    server = build_server(FakeService())
    result = call_result(server, "quote-static-info", {"symbols": ["AAPL.US"]})
    assert result == [{"symbols": ["AAPL.US"], "kind": "static"}]


def test_call_extended_quote_tool(monkeypatch):
    server = build_server(FakeService())
    result = call_result(server, "quote-security-list", {"market": "us"})
    assert result == {"market": "US", "category": None}


def test_call_trade_read_tool(monkeypatch):
    server = build_server(FakeService())
    result = call_result(
        server,
        "trade-history-orders",
        {"statuses": ["filled"], "side": "buy", "market": "us"},
    )
    assert result == {"symbol": None, "status": ["Filled"], "side": "Buy", "market": "US"}


@pytest.mark.skipif(
    not all(os.getenv(name) for name in ("LONGBRIDGE_APP_KEY", "LONGBRIDGE_APP_SECRET", "LONGBRIDGE_ACCESS_TOKEN")),
    reason="Longbridge credentials not configured",
)
def test_live_smoke_import():
    server = build_server()
    assert "quote-static-info" in tool_names(server)
