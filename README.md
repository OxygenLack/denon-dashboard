# Denon AVR Dashboard

A modern, real-time web dashboard for controlling Denon/Marantz AVR receivers. Built with React + FastAPI, communicates via **telnet** (port 23) and **HEOS CLI** (port 1255) — no dependency on the receiver's unreliable built-in web interface.

[![Build](https://github.com/OxygenLack/denon-dashboard/actions/workflows/docker.yml/badge.svg)](https://github.com/OxygenLack/denon-dashboard/actions/workflows/docker.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) ![React 19](https://img.shields.io/badge/React-19-61dafb) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688) ![Docker](https://img.shields.io/badge/Docker-ready-2496ed)

> **Disclaimer:** This is an unofficial, community-developed project. Not affiliated with or endorsed by Denon, Marantz, or Sound United/Masimo. All product names and trademarks are the property of their respective owners.

## Features

### Main Zone
- **Power** on/off (main zone only — doesn't affect Zone 2)
- **Volume** control with slider, +/- buttons, and mute toggle
- **Input Source** selection with custom names and icons
- **Surround Mode** switching
- **Media Controls** — play/pause, next/previous for HEOS/streaming sources
- **Now Playing** — song, artist, album art from Spotify/HEOS
- **Speaker Levels** — per-channel volume trim with Audyssey calibration offsets
- **Subwoofer Level**
- **Tone Controls** — bass/treble (auto-hidden when tone control is off)
- **Audio Settings** — MultEQ, Dynamic EQ, Dynamic Volume, Eco mode

### Zone 2
- Independent power, volume, mute, and source control
- Media controls when on a streaming source

### Status & Monitoring
- Real-time state updates via WebSocket
- Expandable health panel — receiver IP, telnet/WS connection status, power state, surround mode, eco mode
- Audyssey speaker calibration offsets displayed per channel

## Architecture

```
Browser  ◄──WebSocket──►  FastAPI Backend  ──telnet (23)──►  Denon AVR
                           (Python)         ──HEOS (1255)──►  Receiver
```

- **Frontend**: React 19, Vite, Tailwind CSS (dark theme with gold accent)
- **Backend**: FastAPI, async telnet client, HEOS CLI client
- **Communication**: Telnet for all receiver control, HEOS CLI (port 1255) for media playback
- **Real-time**: WebSocket pushes state changes to all connected browsers instantly

## Quick Start (Docker)

### 1. Find Your Receiver

Your Denon AVR must be on the network. Find its IP address from your router or the receiver's network settings menu.

Verify telnet access:
```bash
# Should connect and show receiver responses
(echo -e "PW?\r"; sleep 1) | nc YOUR_RECEIVER_IP 23
```

### 2. Create `compose.yaml`

```yaml
services:
  denon-dashboard:
    image: ghcr.io/oxygenlack/denon-dashboard:latest
    container_name: denon-dashboard
    restart: unless-stopped
    ports:
      - "8084:8080"
    environment:
      # Required: IP address of your Denon AVR
      - DENON_DASHBOARD_DENON_HOST=192.168.1.100
      # Optional: Telnet port (default: 23)
      - DENON_DASHBOARD_DENON_TELNET_PORT=23
      # Display name shown in the header
      - DENON_DASHBOARD_DENON_DEVICE_NAME=My Receiver
      # Zone names (shown in zone selector)
      - DENON_DASHBOARD_DENON_ZONE1_NAME=Main Zone
      - DENON_DASHBOARD_DENON_ZONE2_NAME=Zone 2
      # Custom source names (JSON: protocol_code → display_name)
      - DENON_DASHBOARD_DENON_SOURCE_NAMES={"GAME":"Game Console","TV":"TV Audio","BD":"Blu-ray","NET":"Streaming","BT":"Bluetooth"}
      # Log level: DEBUG, INFO, WARNING, ERROR
      - DENON_DASHBOARD_LOG_LEVEL=INFO
```

### 3. Start

```bash
docker compose up -d
```

Open `http://YOUR_HOST:8084` in your browser.

## Configuration

All configuration is via environment variables with the `DENON_DASHBOARD_` prefix.

| Variable | Required | Default | Description |
|---|---|---|---|
| `DENON_DASHBOARD_DENON_HOST` | ✅ | — | IP address of your Denon AVR |
| `DENON_DASHBOARD_DENON_TELNET_PORT` | — | `23` | Telnet port |
| `DENON_DASHBOARD_DENON_DEVICE_NAME` | — | `Denon AVR` | Display name in header |
| `DENON_DASHBOARD_DENON_ZONE1_NAME` | — | `Main Zone` | Main zone tab label |
| `DENON_DASHBOARD_DENON_ZONE2_NAME` | — | `Zone 2` | Zone 2 tab label |
| `DENON_DASHBOARD_DENON_SOURCE_NAMES` | — | `{}` | JSON map of source codes to names |
| `DENON_DASHBOARD_LOG_LEVEL` | — | `INFO` | Log verbosity |

### Finding Source Codes

Source codes are the internal protocol identifiers your receiver uses. Common ones:

| Code | Default Name | Description |
|---|---|---|
| `GAME` | Game | HDMI input (Game mode) |
| `MPLAY` | Media Player | HDMI input (Media Player) |
| `TV` | TV Audio | ARC/eARC input |
| `NET` | Online Music | HEOS / network streaming |
| `BD` | Blu-ray | HDMI input |
| `SAT/CBL` | SAT/Cable | HDMI input |
| `AUX1` | AUX1 | Auxiliary input |
| `BT` | Bluetooth | Bluetooth |
| `8K` | 8K | HDMI 8K input |
| `CD` | CD | CD input |
| `TUNER` | Tuner | FM/AM tuner |

To discover which codes your receiver uses, switch inputs on the receiver and watch the telnet output:
```bash
# Watch real-time source changes
(while true; do sleep 1; done) | nc YOUR_RECEIVER_IP 23
# You'll see lines like: SIGAME, SIMPLAY, SITV, SINET, etc.
```

## REST API

The dashboard exposes a full REST API at `/api/v1/`. All POST endpoints accept JSON bodies.

### Status & Info

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/status` | Full receiver state (power, volume, source, channels, etc.) |
| `GET` | `/api/v1/device` | Device config (name, zones, sources, receiver IP) |
| `GET` | `/api/v1/channels` | Channel names and current levels |

### Main Zone Control

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/api/v1/power/on` | — | Turn on main zone |
| `POST` | `/api/v1/power/off` | — | Standby main zone |
| `POST` | `/api/v1/power/toggle` | — | Toggle main zone power |
| `POST` | `/api/v1/volume` | `{"level": 45.0}` | Set volume (0–98) |
| `POST` | `/api/v1/volume/up` | — | Volume up |
| `POST` | `/api/v1/volume/down` | — | Volume down |
| `POST` | `/api/v1/mute/on` | — | Mute |
| `POST` | `/api/v1/mute/off` | — | Unmute |
| `POST` | `/api/v1/mute/toggle` | — | Toggle mute |
| `POST` | `/api/v1/source` | `{"source": "GAME"}` | Select input source |
| `POST` | `/api/v1/surround` | `{"mode": "STEREO"}` | Set surround mode |

### Speaker & Audio

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/api/v1/channel-volume` | `{"channel": "C", "level": 48}` | Set channel trim (38–62, 50=0dB) |
| `POST` | `/api/v1/channel-volume/reset` | — | Reset all channels to 0dB |
| `POST` | `/api/v1/tone` | `{"enabled": true, "bass": 52, "treble": 48}` | Tone controls |
| `POST` | `/api/v1/subwoofer-level` | `{"level": 50}` | Subwoofer level (38–62) |
| `POST` | `/api/v1/dynamic-eq` | `{"enabled": true}` | Dynamic EQ on/off |
| `POST` | `/api/v1/dynamic-volume` | `{"mode": "MED"}` | Dynamic Volume (OFF/LIT/MED/HEV) |
| `POST` | `/api/v1/multeq` | `{"mode": "AUDYSSEY"}` | MultEQ mode |
| `POST` | `/api/v1/eco` | `{"mode": "AUTO"}` | Eco mode (ON/AUTO/OFF) |
| `POST` | `/api/v1/sleep` | `{"minutes": 30}` | Sleep timer |

### Zone 2

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/api/v1/zone2/power/on` | — | Turn on Zone 2 |
| `POST` | `/api/v1/zone2/power/off` | — | Turn off Zone 2 |
| `POST` | `/api/v1/zone2/volume` | `{"level": 35}` | Set Z2 volume |
| `POST` | `/api/v1/zone2/volume/up` | — | Z2 volume up |
| `POST` | `/api/v1/zone2/volume/down` | — | Z2 volume down |
| `POST` | `/api/v1/zone2/mute/on` | — | Z2 mute |
| `POST` | `/api/v1/zone2/mute/off` | — | Z2 unmute |
| `POST` | `/api/v1/zone2/source` | `{"source": "NET"}` | Z2 source |

### Media (HEOS)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/media/play` | Play |
| `POST` | `/api/v1/media/pause` | Pause |
| `POST` | `/api/v1/media/stop` | Stop |
| `POST` | `/api/v1/media/next` | Next track |
| `POST` | `/api/v1/media/previous` | Previous track |
| `GET` | `/api/v1/media/now-playing` | Current track info + play state |

### WebSocket

Connect to `/api/v1/ws` for real-time state updates. The server pushes the full state object on every change.

```javascript
const ws = new WebSocket('ws://YOUR_HOST:8084/api/v1/ws')
ws.onmessage = (e) => console.log(JSON.parse(e.data))
```

### Raw Command

```bash
# Send any raw telnet command
curl -X POST http://localhost:8084/api/v1/command -H 'Content-Type: application/json' -d '{"command": "MVUP"}'
```

## Denon Telnet Protocol Reference

For anyone building on this:

- **Line terminator**: `\r` (0x0D) — NOT `\r\n`
- **Command interval**: minimum 50ms between commands
- **After power on**: wait 1 second before sending commands
- **Volume encoding**: `MV50` = 50 (-30 dB), `MV80` = 80 (0 dB). Three digits for 0.5 steps: `MV805` = 80.5
- **Channel volume**: 38–62 where 50 = 0 dB trim
- **Power**: `PW` = system power, `ZM` = main zone only. When only Z2 is on, `PWON` is true but `ZMOFF`
- **HEOS**: Port 1255, line-delimited JSON, commands like `heos://player/set_play_state?pid=X&state=play`

## Development

### Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
DENON_DASHBOARD_DENON_HOST=192.168.1.100 python -m uvicorn main:app --reload --port 9999

# Frontend
cd frontend
npm install
npm run dev
```

### Build Docker Image

```bash
docker build -t denon-dashboard .
```

## Compatibility

Tested with:
- **Denon AVR-X2700H** (firmware 3.88.614)

Should work with any Denon/Marantz AVR that supports:
- Telnet control on port 23
- HEOS CLI on port 1255 (for media controls)

## Home Assistant Integration

A companion [Home Assistant integration](https://github.com/OxygenLack/denon-dashboard-ha) is available that connects to this dashboard's API, creating `media_player` entities for both zones. Supports full control including volume, source selection, surround modes, and media playback.

Install via [HACS](https://hacs.xyz/) by adding `https://github.com/OxygenLack/denon-dashboard-ha` as a custom repository, or copy the `custom_components/denon_avr_telnet/` folder manually to your HA config directory.

## License

MIT
