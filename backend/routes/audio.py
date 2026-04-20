"""Audio settings endpoints: surround, source, channel volume, tone, EQ, eco, sleep."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.models import (
    ChannelVolumeRequest,
    DynamicEQRequest,
    DynamicVolumeRequest,
    EcoModeRequest,
    MultEQRequest,
    SleepTimerRequest,
    SourceRequest,
    SubwooferLevelRequest,
    SurroundRequest,
    ToneRequest,
)
from denon.const import CHANNEL_NAMES
from state import app_state

router = APIRouter(prefix="/api/v1", tags=["audio"])


@router.post("/source")
async def set_source(req: SourceRequest):
    return await _send(f"SI{req.source}")


@router.post("/surround")
async def set_surround(req: SurroundRequest):
    return await _send(f"MS{req.mode}")


@router.post("/channel-volume")
async def set_channel_volume(req: ChannelVolumeRequest):
    if req.channel not in CHANNEL_NAMES:
        raise HTTPException(400, f"Unknown channel: {req.channel}")
    return await _send(f"CV{req.channel} {req.level:02d}")


@router.post("/channel-volume/reset")
async def reset_channel_volumes():
    return await _send("CVZRL")


@router.post("/tone")
async def set_tone(req: ToneRequest):
    results = []
    if req.enabled is not None:
        results.append(await _send_raw(f"PSTONE CTRL {'ON' if req.enabled else 'OFF'}"))
    if req.bass is not None:
        results.append(await _send_raw(f"PSBAS {req.bass:02d}"))
    if req.treble is not None:
        results.append(await _send_raw(f"PSTRE {req.treble:02d}"))
    return {"ok": all(results)}


@router.post("/subwoofer-level")
async def set_subwoofer_level(req: SubwooferLevelRequest):
    if req.index == 2:
        return await _send(f"PSSWL2 {req.level:02d}")
    return await _send(f"PSSWL {req.level:02d}")


@router.post("/dynamic-eq")
async def set_dynamic_eq(req: DynamicEQRequest):
    return await _send(f"PSDYNEQ {'ON' if req.enabled else 'OFF'}")


@router.post("/dynamic-volume")
async def set_dynamic_volume(req: DynamicVolumeRequest):
    return await _send(f"PSDYNVOL {req.mode}")


@router.post("/multeq")
async def set_multeq(req: MultEQRequest):
    return await _send(f"PSMULTEQ:{req.mode}")


@router.post("/sleep")
async def set_sleep(req: SleepTimerRequest):
    if req.minutes is None or req.minutes == 0:
        return await _send("SLPOFF")
    return await _send(f"SLP{req.minutes:03d}")


@router.post("/eco")
async def set_eco(req: EcoModeRequest):
    return await _send(f"ECO{req.mode}")


# -- helpers --

async def _send_raw(cmd: str) -> bool:
    if not app_state.telnet:
        return False
    return await app_state.telnet.send(cmd)


async def _send(cmd: str) -> dict:
    if not app_state.telnet:
        raise HTTPException(503, "Not connected")
    ok = await app_state.telnet.send(cmd)
    if not ok:
        raise HTTPException(502, "Failed to send")
    return {"ok": True}
