"""Android TV Remote protocol endpoints."""
from __future__ import annotations

import ipaddress
import logging
from typing import Literal

from androidtvremote2 import CannotConnect, ConnectionClosed, InvalidAuth
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from androidtv.discovery import discover_android_tvs
from state import app_state

_LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/androidtv", tags=["androidtv"])

AndroidTvKey = Literal[
    "DPAD_UP",
    "DPAD_DOWN",
    "DPAD_LEFT",
    "DPAD_RIGHT",
    "DPAD_CENTER",
    "BACK",
    "HOME",
    "MENU",
    "POWER",
    "SLEEP",
    "MEDIA_PLAY_PAUSE",
    "MEDIA_PLAY",
    "MEDIA_PAUSE",
    "MEDIA_STOP",
    "MEDIA_NEXT",
    "MEDIA_PREVIOUS",
    "VOLUME_UP",
    "VOLUME_DOWN",
    "VOLUME_MUTE",
    "MUTE",
    "CHANNEL_UP",
    "CHANNEL_DOWN",
]


class AndroidTvHostRequest(BaseModel):
    host: str = Field(..., min_length=2, max_length=80)


class AndroidTvPairFinishRequest(BaseModel):
    code: str = Field(..., min_length=4, max_length=32, pattern=r"^\s*[A-Za-z0-9]{4,12}\s*$")


class AndroidTvKeyRequest(BaseModel):
    key: AndroidTvKey


class AndroidTvTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500, pattern=r"^[^\r\n]+$")


@router.get("/status")
async def androidtv_status():
    return app_state.android_tv.build_status()


@router.get("/discover")
async def androidtv_discover():
    try:
        return {"devices": await discover_android_tvs(timeout=4.0)}
    except Exception as exc:
        _LOGGER.error("Android TV discovery error: %s", exc)
        raise HTTPException(500, "Discovery failed")


@router.post("/connect")
async def androidtv_connect(req: AndroidTvHostRequest):
    host = _validate_lan_ip(req.host)
    try:
        return await app_state.android_tv.connect(host)
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/disconnect")
async def androidtv_disconnect():
    await app_state.android_tv.disconnect(clear_host=True)
    return app_state.android_tv.build_status()


@router.post("/pair/start")
async def androidtv_pair_start(req: AndroidTvHostRequest):
    host = _validate_lan_ip(req.host)
    try:
        return await app_state.android_tv.start_pairing(host)
    except (CannotConnect, ConnectionClosed):
        raise HTTPException(502, "Could not start pairing")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


@router.post("/pair/finish")
async def androidtv_pair_finish(req: AndroidTvPairFinishRequest):
    try:
        return await app_state.android_tv.finish_pairing(req.code.strip().upper())
    except InvalidAuth:
        raise HTTPException(401, "Invalid pairing code")
    except ConnectionClosed:
        raise HTTPException(409, "Pairing has not been started")
    except CannotConnect:
        raise HTTPException(502, "Could not connect after pairing")


@router.post("/key")
async def androidtv_key(req: AndroidTvKeyRequest):
    try:
        return await app_state.android_tv.send_key(req.key)
    except ConnectionClosed:
        raise HTTPException(503, "Android TV not connected")
    except ValueError:
        raise HTTPException(400, "Unsupported key")


@router.post("/text")
async def androidtv_text(req: AndroidTvTextRequest):
    try:
        return await app_state.android_tv.send_text(req.text)
    except ConnectionClosed:
        raise HTTPException(503, "Android TV not connected")
    except ValueError as exc:
        raise HTTPException(400, str(exc))


def _validate_lan_ip(value: str) -> str:
    host = value.strip()
    ip_part = host.split("%", 1)[0]
    try:
        addr = ipaddress.ip_address(ip_part)
    except ValueError:
        raise HTTPException(400, "Invalid IP address")
    allowed = addr.is_private or addr.is_link_local
    if not allowed or addr.is_loopback or addr.is_multicast or addr.is_unspecified:
        raise HTTPException(400, "IP address not allowed (must be a local LAN IP)")
    return host
