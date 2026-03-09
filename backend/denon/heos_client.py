"""Async HEOS CLI client for media transport controls."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

_LOGGER = logging.getLogger("denon.heos_client")

HEOS_PORT = 1255


class HeosClient:
    """Lightweight HEOS CLI client (port 1255) for media control."""

    def __init__(self, host: str, port: int = HEOS_PORT):
        self._host = host
        self._port = port
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._lock = asyncio.Lock()
        self._pid: int | None = None

    async def connect(self) -> None:
        """Connect and discover player ID."""
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=5
            )
            _LOGGER.info("HEOS connected to %s:%s", self._host, self._port)
            # Discover player
            resp = await self._command("player/get_players")
            if resp and "payload" in resp:
                for p in resp["payload"]:
                    self._pid = p.get("pid")
                    _LOGGER.info("HEOS player: %s (pid=%s)", p.get("name"), self._pid)
                    break
        except Exception as exc:
            _LOGGER.warning("HEOS connection failed: %s", exc)
            self._reader = None
            self._writer = None

    async def disconnect(self) -> None:
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    @property
    def connected(self) -> bool:
        return self._writer is not None and not self._writer.is_closing()

    @property
    def player_id(self) -> int | None:
        return self._pid

    async def _command(self, cmd: str, params: str = "") -> dict[str, Any] | None:
        """Send a HEOS command and return parsed JSON response."""
        async with self._lock:
            if not self._writer or self._writer.is_closing():
                await self._reconnect()
                if not self._writer:
                    return None
            try:
                url = f"heos://{cmd}"
                if params:
                    url += f"?{params}"
                self._writer.write(f"{url}\r\n".encode())
                await self._writer.drain()

                line = await asyncio.wait_for(self._reader.readline(), timeout=5)
                data = json.loads(line.decode().strip())
                _LOGGER.debug("HEOS RX: %s", data)
                return data
            except Exception as exc:
                _LOGGER.warning("HEOS command error (%s): %s", cmd, exc)
                await self.disconnect()
                return None

    async def _reconnect(self) -> None:
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port), timeout=5
            )
            _LOGGER.info("HEOS reconnected")
        except Exception as exc:
            _LOGGER.warning("HEOS reconnect failed: %s", exc)

    def _pid_param(self) -> str:
        return f"pid={self._pid}" if self._pid else ""

    async def play(self) -> bool:
        resp = await self._command("player/set_play_state", f"{self._pid_param()}&state=play")
        return resp is not None and resp.get("heos", {}).get("result") == "success"

    async def pause(self) -> bool:
        resp = await self._command("player/set_play_state", f"{self._pid_param()}&state=pause")
        return resp is not None and resp.get("heos", {}).get("result") == "success"

    async def stop(self) -> bool:
        resp = await self._command("player/set_play_state", f"{self._pid_param()}&state=stop")
        return resp is not None and resp.get("heos", {}).get("result") == "success"

    async def next_track(self) -> bool:
        resp = await self._command("player/play_next", self._pid_param())
        return resp is not None and resp.get("heos", {}).get("result") == "success"

    async def previous_track(self) -> bool:
        resp = await self._command("player/play_previous", self._pid_param())
        return resp is not None and resp.get("heos", {}).get("result") == "success"

    async def get_play_state(self) -> str | None:
        """Return 'play', 'pause', 'stop', or None."""
        resp = await self._command("player/get_play_state", self._pid_param())
        if resp:
            msg = resp.get("heos", {}).get("message", "")
            for part in msg.split("&"):
                if part.startswith("state="):
                    return part[6:]
        return None

    async def get_now_playing(self) -> dict[str, Any] | None:
        """Return now-playing info."""
        resp = await self._command("player/get_now_playing_media", self._pid_param())
        if resp and "payload" in resp:
            return resp["payload"]
        return None
