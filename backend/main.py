"""Denon Dashboard — FastAPI backend."""
from __future__ import annotations

import asyncio
import json
import logging
import ssl
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
from typing import Any
from urllib.request import urlopen, Request

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.models import (
    ChannelVolumeRequest,
    CommandRequest,
    DeviceInfoResponse,
    DynamicEQRequest,
    DynamicVolumeRequest,
    EcoModeRequest,
    HealthResponse,
    MultEQRequest,
    SleepTimerRequest,
    SourceRequest,
    StatusResponse,
    SubwooferLevelRequest,
    SurroundRequest,
    ToneRequest,
    VolumeRequest,
    Zone2VolumeRequest,
)
from config import settings
from denon.const import CHANNEL_NAMES, DEFAULT_SOURCES
from denon.heos_client import HeosClient
from denon.telnet_client import DenonTelnetClient

# ---- Logging ----
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger("denon_dashboard")

# ---- Global instances ----
telnet: DenonTelnetClient | None = None
heos: HeosClient | None = None
ws_clients: set[WebSocket] = set()

# Source name mapping: protocol code -> display name
# Priority: env config > DEFAULT_SOURCES fallback
source_name_cache: dict[str, str] = {}

# Speaker calibration offsets from Audyssey (HTTP API index -> dB)
# Fetched once at startup, maps channel code to calibration dB offset
speaker_calibration: dict[str, float] = {}

# HTTP speaker index to telnet channel code
_SPEAKER_INDEX_MAP = {
    "0": "FL", "1": "FR", "2": "C", "3": "SW",
    "4": "SR", "5": "SBR", "6": "SB", "7": "SBL",
    "8": "SL", "9": "FHR", "10": "FHL", "11": "FWR",
    "12": "FWL", "13": "TFR", "14": "TFL", "15": "TMR",
    "16": "TML", "17": "TRR", "18": "TRL",
    "30": "SW", "31": "SW2",
}


def _resolve_source_name(code: str | None) -> str | None:
    """Resolve a source protocol code to a display name."""
    if not code:
        return None
    return source_name_cache.get(code, DEFAULT_SOURCES.get(code, code))


async def broadcast_state(state: dict[str, Any]) -> None:
    """Broadcast state to all connected WebSocket clients."""
    data = _build_status(state)
    msg = json.dumps(data)
    dead = set()
    for ws in ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            dead.add(ws)
    if dead:
        ws_clients.difference_update(dead)


def _build_status(state: dict[str, Any]) -> dict[str, Any]:
    """Build status dict from raw telnet state."""
    src = state.get("source")
    z2src = state.get("z2_source")
    return {
        "connected": telnet.connected if telnet else False,
        "power": state.get("power"),
        "volume": state.get("volume"),
        "volume_max": state.get("volume_max"),
        "muted": state.get("muted"),
        "source": src,
        "source_name": _resolve_source_name(src),
        "surround_mode": state.get("surround_mode"),
        "channel_volumes": state.get("channel_volumes", {}),
        "speaker_calibration": speaker_calibration,
        "tone_control": state.get("tone_control"),
        "bass": state.get("bass"),
        "treble": state.get("treble"),
        "subwoofer_level": state.get("subwoofer_level"),
        "subwoofer2_level": state.get("subwoofer2_level"),
        "dialog_level": state.get("dialog_level"),
        "dialog_level_enabled": state.get("dialog_level_enabled"),
        "multeq": state.get("multeq"),
        "dynamic_eq": state.get("dynamic_eq"),
        "dynamic_volume": state.get("dynamic_volume"),
        "ref_level_offset": state.get("ref_level_offset"),
        "sleep_timer": state.get("sleep_timer"),
        "eco_mode": state.get("eco_mode"),
        "z2_power": state.get("z2_power"),
        "z2_volume": state.get("z2_volume"),
        "z2_muted": state.get("z2_muted"),
        "z2_source": z2src,
        "z2_source_name": _resolve_source_name(z2src),
    }


