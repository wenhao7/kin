from pathlib import Path

from kin.hermes_config import hermes_config_script

ROOT = Path(__file__).resolve().parents[1]


def test_template_renders_set_commands():
    script = hermes_config_script(ROOT / "hermes" / "config.yaml")
    assert "hermes config set model.provider nebius" in script
    assert "hermes config set stt.enabled false" in script
    assert "hermes config set memory.memory_enabled false" in script
    assert 'hermes config set agent.disabled_toolsets \'["terminal",' in script
    assert "session_search" in script and "hermes config unset mcp_servers" in script
    assert 'cp /seed/SOUL.md "$HERMES_HOME/SOUL.md"' in script
