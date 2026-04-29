"""HEOS media control endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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


# ── Radio Browser ─────────────────────────────────────────────────────────────

import asyncio
import logging
import time

_LOGGER = logging.getLogger("radio")

TUNEIN_SID = 3
_BROWSE_CACHE: dict[str, tuple[float, dict]] = {}  # key → (timestamp, result)
_CACHE_TTL = 3600  # 1 hour
_preload_done = False


async def _cache_browse(cid: str | None = None) -> dict:
    """Browse and cache a single CID. Returns the result."""
    cache_key = cid or "__root__"
    now = time.monotonic()
    if cache_key in _BROWSE_CACHE:
        ts, cached = _BROWSE_CACHE[cache_key]
        if now - ts < _CACHE_TTL and cached.get("items"):
            return cached
    result = await app_state.heos.browse_source(TUNEIN_SID, cid)
    if result.get("items"):
        _BROWSE_CACHE[cache_key] = (now, result)
    return result


async def preload_radio_stations() -> None:
    """Background task: preload Local Radio, Trending, and Music genres into cache."""
    global _preload_done
    if _preload_done:
        return
    try:
        await asyncio.sleep(10)  # wait for HEOS to be ready
        if not app_state.heos or not app_state.heos.connected:
            _LOGGER.info("Radio preload: HEOS not connected, skipping")
            return

        _LOGGER.info("Radio preload: starting...")
        t0 = time.time()
        total = 0

        top = await _cache_browse()
        if not top.get("items"):
            _LOGGER.warning("Radio preload: no top-level categories")
            return

        # Preload Local Radio + Trending (direct station lists)
        for cat_name in ("Local Radio", "Trending"):
            cat = next((i for i in top["items"] if cat_name in i.get("name", "")), None)
            if cat and cat.get("cid"):
                result = await _cache_browse(cat["cid"])
                n = len([i for i in result.get("items", []) if i.get("playable") == "yes"])
                total += n
                _LOGGER.info("Radio preload: %s → %d stations", cat_name, n)
                await asyncio.sleep(0.5)

        # Preload Music genre station lists
        music = next((i for i in top["items"] if i.get("name") == "Music"), None)
        if music and music.get("cid"):
            genres = await _cache_browse(music["cid"])
            for genre in genres.get("items", []):
                if genre.get("container") == "yes" and genre.get("cid"):
                    result = await _cache_browse(genre["cid"])
                    n = len([i for i in result.get("items", []) if i.get("playable") == "yes"])
                    total += n
                    await asyncio.sleep(0.3)

        _preload_done = True
        _LOGGER.info("Radio preload: done — %d stations cached in %.1fs", total, time.time() - t0)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        _LOGGER.warning("Radio preload error: %s", exc)


@router.get("/radio/browse")
async def radio_browse(cid: str | None = None):
    """Browse TuneIn radio directory. Omit cid for top-level categories."""
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    return await _cache_browse(cid)


@router.get("/radio/search")
async def radio_search(q: str = ""):
    """Search across all cached radio stations. Preload runs on startup."""
    query = q.strip().lower()
    if len(query) < 2:
        return {"results": [], "cached_stations": 0}

    words = query.split()
    results = []
    seen = set()
    all_mids = set()

    for _key, (_, data) in _BROWSE_CACHE.items():
        for item in data.get("items", []):
            if item.get("playable") != "yes" or not item.get("mid"):
                continue
            all_mids.add(item["mid"])
            if item["mid"] in seen:
                continue
            name_lower = item.get("name", "").lower()
            if all(w in name_lower for w in words):
                results.append(item)
                seen.add(item["mid"])

    return {"results": results, "cached_stations": len(all_mids)}


@router.post("/radio/refresh")
async def radio_refresh():
    """Clear radio cache and re-preload stations in background."""
    global _preload_done
    _BROWSE_CACHE.clear()
    _preload_done = False
    asyncio.create_task(preload_radio_stations())
    return {"ok": True}


class RadioPlayRequest(BaseModel):
    mid: str = Field(..., min_length=1, max_length=500, pattern=r"^[^\r\n]+$",
                     description="Station media ID (e.g. 's280354')")


@router.post("/radio/play")
async def radio_play(req: RadioPlayRequest):
    """Play a TuneIn radio station by media ID."""
    if not app_state.heos:
        raise HTTPException(503, "HEOS not connected")
    # Play uses the main HEOS connection (same player session)
    ok = await app_state.heos.play_stream(TUNEIN_SID, req.mid)
    if not ok:
        raise HTTPException(502, "Failed to play station")
    return {"ok": True}
