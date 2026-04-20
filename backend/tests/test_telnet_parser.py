"""Tests for DenonTelnetClient._parse() — telnet protocol parser."""
from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Power ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_power_on(telnet_client):
    """ZMON → power = True."""
    await telnet_client._parse("ZMON")
    assert telnet_client.state["power"] is True


@pytest.mark.asyncio
async def test_parse_power_off(telnet_client):
    """ZMOFF → power = False."""
    await telnet_client._parse("ZMOFF")
    assert telnet_client.state["power"] is False


@pytest.mark.asyncio
async def test_parse_system_standby(telnet_client):
    """PWSTANDBY → power = False."""
    await telnet_client._parse("PWSTANDBY")
    assert telnet_client.state["power"] is False


@pytest.mark.asyncio
async def test_parse_pwon_does_not_set_power(telnet_client):
    """PWON alone should NOT set power=True (use ZM for main zone)."""
    telnet_client.state["power"] = None
    await telnet_client._parse("PWON")
    assert telnet_client.state["power"] is None  # unchanged


# ── Volume ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_volume_integer(telnet_client):
    """MV50 → volume = 50.0."""
    await telnet_client._parse("MV50")
    assert telnet_client.state["volume"] == 50.0


@pytest.mark.asyncio
async def test_parse_volume_half_step(telnet_client):
    """MV505 → volume = 50.5."""
    await telnet_client._parse("MV505")
    assert telnet_client.state["volume"] == 50.5


@pytest.mark.asyncio
async def test_parse_volume_max(telnet_client):
    """MVMAX 80 → volume_max = 80.0."""
    await telnet_client._parse("MVMAX 80")
    assert telnet_client.state["volume_max"] == 80.0


# ── Mute ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_mute_on(telnet_client):
    await telnet_client._parse("MUON")
    assert telnet_client.state["muted"] is True


@pytest.mark.asyncio
async def test_parse_mute_off(telnet_client):
    await telnet_client._parse("MUOFF")
    assert telnet_client.state["muted"] is False


# ── Source ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_source(telnet_client):
    """SIGAME → source = 'GAME'."""
    await telnet_client._parse("SIGAME")
    assert telnet_client.state["source"] == "GAME"


@pytest.mark.asyncio
async def test_parse_source_tv(telnet_client):
    """SITV → source = 'TV'."""
    await telnet_client._parse("SITV")
    assert telnet_client.state["source"] == "TV"


# ── Surround ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_surround(telnet_client):
    """MSDOLBY SURROUND → surround_mode = 'DOLBY SURROUND'."""
    await telnet_client._parse("MSDOLBY SURROUND")
    assert telnet_client.state["surround_mode"] == "DOLBY SURROUND"


# ── Channel Volume ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_channel_volume(telnet_client):
    """CVFL 50 → channel_volumes['FL'] = 50."""
    await telnet_client._parse("CVFL 50")
    assert telnet_client.state["channel_volumes"]["FL"] == 50


@pytest.mark.asyncio
async def test_parse_channel_volume_unknown_channel(telnet_client):
    """Unknown channels should be ignored."""
    await telnet_client._parse("CVXYZ 50")
    assert "XYZ" not in telnet_client.state["channel_volumes"]


@pytest.mark.asyncio
async def test_parse_cvend_ignored(telnet_client):
    """CVEND should not crash."""
    await telnet_client._parse("CVEND")


# ── Tone ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_tone_control_on(telnet_client):
    await telnet_client._parse("PSTONE CTRL ON")
    assert telnet_client.state["tone_control"] is True


@pytest.mark.asyncio
async def test_parse_tone_control_off(telnet_client):
    await telnet_client._parse("PSTONE CTRL OFF")
    assert telnet_client.state["tone_control"] is False


@pytest.mark.asyncio
async def test_parse_bass(telnet_client):
    await telnet_client._parse("PSBAS 52")
    assert telnet_client.state["bass"] == 52


@pytest.mark.asyncio
async def test_parse_treble(telnet_client):
    await telnet_client._parse("PSTRE 48")
    assert telnet_client.state["treble"] == 48


# ── Subwoofer ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_subwoofer_level(telnet_client):
    await telnet_client._parse("PSSWL 54")
    assert telnet_client.state["subwoofer_level"] == 54


@pytest.mark.asyncio
async def test_parse_subwoofer2_level(telnet_client):
    await telnet_client._parse("PSSWL2 46")
    assert telnet_client.state["subwoofer2_level"] == 46


# ── Audio Settings ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_multeq(telnet_client):
    await telnet_client._parse("PSMULTEQ:AUDYSSEY")
    assert telnet_client.state["multeq"] == "AUDYSSEY"


@pytest.mark.asyncio
async def test_parse_dynamic_eq_on(telnet_client):
    await telnet_client._parse("PSDYNEQ ON")
    assert telnet_client.state["dynamic_eq"] is True


@pytest.mark.asyncio
async def test_parse_dynamic_eq_off(telnet_client):
    await telnet_client._parse("PSDYNEQ OFF")
    assert telnet_client.state["dynamic_eq"] is False


@pytest.mark.asyncio
async def test_parse_dynamic_volume(telnet_client):
    await telnet_client._parse("PSDYNVOL MED")
    assert telnet_client.state["dynamic_volume"] == "MED"


@pytest.mark.asyncio
async def test_parse_eco_mode(telnet_client):
    await telnet_client._parse("ECOAUTO")
    assert telnet_client.state["eco_mode"] == "AUTO"


@pytest.mark.asyncio
async def test_parse_sleep_timer(telnet_client):
    await telnet_client._parse("SLP030")
    assert telnet_client.state["sleep_timer"] == 30


@pytest.mark.asyncio
async def test_parse_sleep_off(telnet_client):
    await telnet_client._parse("SLPOFF")
    assert telnet_client.state["sleep_timer"] is None


# ── Zone 2 ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_z2_power_on(telnet_client):
    await telnet_client._parse("Z2ON")
    assert telnet_client.state["z2_power"] is True


@pytest.mark.asyncio
async def test_parse_z2_power_off(telnet_client):
    await telnet_client._parse("Z2OFF")
    assert telnet_client.state["z2_power"] is False


@pytest.mark.asyncio
async def test_parse_z2_volume(telnet_client):
    await telnet_client._parse("Z235")
    assert telnet_client.state["z2_volume"] == 35


@pytest.mark.asyncio
async def test_parse_z2_mute(telnet_client):
    await telnet_client._parse("Z2MUON")
    assert telnet_client.state["z2_muted"] is True


@pytest.mark.asyncio
async def test_parse_z2_source(telnet_client):
    await telnet_client._parse("Z2NET")
    assert telnet_client.state["z2_source"] == "NET"
