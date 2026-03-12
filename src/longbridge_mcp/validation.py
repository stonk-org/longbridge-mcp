from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import re
from typing import Any, Literal

from longbridge.openapi import (
    AdjustType,
    BalanceType,
    CalcIndex,
    FilterWarrantExpiryDate,
    FilterWarrantInOutBoundsType,
    Market,
    OrderSide,
    OrderStatus,
    OrderType,
    OutsideRTH,
    Period,
    SecuritiesUpdateMode,
    SecurityListCategory,
    SortOrderType,
    TimeInForceType,
    WarrantSortBy,
    WarrantStatus,
    WarrantType,
)
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SYMBOL_RE = re.compile(r"^[A-Z0-9]+(?:\.[A-Z]+)+$")


def normalize_name(value: str) -> str:
    return re.sub(r"[\s_\-]+", "", value).lower()


def enum_members(enum_cls: type[Any]) -> dict[str, Any]:
    members: dict[str, Any] = {}
    for name in dir(enum_cls):
        if name.startswith("_"):
            continue
        attr = getattr(enum_cls, name)
        if isinstance(attr, enum_cls):
            members[name] = attr
    return members


def map_enum(enum_cls: type[Any], value: str, *, aliases: dict[str, str] | None = None) -> Any:
    members = enum_members(enum_cls)
    if value in members:
        return members[value]
    normalized = normalize_name(value)
    for name, member in members.items():
        if normalize_name(name) == normalized:
            return member
    if aliases:
        alias_target = aliases.get(normalized)
        if alias_target and alias_target in members:
            return members[alias_target]
    valid = ", ".join(sorted(members))
    raise ValueError(f"Invalid value {value!r}. Expected one of: {valid}")


def map_enums(enum_cls: type[Any], values: list[str] | None, *, aliases: dict[str, str] | None = None) -> list[Any] | None:
    if values is None:
        return None
    return [map_enum(enum_cls, value, aliases=aliases) for value in values]


def validate_symbol(symbol: str) -> str:
    if not SYMBOL_RE.fullmatch(symbol):
        raise ValueError('Symbol must look like "AAPL.US"')
    return symbol


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SymbolListInput(Model):
    symbols: list[str] = Field(min_length=1, max_length=500)

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: list[str]) -> list[str]:
        return [validate_symbol(item) for item in value]


class SingleSymbolInput(Model):
    symbol: str

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str) -> str:
        return validate_symbol(value)


class QuoteTradesInput(SingleSymbolInput):
    count: int = Field(ge=1, le=1000)


class HistoryCandlesticksInput(SingleSymbolInput):
    period: str
    adjust_type: str = "NoAdjust"
    query_type: Literal["by_offset", "by_date"]
    start_date: date | None = None
    end_date: date | None = None
    forward: bool | None = None
    count: int = Field(default=10, ge=1, le=1000)
    anchor_datetime: datetime | None = None

    @model_validator(mode="after")
    def _validate_query_mode(self) -> "HistoryCandlesticksInput":
        if self.query_type == "by_date":
            if not self.start_date or not self.end_date:
                raise ValueError("start_date and end_date are required when query_type='by_date'")
        else:
            if self.forward is None:
                raise ValueError("forward is required when query_type='by_offset'")
        return self

    def sdk_period(self) -> Any:
        return map_enum(
            Period,
            self.period,
            aliases={
                "1m": "Min_1",
                "2m": "Min_2",
                "3m": "Min_3",
                "5m": "Min_5",
                "10m": "Min_10",
                "15m": "Min_15",
                "20m": "Min_20",
                "30m": "Min_30",
                "45m": "Min_45",
                "60m": "Min_60",
                "120m": "Min_120",
                "180m": "Min_180",
                "240m": "Min_240",
            },
        )

    def sdk_adjust_type(self) -> Any:
        return map_enum(
            AdjustType,
            self.adjust_type,
            aliases={"noadjust": "NoAdjust", "forwardadjust": "ForwardAdjust"},
        )


class CalcIndexesInput(SymbolListInput):
    indexes: list[str] = Field(min_length=1)

    def sdk_indexes(self) -> list[Any]:
        return map_enums(CalcIndex, self.indexes)


class SecurityListInput(Model):
    market: str
    category: str | None = None

    def sdk_market(self) -> Any:
        return map_enum(Market, self.market)

    def sdk_category(self) -> Any:
        if self.category is None:
            return None
        return map_enum(SecurityListCategory, self.category)


class MarketInput(Model):
    market: str

    def sdk_market(self) -> Any:
        return map_enum(Market, self.market)


class MarketDateRangeInput(MarketInput):
    start_date: date
    end_date: date


class TradingDaysInput(MarketInput):
    begin: date
    end: date


class OptionChainInfoInput(SingleSymbolInput):
    expiry_date: date


