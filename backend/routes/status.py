"""Status, health, device info, discovery, and connection endpoints."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from api.models import (
    CommandRequest,
    DeviceInfoResponse,
    HealthResponse,
    StatusResponse,
)
from config import settings
from denon.const import CHANNEL_NAMES, DEFAULT_SOURCES
from denon.discovery import discover_receivers
from state import app_state

_LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok" if (app_state.telnet and app_state.telnet.connected) else "degraded",
        telnet_connected=app_state.telnet.connected if app_state.telnet else False,
        receiver_ip=app_state.telnet.host if app_state.telnet else "0.0.0.0",
        receiver_power=app_state.telnet.state.get("power") if app_state.telnet else None,
        device_name=settings.denon_device_name,
        discovery_mode=not bool(settings.denon_host),
        discovering=app_state.discovering,
    )


@router.get("/discover")
async def discover_endpoint():
    """Scan the local network for Denon/Marantz AVR receivers via SSDP."""
    try:
        devices = await discover_receivers(timeout=4.0)
        return {"devices": devices}
    except Exception as exc:
        _LOGGER.error("Discovery error: %s", exc)
        raise HTTPException(500, f"Discovery failed: {exc}")


@router.post("/connect")
async def connect_to_receiver(req: CommandRequest):
    """Connect (or reconnect) to a receiver IP. Uses 'command' field as the IP."""
    ip = req.command.strip()
    if not ip:
        raise HTTPException(400, "IP address required")

    _LOGGER.info("Connecting to receiver at %s", ip)

    try:
        await app_state.connect_to_host(ip)
    except Exception as exc:
        raise HTTPException(502, f"Could not connect to {ip}: {exc}")

    return {"ok": True, "ip": ip}


@router.get("/status", response_model=StatusResponse)
async def status():
    if not app_state.telnet:
        raise HTTPException(503, "Not initialized")
    return StatusResponse(**app_state.build_status())


@router.get("/device", response_model=DeviceInfoResponse)
async def device_info():
    """Return device config (from env vars + telnet-discovered channels)."""
    # Merge sources: discovered from receiver (SSFUN) + env config overrides
    seen = set()
    sources = []

    # Start with receiver-discovered sources (preserves receiver order)
    for code, name in app_state.discovered_sources.items():
        # Env config overrides discovered display name
        display = app_state.source_name_cache.get(code, name)
        sources.append({"id": code, "name": display})
        seen.add(code)

    # Add any env-configured sources not discovered by the receiver
    for code, name in app_state.source_name_cache.items():
        if code not in seen:
            sources.append({"id": code, "name": name})
            seen.add(code)

    # Also include current source if not in either map
    if app_state.telnet:
        for src_field in ("source", "z2_source"):
            src = app_state.telnet.state.get(src_field)
            if src and src not in seen:
                sources.append(
                    {"id": src, "name": DEFAULT_SOURCES.get(src, src)}
                )
                seen.add(src)

    # Build channel names for active channels
    active_channels = {}
    if app_state.telnet:
        for ch in app_state.telnet.state.get("channel_volumes", {}):
            if ch in CHANNEL_NAMES:
                active_channels[ch] = CHANNEL_NAMES[ch]

    return DeviceInfoResponse(
        device_name=settings.denon_device_name,
        zone1_name=settings.denon_zone1_name,
        zone2_name=settings.denon_zone2_name,
        sources=sources,
        source_name_map={**DEFAULT_SOURCES, **app_state.discovered_sources, **app_state.source_name_cache},
        channel_volumes=app_state.telnet.state.get("channel_volumes", {}) if app_state.telnet else {},
        channel_names=active_channels,
        receiver_ip=settings.denon_host,
        theme=settings.theme,
    )


@router.get("/channels")
async def channel_info():
    """Get available channels with names and current levels."""
    if not app_state.telnet:
        raise HTTPException(503, "Not initialized")
    cvs = app_state.telnet.state.get("channel_volumes", {})
    return {
        ch: {"name": CHANNEL_NAMES.get(ch, ch), "level": lvl}
        for ch, lvl in cvs.items()
    }


@router.post("/command")
async def raw_command(req: CommandRequest):
    if not app_state.telnet:
        raise HTTPException(503, "Not connected")
    ok = await app_state.telnet.send(req.command)
    if not ok:
        raise HTTPException(502, "Failed to send command")
    return {"ok": True}


@router.post("/refresh")
async def refresh_status():
    if not app_state.telnet:
        raise HTTPException(503, "Not connected")
    await app_state.telnet.refresh()
    return {"ok": True}
