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

    async def get_music_sources(self) -> list[dict[str, Any]]:
        """Return available HEOS music sources (streaming services)."""
        resp = await self._command("browse/get_music_sources")
        if resp and "payload" in resp:
            return resp["payload"]
        return []

    async def browse_source(self, sid: int, cid: str | None = None) -> dict[str, Any]:
        """Browse a HEOS music source. Returns {items, count, returned}."""
        empty = {"items": [], "count": 0, "returned": 0}
        # Prevent HEOS command injection via cid parameter
        if cid and ('\r' in cid or '\n' in cid or len(cid) > 1000):
            _LOGGER.warning("Invalid cid rejected (injection or length)")
            return {**empty, "_debug": "invalid_cid"}
        params = f"sid={sid}"
        if cid:
            params += f"&cid={cid}"



        async with self._lock:
            if not self._writer or self._writer.is_closing():
                _LOGGER.info("HEOS browse: reconnecting...")
                await self._reconnect()
                if not self._writer:
                    _LOGGER.warning("HEOS browse: reconnect failed")
                    return {**empty, "_debug": "reconnect_failed"}
            try:
                url = f"heos://browse/browse?{params}"
                _LOGGER.info("HEOS TX: %s", url)
                self._writer.write(f"{url}\r\n".encode())
                await self._writer.drain()

                # HEOS may return "command under process" first, then the actual data.
                # It may also return responses from other commands (e.g. media poller).
                # Read up to 5 lines looking for a browse/browse response with payload.
                resp = None
                debug_lines = []
                for attempt in range(5):
                    line = await asyncio.wait_for(self._reader.readline(), timeout=8)
                    data = json.loads(line.decode().strip())
                    _LOGGER.debug("HEOS RX [%d]: %s", attempt, data)
                    cmd = data.get("heos", {}).get("command", "")
                    result = data.get("heos", {}).get("result", "")
                    msg = data.get("heos", {}).get("message", "")
                    has_payload = "payload" in data
                    debug_lines.append(f"[{attempt}] cmd={cmd} result={result} payload={'yes' if has_payload else 'no'} msg={msg[:80]}")
                    if cmd == "browse/browse":
                        if result == "fail":
                            _LOGGER.warning("HEOS browse failed: %s", msg)
                            return {**empty, "_debug": debug_lines}
                        if has_payload:
                            resp = data
                            break
                    # Skip non-browse responses (e.g. now_playing from media poller)
                if resp is None:
                    _LOGGER.warning("HEOS browse: no payload found in %d lines", len(debug_lines))
                    return {**empty, "_debug": debug_lines}

            except Exception as exc:
                _LOGGER.warning("HEOS browse error: %s", exc)
                await self.disconnect()
                return {**empty, "_debug": f"exception: {exc}"}

        # Parse count from message string
        msg = resp.get("heos", {}).get("message", "")
        count = 0
        returned = 0
        for part in msg.split("&"):
            if part.startswith("count="):
                try: count = int(part[6:])
                except ValueError: pass
            elif part.startswith("returned="):
                try: returned = int(part[9:])
                except ValueError: pass
        items = resp.get("payload") or []
        result = {"items": items, "count": count, "returned": returned}
        if not items:
            result["_debug"] = debug_lines
            # Sanitize cid for logging to prevent log injection
            safe_cid = (cid or "None").replace('\n', '\\n').replace('\r', '\\r')[:80]
            _LOGGER.warning("HEOS browse returned 0 items for cid=%s", safe_cid)
        return result

    async def play_stream(self, sid: int, mid: str) -> bool:
        """Play a stream directly (e.g., a TuneIn radio station)."""
        if not self._pid:
            return False
        # Prevent HEOS command injection via mid parameter
        if not mid or '\r' in mid or '\n' in mid or len(mid) > 500:
            _LOGGER.warning("Invalid mid rejected (injection or length)")
            return False
        resp = await self._command("browse/play_stream", f"pid={self._pid}&sid={sid}&mid={mid}")
        return resp is not None and resp.get("heos", {}).get("result") == "success"
