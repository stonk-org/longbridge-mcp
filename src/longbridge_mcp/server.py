from __future__ import annotations

from collections.abc import Callable
from typing import Any

from longbridge.openapi import QuoteContext, TradeContext
from mcp.server.fastmcp import FastMCP
from pydantic import ValidationError

from .config import load_longbridge_config, load_settings
from .serialize import serialize
from .validation import (
    AccountBalanceInput,
    CalcIndexesInput,
    CancelOrderInput,
    CashFlowInput,
    CreateWatchlistGroupInput,
    DeleteWatchlistGroupInput,
    HistoryCandlesticksInput,
    MarginRatioInput,
    MarketDateRangeInput,
    MarketInput,
    OptionalSymbolsInput,
    OptionChainInfoInput,
    OrderDetailInput,
    OrdersQueryInput,
    QuoteTradesInput,
    ReplaceOrderInput,
    SecurityListInput,
    SingleSymbolInput,
    SubmitOrderInput,
    SymbolListInput,
    TodayExecutionsInput,
    TodayOrdersInput,
    TradeHistoryExecutionsInput,
    TradingDaysInput,
    UpdateWatchlistGroupInput,
    WarrantListInput,
)


class LongbridgeService:
    def __init__(self) -> None:
        self._config = None
        self._quote_context: QuoteContext | None = None
        self._trade_context: TradeContext | None = None

    @property
    def config(self):
        if self._config is None:
            self._config = load_longbridge_config()
        return self._config

    @property
    def quote_context(self) -> QuoteContext:
        if self._quote_context is None:
            self._quote_context = QuoteContext(self.config)
        return self._quote_context

    @property
    def trade_context(self) -> TradeContext:
        if self._trade_context is None:
            self._trade_context = TradeContext(self.config)
        return self._trade_context

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return serialize(fn(*args, **kwargs))


StructuredResult = dict[str, object] | list[object] | str | int | float | bool | None


def _validated(model_cls: type[Any], **values: Any) -> Any:
    try:
        return model_cls(**values)
    except ValidationError as exc:
        raise ValueError(exc.errors(include_url=False)) from exc


def _register_tool(
    mcp: FastMCP,
    fn: Callable[..., Any],
    *,
    name: str,
    description: str,
) -> None:
    mcp.add_tool(
        fn,
        name=name,
        description=description,
        structured_output=True,
    )


