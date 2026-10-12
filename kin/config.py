"""Settings loaded from the environment and `.env` (pydantic-settings)."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

TOKEN_FACTORY_BASE_URL = "https://api.tokenfactory.nebius.com/v1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Nebius
    nebius_api_key: SecretStr = Field(default=SecretStr(""), alias="NEBIUS_API_KEY")
    nebius_base_url: str = Field(default=TOKEN_FACTORY_BASE_URL, alias="NEBIUS_BASE_URL")

    # Third parties
    tavily_api_key: SecretStr = Field(default=SecretStr(""), alias="TAVILY_API_KEY")
    telegram_bot_token: SecretStr = Field(default=SecretStr(""), alias="TELEGRAM_BOT_TOKEN")
    admin_telegram_id: str = Field(default="", alias="KIN_ADMIN_TELEGRAM_ID")

    # Models (Token Factory IDs). Vision: photo/document extraction. Nemotron 3 Nano Omni is not in
    # the public Token Factory catalog for our key, so a Token Factory vision model stands in
    # (docs/05-architecture.md, "Vision fallback"); set KIN_MODEL_VISION to the Omni ID once listed.
    model_vision: str = Field(default="openbmb/MiniCPM-V-4_5", alias="KIN_MODEL_VISION")
    model_nano: str = Field(default="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B", alias="KIN_MODEL_NANO")
    model_super: str = Field(default="nvidia/nemotron-3-super-120b-a12b", alias="KIN_MODEL_SUPER")
    model_ultra: str = Field(default="nvidia/Nemotron-3-Ultra-550b-a55b", alias="KIN_MODEL_ULTRA")
    ultra_max_calls: int = Field(default=2, alias="KIN_ULTRA_MAX_CALLS")

    # Service
    data_dir: Path = Field(default=Path("./data"), alias="KIN_DATA_DIR")
    locale: str = Field(default="sg", alias="KIN_LOCALE")
    policy_file: Path = Field(default=Path("./config/policy.yaml"), alias="KIN_POLICY_FILE")
    mcp_host: str = Field(default="0.0.0.0", alias="KIN_MCP_HOST")
    mcp_port: int = Field(default=8765, alias="KIN_MCP_PORT")

    @property
    def models(self) -> dict[str, str]:
        return {
            "vision": self.model_vision,
            "nano": self.model_nano,
            "super": self.model_super,
            "ultra": self.model_ultra,
        }

    @property
    def locale_file(self) -> Path:
        return Path("locale") / self.locale / "locale.yaml"

    def missing_required(self) -> list[str]:
        missing = []
        if not self.nebius_api_key.get_secret_value():
            missing.append("NEBIUS_API_KEY")
        if not self.telegram_bot_token.get_secret_value():
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.tavily_api_key.get_secret_value():
            missing.append("TAVILY_API_KEY")
        return missing


def get_settings() -> Settings:
    return Settings()
