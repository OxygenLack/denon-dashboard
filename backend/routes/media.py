"""HEOS media control endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from state import app_state

router = APIRouter(prefix="/api/v1/media", tags=["media"])


@router.post("/play")
async def media_play():
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await app_state.heos.play()
    if not ok:
        raise HTTPException(502, "Play command failed")
    return {"ok": True}


@router.post("/pause")
async def media_pause():
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await app_state.heos.pause()
    if not ok:
        raise HTTPException(502, "Pause command failed")
    return {"ok": True}


@router.post("/stop")
async def media_stop():
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await app_state.heos.stop()
    if not ok:
        raise HTTPException(502, "Stop command failed")
    return {"ok": True}


@router.post("/next")
async def media_next():
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await app_state.heos.next_track()
    if not ok:
        raise HTTPException(502, "Next command failed")
    return {"ok": True}


@router.post("/previous")
async def media_previous():
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    ok = await app_state.heos.previous_track()
    if not ok:
        raise HTTPException(502, "Previous command failed")
    return {"ok": True}


@router.get("/now-playing")
async def media_now_playing():
    """Return cached now-playing info (updated by background poller)."""
    return app_state.media_state
