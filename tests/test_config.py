from longbridge_mcp.config import load_settings


def test_load_settings_defaults_to_quote_only():
    settings = load_settings({})
    assert settings.quote_only is True


def test_load_settings_parses_quote_only_false():
    settings = load_settings({"LONGBRIDGE_MCP_QUOTE_ONLY": "false"})
    assert settings.quote_only is False
