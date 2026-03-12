from longbridge_mcp.config import load_settings


def test_load_settings_defaults_to_read_only():
    settings = load_settings({})
    assert settings.enable_write_tools is False


def test_load_settings_parses_true():
    settings = load_settings({"LONGBRIDGE_MCP_ENABLE_WRITE_TOOLS": "true"})
    assert settings.enable_write_tools is True