def build_server(service: LongbridgeService | None = None) -> FastMCP:
    settings = load_settings()
    gateway = service or LongbridgeService()
    mcp = FastMCP(
        name="Longbridge",
        instructions=(
            "Longbridge OpenAPI MCP server. Quote tools are enabled by default. "
            "Set LONGBRIDGE_MCP_QUOTE_ONLY=false to enable trade and account tools."
        ),
    )

    def quote_static_info(symbols: list[str]) -> StructuredResult:
        params = _validated(SymbolListInput, symbols=symbols)
        return gateway.call(gateway.quote_context.static_info, params.symbols)

    def quote_realtime_info(symbols: list[str]) -> StructuredResult:
        params = _validated(SymbolListInput, symbols=symbols)
        return gateway.call(gateway.quote_context.quote, params.symbols)

    def quote_depth(symbol: str) -> StructuredResult:
        params = _validated(SingleSymbolInput, symbol=symbol)
        return gateway.call(gateway.quote_context.depth, params.symbol)

    def quote_trades(symbol: str, count: int) -> StructuredResult:
        params = _validated(QuoteTradesInput, symbol=symbol, count=count)
        return gateway.call(gateway.quote_context.trades, params.symbol, params.count)

    def quote_intraday(symbol: str) -> StructuredResult:
        params = _validated(SingleSymbolInput, symbol=symbol)
        return gateway.call(gateway.quote_context.intraday, params.symbol)

    def quote_history_candlesticks(
        symbol: str,
        period: str,
        query_type: str,
        adjust_type: str = "NoAdjust",
        start_date: str | None = None,
        end_date: str | None = None,
        forward: bool | None = None,
        count: int = 10,
        anchor_datetime: str | None = None,
    ) -> StructuredResult:
        params = _validated(
            HistoryCandlesticksInput,
            symbol=symbol,
            period=period,
            query_type=query_type,
            adjust_type=adjust_type,
            start_date=start_date,
            end_date=end_date,
            forward=forward,
            count=count,
            anchor_datetime=anchor_datetime,
        )
        if params.query_type == "by_date":
            return gateway.call(
                gateway.quote_context.history_candlesticks_by_date,
                params.symbol,
                params.sdk_period(),
                params.sdk_adjust_type(),
                params.start_date,
                params.end_date,
            )
        return gateway.call(
            gateway.quote_context.history_candlesticks_by_offset,
            params.symbol,
            params.sdk_period(),
            params.sdk_adjust_type(),
            params.forward,
            params.count,
            params.anchor_datetime,
        )

    def quote_capital_flow(symbol: str) -> StructuredResult:
        params = _validated(SingleSymbolInput, symbol=symbol)
        return gateway.call(gateway.quote_context.capital_flow, params.symbol)

    def quote_capital_distribution(symbol: str) -> StructuredResult:
        params = _validated(SingleSymbolInput, symbol=symbol)
        return gateway.call(gateway.quote_context.capital_distribution, params.symbol)

    def quote_calc_index(symbols: list[str], indexes: list[str]) -> StructuredResult:
        params = _validated(CalcIndexesInput, symbols=symbols, indexes=indexes)
        return gateway.call(gateway.quote_context.calc_indexes, params.symbols, params.sdk_indexes())

    def quote_watch_list() -> StructuredResult:
        return gateway.call(gateway.quote_context.watchlist)

    def quote_security_list(market: str, category: str | None = None) -> StructuredResult:
        params = _validated(SecurityListInput, market=market, category=category)
        return gateway.call(gateway.quote_context.security_list, params.sdk_market(), params.sdk_category())

    def quote_market_temperature(market: str) -> StructuredResult:
        params = _validated(MarketInput, market=market)
        return gateway.call(gateway.quote_context.market_temperature, params.sdk_market())

    def quote_history_market_temperature(market: str, start_date: str, end_date: str) -> StructuredResult:
        params = _validated(MarketDateRangeInput, market=market, start_date=start_date, end_date=end_date)
        return gateway.call(
            gateway.quote_context.history_market_temperature,
            params.sdk_market(),
            params.start_date,
            params.end_date,
        )

    def quote_trading_days(market: str, begin: str, end: str) -> StructuredResult:
        params = _validated(TradingDaysInput, market=market, begin=begin, end=end)
        return gateway.call(gateway.quote_context.trading_days, params.sdk_market(), params.begin, params.end)

    def quote_option_chain_expiry_dates(symbol: str) -> StructuredResult:
        params = _validated(SingleSymbolInput, symbol=symbol)
        return gateway.call(gateway.quote_context.option_chain_expiry_date_list, params.symbol)

    def quote_option_chain_info(symbol: str, expiry_date: str) -> StructuredResult:
        params = _validated(OptionChainInfoInput, symbol=symbol, expiry_date=expiry_date)
        return gateway.call(gateway.quote_context.option_chain_info_by_date, params.symbol, params.expiry_date)

    def quote_option_quote(symbols: list[str]) -> StructuredResult:
        params = _validated(SymbolListInput, symbols=symbols)
        return gateway.call(gateway.quote_context.option_quote, params.symbols)

    def quote_warrant_quote(symbols: list[str]) -> StructuredResult:
        params = _validated(SymbolListInput, symbols=symbols)
        return gateway.call(gateway.quote_context.warrant_quote, params.symbols)

    def quote_warrant_list(
        symbol: str,
        sort_by: str,
        sort_order: str,
        warrant_types: list[str] | None = None,
        issuer_ids: list[int] | None = None,
        expiry_dates: list[str] | None = None,
        price_types: list[str] | None = None,
        statuses: list[str] | None = None,
    ) -> StructuredResult:
        params = _validated(
            WarrantListInput,
            symbol=symbol,
            sort_by=sort_by,
            sort_order=sort_order,
            warrant_types=warrant_types,
            issuer_ids=issuer_ids,
            expiry_dates=expiry_dates,
            price_types=price_types,
            statuses=statuses,
        )
        return gateway.call(
            gateway.quote_context.warrant_list,
            params.symbol,
            params.sdk_sort_by(),
            params.sdk_sort_order(),
            params.sdk_warrant_types(),
            params.issuer_ids,
            params.sdk_expiry_dates(),
            params.sdk_price_types(),
            params.sdk_statuses(),
        )

    def quote_brokers(symbol: str) -> StructuredResult:
        params = _validated(SingleSymbolInput, symbol=symbol)
        return gateway.call(gateway.quote_context.brokers, params.symbol)

    def quote_participants() -> StructuredResult:
        return gateway.call(gateway.quote_context.participants)

    def quote_level() -> StructuredResult:
        return gateway.call(gateway.quote_context.quote_level)

    def quote_package_details() -> StructuredResult:
        return gateway.call(gateway.quote_context.quote_package_details)

    def trade_history_executions(
        symbol: str | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
    ) -> StructuredResult:
        params = _validated(TradeHistoryExecutionsInput, symbol=symbol, start_at=start_at, end_at=end_at)
        return gateway.call(
            gateway.trade_context.history_executions,
            params.symbol,
            params.start_at,
            params.end_at,
        )

    def trade_today_executions(symbol: str | None = None, order_id: str | None = None) -> StructuredResult:
        params = _validated(TodayExecutionsInput, symbol=symbol, order_id=order_id)
        return gateway.call(gateway.trade_context.today_executions, params.symbol, params.order_id)

    def trade_account_balance(currency: str | None = None) -> StructuredResult:
        params = _validated(AccountBalanceInput, currency=currency)
        return gateway.call(gateway.trade_context.account_balance, params.currency)

    def trade_stock_positions(symbols: list[str] | None = None) -> StructuredResult:
        params = _validated(OptionalSymbolsInput, symbols=symbols)
        return gateway.call(gateway.trade_context.stock_positions, params.symbols)

    def trade_cash_flow(
        start_at: str,
        end_at: str,
        business_type: str | None = None,
        symbol: str | None = None,
        page: int | None = None,
        size: int | None = None,
    ) -> StructuredResult:
        params = _validated(
            CashFlowInput,
            start_at=start_at,
            end_at=end_at,
            business_type=business_type,
            symbol=symbol,
            page=page,
            size=size,
        )
        return gateway.call(
            gateway.trade_context.cash_flow,
            params.start_at,
            params.end_at,
            params.sdk_business_type(),
            params.symbol,
            params.page,
            params.size,
        )

    def trade_fund_positions(symbols: list[str] | None = None) -> StructuredResult:
        params = _validated(OptionalSymbolsInput, symbols=symbols)
        return gateway.call(gateway.trade_context.fund_positions, params.symbols)

    def trade_history_orders(
        symbol: str | None = None,
        statuses: list[str] | None = None,
        side: str | None = None,
        market: str | None = None,
        start_at: str | None = None,
        end_at: str | None = None,
    ) -> StructuredResult:
        params = _validated(
            OrdersQueryInput,
            symbol=symbol,
            statuses=statuses,
            side=side,
            market=market,
            start_at=start_at,
            end_at=end_at,
        )
        return gateway.call(
            gateway.trade_context.history_orders,
            params.symbol,
            params.sdk_statuses(),
            params.sdk_side(),
            params.sdk_market(),
            params.start_at,
            params.end_at,
        )

    def trade_today_orders(
        symbol: str | None = None,
        statuses: list[str] | None = None,
        side: str | None = None,
        market: str | None = None,
        order_id: str | None = None,
    ) -> StructuredResult:
        params = _validated(
            TodayOrdersInput,
            symbol=symbol,
            statuses=statuses,
            side=side,
            market=market,
            order_id=order_id,
        )
        return gateway.call(
            gateway.trade_context.today_orders,
            params.symbol,
            params.sdk_statuses(),
            params.sdk_side(),
            params.sdk_market(),
            params.order_id,
        )

    def trade_order_detail(order_id: str) -> StructuredResult:
        params = _validated(OrderDetailInput, order_id=order_id)
        return gateway.call(gateway.trade_context.order_detail, params.order_id)

    def trade_margin_ratio(symbol: str) -> StructuredResult:
        params = _validated(MarginRatioInput, symbol=symbol)
        return gateway.call(gateway.trade_context.margin_ratio, params.symbol)

    quote_tools = [
        ("quote-static-info", "Get basic information for one or more securities.", quote_static_info),
        ("quote-realtime-info", "Get real-time quotes for one or more securities.", quote_realtime_info),
        ("quote-depth", "Get order book depth for a security.", quote_depth),
        ("quote-trades", "Get recent trades for a security.", quote_trades),
        ("quote-intraday", "Get intraday line data for a security.", quote_intraday),
        ("quote-history-candlesticks", "Get historical candlesticks by date range or offset.", quote_history_candlesticks),
        ("quote-capital-flow", "Get intraday capital flow for a security.", quote_capital_flow),
        ("quote-capital-distribution", "Get capital distribution for a security.", quote_capital_distribution),
        ("quote-calc-index", "Calculate quote indexes for one or more securities.", quote_calc_index),
        ("quote-watch-list", "Get watch list groups.", quote_watch_list),
        ("quote-security-list", "Get the market security list.", quote_security_list),
        ("quote-market-temperature", "Get current market temperature.", quote_market_temperature),
        ("quote-history-market-temperature", "Get historical market temperature.", quote_history_market_temperature),
        ("quote-trading-days", "Get trading days for a market date range.", quote_trading_days),
        ("quote-option-chain-expiry-dates", "Get option expiry dates for an underlying symbol.", quote_option_chain_expiry_dates),
        ("quote-option-chain-info", "Get option chain details for a symbol and expiry date.", quote_option_chain_info),
        ("quote-option-quote", "Get option quotes.", quote_option_quote),
        ("quote-warrant-quote", "Get warrant quotes.", quote_warrant_quote),
        ("quote-warrant-list", "Get warrant list results for an underlying symbol.", quote_warrant_list),
        ("quote-brokers", "Get brokers for a security.", quote_brokers),
        ("quote-participants", "Get market participants.", quote_participants),
        ("quote-level", "Get your quote level.", quote_level),
        ("quote-package-details", "Get quote package details.", quote_package_details),
    ]

    trade_tools = [
        ("trade-history-executions", "Get historical executions.", trade_history_executions),
        ("trade-today-executions", "Get today's executions.", trade_today_executions),
        ("trade-account-balance", "Get account balance.", trade_account_balance),
        ("trade-stock-positions", "Get stock positions.", trade_stock_positions),
        ("trade-cash-flow", "Get cash flow records.", trade_cash_flow),
        ("trade-fund-positions", "Get fund positions.", trade_fund_positions),
        ("trade-history-orders", "Get historical orders.", trade_history_orders),
        ("trade-today-orders", "Get today's orders.", trade_today_orders),
        ("trade-order-detail", "Get order details.", trade_order_detail),
        ("trade-margin-ratio", "Get margin ratio for a symbol.", trade_margin_ratio),
    ]

    for name, description, fn in quote_tools:
        _register_tool(mcp, fn, name=name, description=description)

    if not settings.quote_only:
        for name, description, fn in trade_tools:
            _register_tool(mcp, fn, name=name, description=description)

    if not settings.quote_only:
        def trade_submit_order(
            symbol: str,
            order_type: str,
            side: str,
            submitted_quantity: str,
            time_in_force: str,
            submitted_price: str | None = None,
            trigger_price: str | None = None,
            limit_offset: str | None = None,
            trailing_amount: str | None = None,
            trailing_percent: str | None = None,
            expire_date: str | None = None,
            outside_rth: str | None = None,
            limit_depth_level: int | None = None,
            trigger_count: int | None = None,
            monitor_price: str | None = None,
            remark: str | None = None,
        ) -> StructuredResult:
            params = _validated(
                SubmitOrderInput,
                symbol=symbol,
                order_type=order_type,
                side=side,
                submitted_quantity=submitted_quantity,
                time_in_force=time_in_force,
                submitted_price=submitted_price,
                trigger_price=trigger_price,
                limit_offset=limit_offset,
                trailing_amount=trailing_amount,
                trailing_percent=trailing_percent,
                expire_date=expire_date,
                outside_rth=outside_rth,
                limit_depth_level=limit_depth_level,
                trigger_count=trigger_count,
                monitor_price=monitor_price,
                remark=remark,
            )
            return gateway.call(
                gateway.trade_context.submit_order,
                params.symbol,
                params.sdk_order_type(),
                params.sdk_side(),
                params.submitted_quantity,
                params.sdk_time_in_force(),
                params.submitted_price,
                params.trigger_price,
                params.limit_offset,
                params.trailing_amount,
                params.trailing_percent,
                params.expire_date,
                params.sdk_outside_rth(),
                params.limit_depth_level,
                params.trigger_count,
                params.monitor_price,
                params.remark,
            )

        def trade_cancel_order(order_id: str) -> StructuredResult:
            params = _validated(CancelOrderInput, order_id=order_id)
            return gateway.call(gateway.trade_context.cancel_order, params.order_id)

        def trade_replace_order(
            order_id: str,
            quantity: str,
            price: str | None = None,
            trigger_price: str | None = None,
            limit_offset: str | None = None,
            trailing_amount: str | None = None,
            trailing_percent: str | None = None,
            limit_depth_level: int | None = None,
            trigger_count: int | None = None,
            monitor_price: str | None = None,
            remark: str | None = None,
        ) -> StructuredResult:
            params = _validated(
                ReplaceOrderInput,
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                limit_offset=limit_offset,
                trailing_amount=trailing_amount,
                trailing_percent=trailing_percent,
                limit_depth_level=limit_depth_level,
                trigger_count=trigger_count,
                monitor_price=monitor_price,
                remark=remark,
            )
            return gateway.call(
                gateway.trade_context.replace_order,
                params.order_id,
                params.quantity,
                params.price,
                params.trigger_price,
                params.limit_offset,
                params.trailing_amount,
                params.trailing_percent,
                params.limit_depth_level,
                params.trigger_count,
                params.monitor_price,
                params.remark,
            )

        def quote_watch_list_create_group(name: str, securities: list[str] | None = None) -> StructuredResult:
            params = _validated(CreateWatchlistGroupInput, name=name, securities=securities)
            return gateway.call(gateway.quote_context.create_watchlist_group, params.name, params.securities)

        def quote_watch_list_update_group(
            id: int,
            name: str | None = None,
            securities: list[str] | None = None,
            mode: str | None = None,
        ) -> StructuredResult:
            params = _validated(
                UpdateWatchlistGroupInput,
                id=id,
                name=name,
                securities=securities,
                mode=mode,
            )
            return gateway.call(
                gateway.quote_context.update_watchlist_group,
                params.id,
                params.name,
                params.securities,
                params.sdk_mode(),
            )

        def quote_watch_list_delete_group(id: int, purge: bool = False) -> StructuredResult:
            params = _validated(DeleteWatchlistGroupInput, id=id, purge=purge)
            return gateway.call(gateway.quote_context.delete_watchlist_group, params.id, params.purge)

        write_tools = [
            ("trade-submit-order", "Submit a trade order.", trade_submit_order),
            ("trade-cancel-order", "Cancel a trade order.", trade_cancel_order),
            ("trade-replace-order", "Replace a trade order.", trade_replace_order),
            ("quote-watch-list-create-group", "Create a watch list group.", quote_watch_list_create_group),
            ("quote-watch-list-update-group", "Update a watch list group.", quote_watch_list_update_group),
            ("quote-watch-list-delete-group", "Delete a watch list group.", quote_watch_list_delete_group),
        ]
        for name, description, fn in write_tools:
            _register_tool(mcp, fn, name=name, description=description)

    return mcp


def main() -> None:
    build_server().run(transport="stdio")
