"""Application configuration via environment variables."""
from __future__ import annotations

import json
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Required: receiver IP
    denon_host: str = "192.168.1.100"
    denon_telnet_port: int = 23

    # Optional display names (auto-detected via telnet if not set)
    denon_device_name: str = "Denon AVR"
    denon_zone1_name: str = "Main Zone"
    denon_zone2_name: str = "Zone 2"

    # Custom source names as JSON: {"GAME":"NintendoSwitch","BD":"FireTV"}
    denon_source_names: str = "{}"

    log_level: str = "INFO"

    @property
    def source_name_map(self) -> dict[str, str]:
        try:
            return json.loads(self.denon_source_names)
        except (json.JSONDecodeError, TypeError):
            return {}

    model_config = {"env_prefix": "DENON_DASHBOARD_", "env_file": ".env"}


settings = Settings()
