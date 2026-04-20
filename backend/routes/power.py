"""Power control endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from state import app_state

router = APIRouter(prefix="/api/v1", tags=["power"])


@router.post("/power/on")
async def power_on():
    return await _send("PWON")


@router.post("/power/off")
async def power_off():
    return await _send("PWSTANDBY")


@router.post("/power/toggle")
async def power_toggle():
    if app_state.telnet and app_state.telnet.state.get("power"):
        return await _send("PWSTANDBY")
    return await _send("PWON")


async def _send(cmd: str) -> dict:
    if not app_state.telnet:
        raise HTTPException(503, "Not connected")
    ok = await app_state.telnet.send(cmd)
    if not ok:
        raise HTTPException(502, "Failed to send")
    return {"ok": True}
