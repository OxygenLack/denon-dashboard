"""Zone 2 control endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import SourceRequest, Zone2VolumeRequest
from state import app_state

router = APIRouter(prefix="/api/v1/zone2", tags=["zone2"])


@router.post("/power/on")
async def z2_power_on():
    return await _send("Z2ON")


@router.post("/power/off")
async def z2_power_off():
    return await _send("Z2OFF")


@router.post("/volume")
async def z2_volume(req: Zone2VolumeRequest):
    return await _send(f"Z2{req.level:02d}")


@router.post("/volume/up")
async def z2_volume_up():
    return await _send("Z2UP")


@router.post("/volume/down")
async def z2_volume_down():
    return await _send("Z2DOWN")


@router.post("/mute/on")
async def z2_mute_on():
    return await _send("Z2MUON")


@router.post("/mute/off")
async def z2_mute_off():
    return await _send("Z2MUOFF")


@router.post("/source")
async def z2_source(req: SourceRequest):
    return await _send(f"Z2{req.source}")


async def _send(cmd: str) -> dict:
    if not app_state.telnet:
        raise HTTPException(503, "Not connected")
    ok = await app_state.telnet.send(cmd)
    if not ok:
        raise HTTPException(502, "Failed to send")
    return {"ok": True}
