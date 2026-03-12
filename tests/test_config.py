from longbridge_mcp.config import load_settings


def test_load_settings_defaults_to_read_only():
    settings = load_settings({})
    assert settings.read_only is True


def test_load_settings_parses_read_only_false():
    settings = load_settings({"LONGBRIDGE_MCP_READ_ONLY": "false"})
    assert settings.read_only is False