class WarrantListInput(SingleSymbolInput):
    sort_by: str
    sort_order: str
    warrant_types: list[str] | None = None
    issuer_ids: list[int] | None = None
    expiry_dates: list[str] | None = None
    price_types: list[str] | None = None
    statuses: list[str] | None = None

    def sdk_sort_by(self) -> Any:
        return map_enum(WarrantSortBy, self.sort_by)

    def sdk_sort_order(self) -> Any:
        return map_enum(SortOrderType, self.sort_order)

    def sdk_warrant_types(self) -> list[Any] | None:
        return map_enums(WarrantType, self.warrant_types)

    def sdk_expiry_dates(self) -> list[Any] | None:
        return map_enums(FilterWarrantExpiryDate, self.expiry_dates)

    def sdk_price_types(self) -> list[Any] | None:
        return map_enums(FilterWarrantInOutBoundsType, self.price_types)

    def sdk_statuses(self) -> list[Any] | None:
        return map_enums(WarrantStatus, self.statuses)


class TradeHistoryExecutionsInput(Model):
    symbol: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_symbol(value)


class TodayExecutionsInput(Model):
    symbol: str | None = None
    order_id: str | None = None

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_symbol(value)


class AccountBalanceInput(Model):
    currency: str | None = None


class OptionalSymbolsInput(Model):
    symbols: list[str] | None = Field(default=None, max_length=500)

    @field_validator("symbols")
    @classmethod
    def _validate_symbols(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return [validate_symbol(item) for item in value]


class CashFlowInput(Model):
    start_at: datetime
    end_at: datetime
    business_type: str | None = None
    symbol: str | None = None
    page: int | None = Field(default=None, ge=1)
    size: int | None = Field(default=None, ge=1, le=200)

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_symbol(value)

    def sdk_business_type(self) -> Any:
        if self.business_type is None:
            return None
        return map_enum(BalanceType, self.business_type)


class OrdersQueryInput(Model):
    symbol: str | None = None
    statuses: list[str] | None = None
    side: str | None = None
    market: str | None = None
    start_at: datetime | None = None
    end_at: datetime | None = None

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return validate_symbol(value)

    def sdk_statuses(self) -> list[Any] | None:
        return map_enums(OrderStatus, self.statuses)

    def sdk_side(self) -> Any:
        if self.side is None:
            return None
        return map_enum(OrderSide, self.side)

    def sdk_market(self) -> Any:
        if self.market is None:
            return None
        return map_enum(Market, self.market)


class TodayOrdersInput(OrdersQueryInput):
    order_id: str | None = None


class OrderDetailInput(Model):
    order_id: str


class MarginRatioInput(SingleSymbolInput):
    pass


class SubmitOrderInput(Model):
    symbol: str
    order_type: str
    side: str
    submitted_quantity: Decimal
    time_in_force: str
    submitted_price: Decimal | None = None
    trigger_price: Decimal | None = None
    limit_offset: Decimal | None = None
    trailing_amount: Decimal | None = None
    trailing_percent: Decimal | None = None
    expire_date: date | None = None
    outside_rth: str | None = None
    limit_depth_level: int | None = None
    trigger_count: int | None = None
    monitor_price: Decimal | None = None
    remark: str | None = None

    @field_validator("symbol")
    @classmethod
    def _validate_symbol(cls, value: str) -> str:
        return validate_symbol(value)

    def sdk_order_type(self) -> Any:
        return map_enum(OrderType, self.order_type)

    def sdk_side(self) -> Any:
        return map_enum(OrderSide, self.side)

    def sdk_time_in_force(self) -> Any:
        return map_enum(TimeInForceType, self.time_in_force)

    def sdk_outside_rth(self) -> Any:
        if self.outside_rth is None:
            return None
        return map_enum(OutsideRTH, self.outside_rth)


class CancelOrderInput(Model):
    order_id: str


class ReplaceOrderInput(Model):
    order_id: str
    quantity: Decimal
    price: Decimal | None = None
    trigger_price: Decimal | None = None
    limit_offset: Decimal | None = None
    trailing_amount: Decimal | None = None
    trailing_percent: Decimal | None = None
    limit_depth_level: int | None = None
    trigger_count: int | None = None
    monitor_price: Decimal | None = None
    remark: str | None = None


class CreateWatchlistGroupInput(Model):
    name: str
    securities: list[str] | None = None

    @field_validator("securities")
    @classmethod
    def _validate_securities(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value
        return [validate_symbol(item) for item in value]


class UpdateWatchlistGroupInput(CreateWatchlistGroupInput):
    id: int
    name: str | None = None
    mode: str | None = None

    def sdk_mode(self) -> Any:
        if self.mode is None:
            return None
        return map_enum(SecuritiesUpdateMode, self.mode)


class DeleteWatchlistGroupInput(Model):
    id: int
    purge: bool = False
