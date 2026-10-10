from kin.config import Settings


def test_defaults_and_missing(monkeypatch):
    for var in ("NEBIUS_API_KEY", "TELEGRAM_BOT_TOKEN", "TAVILY_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.locale == "sg"
    assert s.model_omni.startswith("nvidia/")
    assert set(s.missing_required()) == {"NEBIUS_API_KEY", "TELEGRAM_BOT_TOKEN", "TAVILY_API_KEY"}


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TAVILY_API_KEY", "v")
    monkeypatch.setenv("KIN_MCP_PORT", "9000")
    s = Settings(_env_file=None)
    assert s.mcp_port == 9000
    assert s.missing_required() == []
