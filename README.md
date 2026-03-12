# longbridge-mcp

Python MCP server for Longbridge OpenAPI, designed to run with `uvx`.

## Requirements

- `uv`
- Longbridge OpenAPI credentials using only the `LONGBRIDGE_*` prefix

## Environment

Required:

- `LONGBRIDGE_APP_KEY`
- `LONGBRIDGE_APP_SECRET`
- `LONGBRIDGE_ACCESS_TOKEN`

Optional Longbridge SDK passthrough:

- `LONGBRIDGE_LANGUAGE`
- `LONGBRIDGE_HTTP_URL`
- `LONGBRIDGE_QUOTE_WS_URL`
- `LONGBRIDGE_TRADE_WS_URL`
- `LONGBRIDGE_ENABLE_OVERNIGHT`
- `LONGBRIDGE_PUSH_CANDLESTICK_MODE`
- `LONGBRIDGE_PRINT_QUOTE_PACKAGES`
- `LONGBRIDGE_LOG_PATH`

Server safety switch:

- `LONGBRIDGE_MCP_QUOTE_ONLY=true` by default

## Usage

Run from PyPI:

```bash
uvx longbridge-mcp
```

Run locally from this repo during development:

```bash
uvx --from . longbridge-mcp
```

For an MCP client configuration:

```json
{
  "mcpServers": {
    "longbridge": {
      "command": "uvx",
      "args": ["longbridge-mcp"],
      "env": {
        "LONGBRIDGE_APP_KEY": "your-app-key",
        "LONGBRIDGE_APP_SECRET": "your-app-secret",
        "LONGBRIDGE_ACCESS_TOKEN": "your-access-token",
        "LONGBRIDGE_MCP_QUOTE_ONLY": "true"
      }
    }
  }
}
```

## Tool Surface

Quote tools always available by default:

- `quote-static-info`
- `quote-realtime-info`
- `quote-depth`
- `quote-trades`
- `quote-intraday`
- `quote-history-candlesticks`
- `quote-capital-flow`
- `quote-capital-distribution`
- `quote-calc-index`
- `quote-watch-list`
- `quote-security-list`
- `quote-market-temperature`
- `quote-history-market-temperature`
- `quote-trading-days`
- `quote-option-chain-expiry-dates`
- `quote-option-chain-info`
- `quote-option-quote`
- `quote-warrant-quote`
- `quote-warrant-list`
- `quote-brokers`
- `quote-participants`
- `quote-level`
- `quote-package-details`

Trade read tools are only registered when `LONGBRIDGE_MCP_QUOTE_ONLY=false`:

- `trade-history-executions`
- `trade-today-executions`
- `trade-account-balance`
- `trade-stock-positions`
- `trade-cash-flow`
- `trade-fund-positions`
- `trade-history-orders`
- `trade-today-orders`
- `trade-order-detail`
- `trade-margin-ratio`

Write tools are also registered when `LONGBRIDGE_MCP_QUOTE_ONLY=false`:

- `trade-submit-order`
- `trade-cancel-order`
- `trade-replace-order`
- `quote-watch-list-create-group`
- `quote-watch-list-update-group`
- `quote-watch-list-delete-group`

## Notes

- Transport is stdio only.
- Output is structured JSON-like tool data, not text-wrapped JSON blobs.
- OAuth and push streaming are intentionally out of scope for this version.
