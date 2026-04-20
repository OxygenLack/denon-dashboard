"""Denon Dashboard — FastAPI backend."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from denon.discovery import discover_receivers
from routes import power, volume, audio, zone2, media, status
from state import app_state

# ---- Logging ----
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_LOGGER = logging.getLogger("denon_dashboard")


# ---- Background discovery ----

async def _auto_discover_and_connect() -> None:
    """Background task: discover receiver and connect. Retries every 30s until found."""
    _LOGGER.info("No DENON_DASHBOARD_DENON_HOST set — starting auto-discovery in background...")
    while True:
        app_state.discovering = True
        await app_state.broadcast_state()
        try:
            devices = await discover_receivers(timeout=5.0)
            if devices:
                host = devices[0]["ip"]
                _LOGGER.info("Auto-discovered receiver at %s (%s)", host, devices[0].get("model"))
                app_state.discovering = False
                await app_state.connect_to_host(host)
                return  # success — stop retrying
            else:
                _LOGGER.warning("Auto-discovery found no receivers — retrying in 30s")
        except Exception as exc:
            _LOGGER.error("Auto-discovery error: %s — retrying in 30s", exc)
        app_state.discovering = False
        await app_state.broadcast_state()
        await asyncio.sleep(30)


# ---- Lifespan ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build source name cache from env config
    app_state.source_name_cache = settings.source_name_map.copy()
    _LOGGER.info(
        "Configured %d custom source names: %s",
        len(app_state.source_name_cache),
        list(app_state.source_name_cache.keys()),
    )

    host = settings.denon_host
    if host:
        _LOGGER.info("Connecting to configured host %s...", host)
        await app_state.connect_to_host(host)
    else:
        asyncio.create_task(_auto_discover_and_connect())

    yield

    if app_state.heos:
        await app_state.heos.disconnect()
    if app_state.telnet:
        await app_state.telnet.disconnect()


# ---- App ----

app = FastAPI(
    title="Denon Dashboard API",
    version="1.0.0",
    description="Control API for Denon AVR receivers (telnet-only)",
    lifespan=lifespan,
)

# CORS — configurable via DENON_DASHBOARD_CORS_ORIGINS
cors_origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Include routers ----
app.include_router(power.router)
app.include_router(volume.router)
app.include_router(audio.router)
app.include_router(zone2.router)
app.include_router(media.router)
app.include_router(status.router)


# ---- WebSocket ----

@app.websocket("/api/v1/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    app_state.ws_clients.add(ws)
    _LOGGER.info("WebSocket client connected (%d total)", len(app_state.ws_clients))
    try:
        # Send current state immediately
        if app_state.telnet:
            await ws.send_text(json.dumps(app_state.build_status()))

        # Keep alive and handle incoming commands
        while True:
            data = await ws.receive_text()
            try:
                msg = json.loads(data)
                if "command" in msg and app_state.telnet:
                    await app_state.telnet.send(msg["command"])
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        _LOGGER.debug("WebSocket error: %s", exc)
    finally:
        app_state.ws_clients.discard(ws)
        _LOGGER.info(
            "WebSocket client disconnected (%d remaining)", len(app_state.ws_clients)
        )


# ---- Static files (served last, catches all non-API routes) ----

_STATIC_DIR = os.environ.get("STATIC_DIR", "/app/static")
if os.path.isdir(_STATIC_DIR):
    app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="static")
