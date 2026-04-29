"""Shared test fixtures."""
from __future__ import annotations

import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock
from typing import Any

import pytest

# Ensure backend is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from denon.telnet_client import DenonTelnetClient


@pytest.fixture
def telnet_client():
    """Create a DenonTelnetClient with mocked connection (no real network)."""
    client = DenonTelnetClient("192.168.1.100", 23)
    # Simulate connected state without actually connecting
    client._connected = True
    client._writer = MagicMock()
    client._writer.write = MagicMock()
    client._writer.drain = AsyncMock()
    client._writer.close = MagicMock()
    client._writer.wait_closed = AsyncMock()
    return client


@pytest.fixture
def mock_state() -> dict[str, Any]:
    """Default receiver state for tests."""
    return {
        "power": True,
        "volume": 50.0,
        "volume_max": 98.0,
        "muted": False,
        "source": "GAME",
        "surround_mode": "DOLBY SURROUND",
        "channel_volumes": {"FL": 50, "FR": 50, "C": 48, "SW": 52},
        "tone_control": True,
        "bass": 50,
        "treble": 50,
        "subwoofer_level": 50,
        "subwoofer2_level": None,
        "dialog_level": None,
        "dialog_level_enabled": None,
        "multeq": "AUDYSSEY",
        "dynamic_eq": True,
        "dynamic_volume": "OFF",
        "ref_level_offset": None,
        "sleep_timer": None,
        "eco_mode": "AUTO",
        "sound_decoder": "AUTO",
        "surround_mode_list": [],
        "z2_power": False,
        "z2_volume": None,
        "z2_muted": None,
        "z2_source": None,
    }
