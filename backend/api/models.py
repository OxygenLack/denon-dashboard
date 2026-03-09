"""Pydantic models for the API."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# -- Request models --

class CommandRequest(BaseModel):
    command: str = Field(..., description="Raw telnet command (e.g. 'PWON', 'MV50')")


class VolumeRequest(BaseModel):
    level: float = Field(..., ge=0, le=98, description="Volume level 0–98 (80 = 0dB)")


class ChannelVolumeRequest(BaseModel):
    channel: str = Field(..., description="Channel code (FL, FR, C, SW, SL, SR, etc.)")
    level: int = Field(..., ge=38, le=62, description="Level 38–62 (50 = 0dB)")


class ToneRequest(BaseModel):
    bass: int | None = Field(None, ge=44, le=56, description="Bass 44–56 (50 = 0dB)")
    treble: int | None = Field(None, ge=44, le=56, description="Treble 44–56 (50 = 0dB)")
    enabled: bool | None = Field(None, description="Tone control on/off")


class SubwooferLevelRequest(BaseModel):
    level: int = Field(..., ge=38, le=62, description="Level 38–62 (50 = 0dB)")
    index: int = Field(1, ge=1, le=2, description="Subwoofer 1 or 2")


class SourceRequest(BaseModel):
    source: str = Field(..., description="Source command code (e.g. 'GAME', 'BD', 'TV')")


class SurroundRequest(BaseModel):
    mode: str = Field(..., description="Surround mode name (e.g. 'STEREO', 'MOVIE')")


class Zone2VolumeRequest(BaseModel):
    level: int = Field(..., ge=0, le=98, description="Zone 2 volume 0–98")


class DynamicEQRequest(BaseModel):
    enabled: bool


class DynamicVolumeRequest(BaseModel):
    mode: str = Field(..., description="OFF, LIT, MED, HEV")


class MultEQRequest(BaseModel):
    mode: str = Field(..., description="AUDYSSEY, BYP.LR, FLAT, MANUAL, OFF")


class SleepTimerRequest(BaseModel):
    minutes: int | None = Field(None, ge=0, le=120, description="0 or None = OFF, 1–120 = minutes")


class EcoModeRequest(BaseModel):
    mode: str = Field(..., description="ON, AUTO, OFF")


# -- Response models --

class StatusResponse(BaseModel):
    connected: bool
    power: bool | None = None
    volume: float | None = None
    volume_max: float | None = None
    muted: bool | None = None
    source: str | None = None
    source_name: str | None = None
    surround_mode: str | None = None
    channel_volumes: dict[str, int] = {}
    tone_control: bool | None = None
    bass: int | None = None
    treble: int | None = None
    subwoofer_level: int | None = None
    subwoofer2_level: int | None = None
    dialog_level: int | None = None
    dialog_level_enabled: bool | None = None
    multeq: str | None = None
    dynamic_eq: bool | None = None
    dynamic_volume: str | None = None
    ref_level_offset: int | None = None
    sleep_timer: int | None = None
    eco_mode: str | None = None
    z2_power: bool | None = None
    z2_volume: int | None = None
    z2_muted: bool | None = None
    z2_source: str | None = None
    z2_source_name: str | None = None
    speaker_calibration: dict[str, float] = {}


class DeviceInfoResponse(BaseModel):
    device_name: str = "Denon AVR"
    zone1_name: str = "Main Zone"
    zone2_name: str = "Zone 2"
    sources: list[dict[str, str]] = []
    source_name_map: dict[str, str] = {}
    channel_volumes: dict[str, int] = {}
    receiver_ip: str | None = None


class HealthResponse(BaseModel):
    status: str
    telnet_connected: bool
    receiver_ip: str
    receiver_power: bool | None = None
    device_name: str | None = None
    discovery_mode: bool = False
