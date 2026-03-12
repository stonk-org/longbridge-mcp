from __future__ import annotations

import os
from dataclasses import dataclass

from longbridge.openapi import Config


def _parse_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(
        "LONGBRIDGE_MCP_ENABLE_WRITE_TOOLS must be one of: true, false, 1, 0, yes, no, on, off"
    )


@dataclass(frozen=True)
class MCPSettings:
    enable_write_tools: bool = False


def load_settings(environ: dict[str, str] | None = None) -> MCPSettings:
    values = environ or os.environ
    return MCPSettings(
        enable_write_tools=_parse_bool(
            values.get("LONGBRIDGE_MCP_ENABLE_WRITE_TOOLS"),
            default=False,
        )
    )


def load_longbridge_config() -> Config:
    try:
        return Config.from_apikey_env()
    except Exception as exc:  # pragma: no cover - exact SDK exception type is binding-defined
        raise RuntimeError(
            "Failed to load Longbridge configuration from environment. "
            "Set LONGBRIDGE_APP_KEY, LONGBRIDGE_APP_SECRET, and LONGBRIDGE_ACCESS_TOKEN."
        ) from exc
