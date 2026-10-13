from kin.config import Settings


def test_defaults_and_missing(monkeypatch):
    for var in ("NEBIUS_API_KEY", "TELEGRAM_BOT_TOKEN", "TAVILY_API_KEY"):
        monkeypatch.delenv(var, raising=False)
    s = Settings(_env_file=None)
    assert s.locale == "sg"
    # Hackathon hard requirement: an NVIDIA open model in the product path.
    assert s.model_nano.startswith("nvidia/") and s.model_super.startswith("nvidia/")
    assert s.models["vision"] == s.model_vision
    assert set(s.missing_required()) == {"NEBIUS_API_KEY", "TELEGRAM_BOT_TOKEN", "TAVILY_API_KEY"}


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TAVILY_API_KEY", "v")
    monkeypatch.setenv("KIN_API_PORT", "9000")
    s = Settings(_env_file=None)
    assert s.api_port == 9000
    assert s.missing_required() == []