def _fetch_speaker_calibration() -> dict[str, float]:
    """Fetch Audyssey speaker calibration from receiver HTTP API (best-effort)."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        url = f"https://{settings.denon_host}:10443/ajax/speakers/get_config?type=5"
        req = Request(url, headers={"User-Agent": "DenonDashboard/1.0"})
        with urlopen(req, timeout=5, context=ctx) as resp:
            data = resp.read().decode()
        root = ET.fromstring(data)
        cal: dict[str, float] = {}
        for sp in root.findall(".//Speaker"):
            idx = sp.get("index", "")
            ch = _SPEAKER_INDEX_MAP.get(idx)
            if ch and sp.text:
                cal[ch] = int(sp.text) / 10.0
        _LOGGER.info("Fetched speaker calibration: %s", cal)
        return cal
    except Exception as exc:
        _LOGGER.warning("Could not fetch speaker calibration (HTTP): %s", exc)
        return {}


# ---- Lifespan ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    global telnet, heos, source_name_cache, speaker_calibration

    # Build source name cache from env config
    source_name_cache = settings.source_name_map.copy()
    _LOGGER.info(
        "Configured %d custom source names: %s",
        len(source_name_cache),
        list(source_name_cache.keys()),
    )

    # Fetch speaker calibration from HTTP (best-effort, non-blocking)
    speaker_calibration = await asyncio.to_thread(_fetch_speaker_calibration)

    # Connect telnet
    telnet = DenonTelnetClient(settings.denon_host, settings.denon_telnet_port)
    telnet.on_state_change(broadcast_state)

    try:
        await telnet.connect()
        _LOGGER.info("Telnet connected to %s:%s", settings.denon_host, settings.denon_telnet_port)
    except Exception as exc:
        _LOGGER.error(
            "Initial telnet connection failed: %s (will retry in background)", exc
        )

    # Connect HEOS (for media controls)
    heos = HeosClient(settings.denon_host)
    try:
        await heos.connect()
    except Exception as exc:
        _LOGGER.warning("HEOS connection failed: %s", exc)

    yield

    if heos:
        await heos.disconnect()
    if telnet:
        await telnet.disconnect()


# ---- App ----

app = FastAPI(
    title="Denon Dashboard API",
    version="1.0.0",
    description="Control API for Denon AVR receivers (telnet-only)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- WebSocket ----

@app.websocket("/api/v1/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    ws_clients.add(ws)
    _LOGGER.info("WebSocket client connected (%d total)", len(ws_clients))
    try:
        # Send current state immediately
        if telnet:
            await ws.send_text(json.dumps(_build_status(telnet.state)))

        # Keep alive and handle incoming commands
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if "command" in msg and telnet:
                    await telnet.send(msg["command"])
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        _LOGGER.debug("WebSocket error: %s", exc)
    finally:
        ws_clients.discard(ws)
        _LOGGER.info(
            "WebSocket client disconnected (%d remaining)", len(ws_clients)
        )


# ---- REST API ----

@app.get("/api/v1/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok" if (telnet and telnet.connected) else "degraded",
        telnet_connected=telnet.connected if telnet else False,
        receiver_ip=settings.denon_host,
        receiver_power=telnet.state.get("power") if telnet else None,
        device_name=settings.denon_device_name,
    )


@app.get("/api/v1/status", response_model=StatusResponse)
async def status():
    if not telnet:
        raise HTTPException(503, "Not initialized")
    return StatusResponse(**_build_status(telnet.state))


@app.get("/api/v1/device", response_model=DeviceInfoResponse)
async def device_info():
    """Return device config (from env vars + telnet-discovered channels)."""
    # Build source list from configured names + defaults for active source
    sources = []
    all_source_names = {**DEFAULT_SOURCES, **source_name_cache}
    for code, name in source_name_cache.items():
        sources.append({"id": code, "name": name})

    # Also include current source if not in the map
    if telnet:
        for src_field in ("source", "z2_source"):
            src = telnet.state.get(src_field)
            if src and src not in source_name_cache:
                sources.append(
                    {"id": src, "name": DEFAULT_SOURCES.get(src, src)}
                )

    return DeviceInfoResponse(
        device_name=settings.denon_device_name,
        zone1_name=settings.denon_zone1_name,
        zone2_name=settings.denon_zone2_name,
        sources=sources,
        source_name_map={**DEFAULT_SOURCES, **source_name_cache},
        channel_volumes=telnet.state.get("channel_volumes", {}) if telnet else {},
        receiver_ip=settings.denon_host,
    )


@app.get("/api/v1/channels")
async def channel_info():
    """Get available channels with names and current levels."""
    if not telnet:
        raise HTTPException(503, "Not initialized")
    cvs = telnet.state.get("channel_volumes", {})
    return {
        ch: {"name": CHANNEL_NAMES.get(ch, ch), "level": lvl}
        for ch, lvl in cvs.items()
    }


# -- Commands --

@app.post("/api/v1/command")
async def raw_command(req: CommandRequest):
    if not telnet:
        raise HTTPException(503, "Not connected")
    ok = await telnet.send(req.command)
    if not ok:
        raise HTTPException(502, "Failed to send command")
    return {"ok": True}


@app.post("/api/v1/power/on")
async def power_on():
    return await _send("PWON")


@app.post("/api/v1/power/off")
async def power_off():
    return await _send("PWSTANDBY")


@app.post("/api/v1/power/toggle")
async def power_toggle():
    if telnet and telnet.state.get("power"):
        return await _send("PWSTANDBY")
    return await _send("PWON")


@app.post("/api/v1/volume")
async def set_volume(req: VolumeRequest):
    if req.level == int(req.level):
        cmd = f"MV{int(req.level):02d}"
    else:
        cmd = f"MV{int(req.level):02d}5"
    return await _send(cmd)


@app.post("/api/v1/volume/up")
async def volume_up():
    return await _send("MVUP")


@app.post("/api/v1/volume/down")
async def volume_down():
    return await _send("MVDOWN")


@app.post("/api/v1/mute/on")
async def mute_on():
    return await _send("MUON")


@app.post("/api/v1/mute/off")
async def mute_off():
    return await _send("MUOFF")


@app.post("/api/v1/mute/toggle")
async def mute_toggle():
    if telnet and telnet.state.get("muted"):
        return await _send("MUOFF")
    return await _send("MUON")


@app.post("/api/v1/source")
async def set_source(req: SourceRequest):
    return await _send(f"SI{req.source}")


@app.post("/api/v1/surround")
async def set_surround(req: SurroundRequest):
    return await _send(f"MS{req.mode}")


@app.post("/api/v1/channel-volume")
async def set_channel_volume(req: ChannelVolumeRequest):
    if req.channel not in CHANNEL_NAMES:
        raise HTTPException(400, f"Unknown channel: {req.channel}")
    return await _send(f"CV{req.channel} {req.level:02d}")


@app.post("/api/v1/channel-volume/reset")
async def reset_channel_volumes():
    return await _send("CVZRL")


@app.post("/api/v1/tone")
async def set_tone(req: ToneRequest):
    results = []
    if req.enabled is not None:
        results.append(await _send_raw(f"PSTONE CTRL {'ON' if req.enabled else 'OFF'}"))
    if req.bass is not None:
        results.append(await _send_raw(f"PSBAS {req.bass:02d}"))
    if req.treble is not None:
        results.append(await _send_raw(f"PSTRE {req.treble:02d}"))
    return {"ok": all(results)}


@app.post("/api/v1/subwoofer-level")
async def set_subwoofer_level(req: SubwooferLevelRequest):
    if req.index == 2:
        return await _send(f"PSSWL2 {req.level:02d}")
    return await _send(f"PSSWL {req.level:02d}")


@app.post("/api/v1/dynamic-eq")
async def set_dynamic_eq(req: DynamicEQRequest):
    return await _send(f"PSDYNEQ {'ON' if req.enabled else 'OFF'}")


@app.post("/api/v1/dynamic-volume")
async def set_dynamic_volume(req: DynamicVolumeRequest):
    return await _send(f"PSDYNVOL {req.mode}")


@app.post("/api/v1/multeq")
async def set_multeq(req: MultEQRequest):
    return await _send(f"PSMULTEQ:{req.mode}")


@app.post("/api/v1/sleep")
async def set_sleep(req: SleepTimerRequest):
    if req.minutes is None or req.minutes == 0:
        return await _send("SLPOFF")
    return await _send(f"SLP{req.minutes:03d}")


@app.post("/api/v1/eco")
async def set_eco(req: EcoModeRequest):
    return await _send(f"ECO{req.mode}")


# -- Zone 2 --

@app.post("/api/v1/zone2/power/on")
async def z2_power_on():
    return await _send("Z2ON")


@app.post("/api/v1/zone2/power/off")
async def z2_power_off():
    return await _send("Z2OFF")


@app.post("/api/v1/zone2/volume")
async def z2_volume(req: Zone2VolumeRequest):
    return await _send(f"Z2{req.level:02d}")


@app.post("/api/v1/zone2/volume/up")
async def z2_volume_up():
    return await _send("Z2UP")


@app.post("/api/v1/zone2/volume/down")
async def z2_volume_down():
    return await _send("Z2DOWN")


@app.post("/api/v1/zone2/mute/on")
async def z2_mute_on():
    return await _send("Z2MUON")


@app.post("/api/v1/zone2/mute/off")
async def z2_mute_off():
    return await _send("Z2MUOFF")


@app.post("/api/v1/zone2/source")
async def z2_source(req: SourceRequest):
    return await _send(f"Z2{req.source}")


# -- HEOS Media Controls --

@app.post("/api/v1/media/play")
async def media_play():
    if not heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await heos.play()
    if not ok:
        raise HTTPException(502, "Play command failed")
    return {"ok": True}


@app.post("/api/v1/media/pause")
async def media_pause():
    if not heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await heos.pause()
    if not ok:
        raise HTTPException(502, "Pause command failed")
    return {"ok": True}


@app.post("/api/v1/media/stop")
async def media_stop():
    if not heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await heos.stop()
    if not ok:
        raise HTTPException(502, "Stop command failed")
    return {"ok": True}


@app.post("/api/v1/media/next")
async def media_next():
    if not heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await heos.next_track()
    if not ok:
        raise HTTPException(502, "Next command failed")
    return {"ok": True}


@app.post("/api/v1/media/previous")
async def media_previous():
    if not heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await heos.previous_track()
    if not ok:
        raise HTTPException(502, "Previous command failed")
    return {"ok": True}


@app.get("/api/v1/media/now-playing")
async def media_now_playing():
    if not heos:
        raise HTTPException(503, "HEOS not connected")
    info = await heos.get_now_playing()
    state = await heos.get_play_state()
    return {"now_playing": info, "play_state": state}


@app.post("/api/v1/refresh")
async def refresh_status():
    if not telnet:
        raise HTTPException(503, "Not connected")
    await telnet.refresh()
    return {"ok": True}


# -- helpers --

async def _send_raw(cmd: str) -> bool:
    if not telnet:
        return False
    return await telnet.send(cmd)


async def _send(cmd: str) -> dict:
    if not telnet:
        raise HTTPException(503, "Not connected")
    ok = await telnet.send(cmd)
    if not ok:
        raise HTTPException(502, "Failed to send")
    return {"ok": True}


# ---- Static files (served last, catches all non-API routes) ----
import os

_STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
