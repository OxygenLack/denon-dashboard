"""Volume and mute control endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import VolumeRequest
from state import app_state

router = APIRouter(prefix="/api/v1", tags=["volume"])


@router.post("/volume")
async def set_volume(req: VolumeRequest):
    if req.level == int(req.level):
        cmd = f"MV{int(req.level):02d}"
    else:
        cmd = f"MV{int(req.level):02d}5"
    return await _send(cmd)


@router.post("/volume/up")
async def volume_up():
    return await _send("MVUP")


@router.post("/volume/down")
async def volume_down():
    return await _send("MVDOWN")


@router.post("/mute/on")
async def mute_on():
    return await _send("MUON")


@router.post("/mute/off")
async def mute_off():
    return await _send("MUOFF")


@router.post("/mute/toggle")
async def mute_toggle():
    if app_state.telnet and app_state.telnet.state.get("muted"):
        return await _send("MUOFF")
    return await _send("MUON")


async def _send(cmd: str) -> dict:
    if not app_state.telnet:
        raise HTTPException(503, "Not connected")
    ok = await app_state.telnet.send(cmd)
    if not ok:
        raise HTTPException(502, "Failed to send")
    return {"ok": True}
