# CLAUDE.md — Denon Dashboard

This file provides context for AI assistants (Claude, Codex, etc.) working on this project.

## Project Overview

A web dashboard for controlling Denon AVR receivers via telnet. Single Docker container serving a React frontend + FastAPI backend.

## Architecture

```
frontend/ (React 19 + Vite + Tailwind)
  └── src/
      ├── App.jsx              → Zone selector, section routing
      ├── hooks/
      │   ├── useWebSocket.js  → WebSocket client, state management
      │   ├── useApi.js        → REST API helper (POST)
      │   └── useDeviceInfo.js → Fetches /api/v1/device on mount
      └── components/
          ├── StatusBar.jsx       → Header + expandable health panel
          ├── PowerControl.jsx    → Zone-aware power (ZMON/ZMOFF or Z2ON/Z2OFF)
          ├── VolumeControl.jsx   → Slider + buttons + mute
          ├── MediaControls.jsx   → HEOS play/pause/next/prev + now playing
          ├── SourceSelector.jsx  → Grid with icons, zone-aware
          ├── SurroundMode.jsx    → Surround mode dropdown
          ├── ChannelLevels.jsx   → Per-speaker trim + calibration
          ├── SubwooferLevel.jsx  → Subwoofer trim slider
          ├── ToneControls.jsx    → Bass/treble (hidden when tone off)
          ├── AudioSettings.jsx   → MultEQ, DynEQ, DynVol, eco
          └── Zone2Controls.jsx   → Z2 power, volume, media, source

backend/
  ├── main.py                 → FastAPI app, lifespan, all endpoints, WebSocket
  ├── config.py               → Pydantic settings (DENON_DASHBOARD_ prefix)
  ├── api/models.py           → Request/response Pydantic models
  └── denon/
      ├── const.py            → Protocol constants, source defaults, query commands
      ├── telnet_client.py    → Async telnet: connect, parse, reconnect, heartbeat
      └── heos_client.py      → HEOS CLI (port 1255): media transport, now playing
```

## Key Protocol Details

- **Telnet** (port 23): `\r` terminator, 50ms command interval
- **HEOS CLI** (port 1255): JSON over TCP, `\r\n` terminator
- **PW vs ZM**: `PWON` = system power (any zone), `ZMON`/`ZMOFF` = main zone only
  - When only Z2 is on: PWON is sent but ZMOFF is the truth for main zone
- **Volume**: 0–98 scale, 80 = 0dB. Three-digit for half steps (805 = 80.5)
- **Channel volume**: 38–62 range, 50 = 0dB trim on top of Audyssey calibration
- **Source codes**: GAME, MPLAY, TV, NET, 8K, BD, etc. — mapped to display names via env config

## State Flow

1. Telnet client connects, sends query commands, parses responses into `state` dict
2. On state change, `broadcast_state()` pushes to all WebSocket clients
3. Frontend `useWebSocket` hook receives state, triggers React re-renders
4. User actions → REST API POST → backend sends telnet command → receiver responds → state updates → WebSocket push

## Speaker Calibration

- Audyssey calibration offsets fetched from receiver's HTTP API at startup (`/ajax/speakers/get_config?type=5`)
- Stored as `speaker_calibration` dict (channel → dB offset)
- Frontend shows effective level = calibration + trim

## Environment Variables

All prefixed with `DENON_DASHBOARD_`. See README for full list.
Key: `DENON_HOST` (required), `DENON_SOURCE_NAMES` (JSON map), zone/device names.

## Build & Deploy

- Multi-stage Dockerfile: node:22-alpine (frontend build) → python:3.12-slim (runtime)
- GitLab CI builds image → pushes to registry → Komodo webhook auto-deploys
- Container serves frontend as static files from FastAPI

## Common Tasks

- **Add a new API endpoint**: Add route in `main.py`, model in `api/models.py` if needed
- **Add a new telnet response**: Add parsing in `telnet_client.py._parse()`, add to state dict
- **Add a new UI component**: Create in `frontend/src/components/`, wire into `App.jsx`
- **Add a new source**: Just add to `DENON_SOURCE_NAMES` env var, no code change needed
- **Debug**: Set `DENON_DASHBOARD_LOG_LEVEL=DEBUG` for full telnet RX logging
