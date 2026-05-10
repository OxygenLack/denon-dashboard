"""Integration tests for API endpoints using FastAPI TestClient."""
from __future__ import annotations

import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch settings before importing app to prevent real connections
os.environ["DENON_DASHBOARD_DENON_HOST"] = ""
os.environ["DENON_DASHBOARD_LOG_LEVEL"] = "WARNING"


def _make_mock_telnet(state: dict):
    """Create a mock telnet client with the given state."""
    mock = MagicMock()
    mock.connected = True
    mock.host = "192.168.1.100"
    mock.state = state
    mock.send = AsyncMock(return_value=True)
    mock.refresh = AsyncMock()
    mock.disconnect = AsyncMock()
    return mock


def _make_mock_heos():
    """Create a mock HEOS client."""
    mock = MagicMock()
    mock.connected = True
    mock.play = AsyncMock(return_value=True)
    mock.pause = AsyncMock(return_value=True)
    mock.stop = AsyncMock(return_value=True)
    mock.next_track = AsyncMock(return_value=True)
    mock.previous_track = AsyncMock(return_value=True)
    mock.get_now_playing = AsyncMock(return_value={"song": "Test Song"})
    mock.get_play_state = AsyncMock(return_value="play")
    mock.disconnect = AsyncMock()
    return mock


@pytest.fixture
def mock_app_state(mock_state):
    """Patch app_state with mock clients."""
    from state import app_state

    app_state.telnet = _make_mock_telnet(mock_state)
    app_state.heos = _make_mock_heos()
    app_state.source_name_cache = {"GAME": "Game Console"}
    app_state.speaker_calibration = {"FL": -1.5, "FR": -2.0}
    yield app_state
    app_state.telnet = None
    app_state.heos = None


@pytest.fixture
def mock_app_no_connection():
    """Patch app_state with no connection."""
    from state import app_state

    app_state.telnet = None
    app_state.heos = None
    yield app_state


# ── Health ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health_connected(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["telnet_connected"] is True


@pytest.mark.asyncio
async def test_health_disconnected(mock_app_no_connection):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "degraded"
    assert data["telnet_connected"] is False


# ── Status ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_status_connected(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is True
    assert data["power"] is True
    assert data["volume"] == 50.0
    assert data["source"] == "GAME"
    assert data["source_name"] == "Game Console"


@pytest.mark.asyncio
async def test_status_not_initialized(mock_app_no_connection):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/status")
    assert resp.status_code == 503


# ── Power ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_power_on(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/power/on")
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("PWON")


@pytest.mark.asyncio
async def test_power_off(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/power/off")
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("PWSTANDBY")


# ── Volume ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_volume(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/volume", json={"level": 45.0})
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("MV45")


@pytest.mark.asyncio
async def test_set_volume_half_step(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/volume", json={"level": 45.5})
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("MV455")


@pytest.mark.asyncio
async def test_volume_up(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/volume/up")
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("MVUP")


# ── Source ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_set_source(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/source", json={"source": "TV"})
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("SITV")


# ── Media ──────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_media_play(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/media/play")
    assert resp.status_code == 200
    mock_app_state.heos.play.assert_called_once()


@pytest.mark.asyncio
async def test_media_now_playing(mock_app_state):
    from main import app

    # Pre-populate cached media state (normally filled by background poller)
    mock_app_state.media_state = {
        "now_playing": {"song": "Test Song"},
        "play_state": "play",
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/media/now-playing")
    assert resp.status_code == 200
    data = resp.json()
    assert data["now_playing"]["song"] == "Test Song"
    assert data["play_state"] == "play"


# ── Zone 2 ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_z2_power_on(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/zone2/power/on")
    assert resp.status_code == 200
    mock_app_state.telnet.send.assert_called_with("Z2ON")


# ── Device Info ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_device_info(mock_app_state):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/device")
    assert resp.status_code == 200
    data = resp.json()
    assert data["device_name"] == "Denon AVR"
    assert "channel_names" in data
    assert data["source_name_map"]["GAME"] == "Game Console"


# ── Not Connected ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_commands_503_when_disconnected(mock_app_no_connection):
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for endpoint in ["/api/v1/power/on", "/api/v1/volume/up", "/api/v1/mute/on"]:
            resp = await ac.post(endpoint)
            assert resp.status_code == 503, f"{endpoint} should return 503"


# ── Android TV ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_androidtv_status():
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/androidtv/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is False
    assert "paired" in data


@pytest.mark.asyncio
async def test_androidtv_key(monkeypatch):
    from main import app
    from state import app_state

    send_key = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(app_state.android_tv, "send_key", send_key)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/androidtv/key", json={"key": "DPAD_CENTER"})
    assert resp.status_code == 200
    send_key.assert_called_once_with("DPAD_CENTER")


@pytest.mark.asyncio
async def test_androidtv_text(monkeypatch):
    from main import app
    from state import app_state

    send_text = AsyncMock(return_value={"ok": True})
    monkeypatch.setattr(app_state.android_tv, "send_text", send_text)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/androidtv/text", json={"text": "Hello"})
    assert resp.status_code == 200
    send_text.assert_called_once_with("Hello")


@pytest.mark.asyncio
async def test_androidtv_pair_start(monkeypatch):
    from main import app
    from state import app_state

    start_pairing = AsyncMock(return_value={"pairing": True, "host": "192.168.1.120"})
    monkeypatch.setattr(app_state.android_tv, "start_pairing", start_pairing)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/androidtv/pair/start", json={"host": "192.168.1.120"})
    assert resp.status_code == 200
    start_pairing.assert_called_once_with("192.168.1.120")


@pytest.mark.asyncio
async def test_androidtv_pair_start_ipv6(monkeypatch):
    from main import app
    from state import app_state

    host = "fd00::1234"
    start_pairing = AsyncMock(return_value={"pairing": True, "host": host})
    monkeypatch.setattr(app_state.android_tv, "start_pairing", start_pairing)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/androidtv/pair/start", json={"host": host})
    assert resp.status_code == 200
    start_pairing.assert_called_once_with(host)


@pytest.mark.asyncio
async def test_androidtv_rejects_global_ipv6(monkeypatch):
    from main import app
    from state import app_state

    start_pairing = AsyncMock()
    monkeypatch.setattr(app_state.android_tv, "start_pairing", start_pairing)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/androidtv/pair/start", json={"host": "2001:4860:4860::8888"})
    assert resp.status_code == 400
    start_pairing.assert_not_called()


@pytest.mark.asyncio
async def test_androidtv_disconnect(monkeypatch):
    from main import app
    from state import app_state

    disconnect = AsyncMock()
    monkeypatch.setattr(app_state.android_tv, "disconnect", disconnect)
    monkeypatch.setattr(app_state.android_tv, "build_status", lambda: {"connected": False, "host": None})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/androidtv/disconnect")
    assert resp.status_code == 200
    assert resp.json()["connected"] is False
    disconnect.assert_called_once_with(clear_host=True)


def test_androidtv_last_host_persistence(tmp_path):
    from androidtv.remote_client import AndroidTvRemoteClient

    client = AndroidTvRemoteClient(
        client_name="Test",
        storage_dir=str(tmp_path),
        notify=AsyncMock(),
    )
    assert client.load_last_host() is None

    client.host = "192.168.1.120"
    client._save_last_host()

    restored = AndroidTvRemoteClient(
        client_name="Test",
        storage_dir=str(tmp_path),
        notify=AsyncMock(),
    )
    assert restored.load_last_host() == "192.168.1.120"

    restored._delete_last_host()
    assert restored.load_last_host() is None
