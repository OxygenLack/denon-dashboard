# Denon AVR Dashboard

A modern, real-time web dashboard for controlling Denon/Marantz AVR receivers. Built with React + FastAPI, communicates via **telnet** (port 23) and **HEOS CLI** (port 1255) — no dependency on the receiver's unreliable built-in web interface.

[![Build](https://github.com/OxygenLack/denon-dashboard/actions/workflows/docker.yml/badge.svg)](https://github.com/OxygenLack/denon-dashboard/actions/workflows/docker.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) ![React 19](https://img.shields.io/badge/React-19-61dafb) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688) ![Docker](https://img.shields.io/badge/Docker-ready-2496ed)

> **Disclaimer:** This is an unofficial, community-developed project. Not affiliated with or endorsed by Denon, Marantz, or Sound United/Masimo. All product names and trademarks are the property of their respective owners.

<div align="center">

| Controls | Audio / EQ |
|:---:|:---:|
| ![Controls](docs/preview.png) | ![Audio EQ](docs/preview_audio_eq.png) |
| **Speakers** | **Health** |
| ![Speakers](docs/preview_speakers.png) | ![Health](docs/preview_health.png) |
| **Zone 2** | |
| ![Zone 2](docs/preview_zone2.png) | |

</div>

## Features

### Main Zone
- **Power** on/off (main zone only — doesn't affect Zone 2)
- **Volume** control with slider, +/- buttons, and mute toggle
- **Input Source** selection with custom names and icons
- **Surround Modes** — cycle through categories (Movie/Music/Game/Pure) or pick any mode directly. Shows cycling order with current/next indicators. Info mode explains each mode's speaker layout, purpose, and quirks on hover (desktop) or via toggle (mobile). Mode list dynamically populated from receiver via OPSMLALL protocol data
- **Internet Radio Browser** — full TuneIn radio browser with category navigation (Local Radio, Trending, Music genres, Sports, Talk, Podcasts, By Location). ~800+ stations preloaded on startup for instant search. Backend caching (1hr TTL) shared across all clients. Play any station directly from the browser. Country/region flag icons, genre icons, station logos
- **Smart Source Detection** — automatically identifies the active HEOS streaming service (Spotify, TuneIn, Bluetooth, etc.) from the `NET` source using HEOS now-playing data. Highlights the correct source button instead of generic "Online Music". Region-locked services (Pandora, SiriusXM) hidden automatically when unavailable
- **Media Controls** — play/pause, next/previous for HEOS/streaming sources
- **Now Playing** — song, artist, station name, album art. Shows stream quality/bitrate when detectable (e.g., "AAC 128 kbps", "Spotify Connect")
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

### 1. Create `compose.yaml`

```yaml
services:
  denon-dashboard:
    image: ghcr.io/oxygenlack/denon-dashboard:latest
    container_name: denon-dashboard
    restart: unless-stopped
    network_mode: host        # required for SSDP auto-discovery
    environment:
      - DENON_DASHBOARD_DENON_HOST=   # leave empty — auto-discovers your receiver
      #- DENON_DASHBOARD_PORT=8080    # change if port 8080 is taken on your host
```

### 2. Start

```bash
docker compose up -d
```

Open `http://YOUR_HOST:8080` — the dashboard will find your receiver automatically.

> **No receiver found?** The dashboard starts immediately and shows a "Searching…" screen while scanning your network. Once found, it connects automatically — no page refresh needed. If it can't find the receiver after ~30 seconds, a setup screen appears where you can enter the IP manually.

### Manual IP (bridge mode / Traefik)

If you use Traefik or can't use `network_mode: host`, set the IP explicitly:

```yaml
services:
  denon-dashboard:
    image: ghcr.io/oxygenlack/denon-dashboard:latest
    container_name: denon-dashboard
    restart: unless-stopped
    ports:
      - "8080:8080"
    environment:
      - DENON_DASHBOARD_DENON_HOST=192.168.1.100   # your receiver's IP
```

> SSDP auto-discovery requires `network_mode: host` because Docker's bridge network blocks multicast. With bridge mode, set `DENON_DASHBOARD_DENON_HOST` explicitly.

## Configuration

All configuration is via environment variables with the `DENON_DASHBOARD_` prefix.

| Variable | Default | Description |
|---|---|---|
| `DENON_DASHBOARD_DENON_HOST` | *(empty)* | Receiver IP. **Leave empty** to auto-discover via SSDP. Set explicitly if using bridge networking or Traefik. |
| `DENON_DASHBOARD_PORT` | `8080` | Dashboard port. Change if 8080 is already in use on your host (e.g. `8084`). |
| `DENON_DASHBOARD_DENON_TELNET_PORT` | `23` | Telnet port — rarely needs changing. |
| `DENON_DASHBOARD_DENON_DEVICE_NAME` | `Denon AVR` | Display name shown in the header. |
| `DENON_DASHBOARD_DENON_ZONE1_NAME` | `Main Zone` | Main zone tab label. |
| `DENON_DASHBOARD_DENON_ZONE2_NAME` | `Zone 2` | Zone 2 tab label. |
| `DENON_DASHBOARD_DENON_SOURCE_NAMES` | `{}` | JSON map of source codes → display names. |
| `DENON_DASHBOARD_HEOS_SOURCES` | `true` | Include HEOS/network sources (Bluetooth, Internet Radio, Spotify, etc.) in the source list. The receiver's `SSFUN` command only reports physical inputs — this adds the missing network sources automatically. Set to `false` to hide them. |
| `DENON_DASHBOARD_THEME` | `gold` | UI accent color. See [Themes](#themes) below. |
| `DENON_DASHBOARD_CORS_ORIGINS` | *(empty)* | Comma-separated list of allowed CORS origins. Empty = same-origin only. Set to `*` to allow all origins (not recommended). |
| `DENON_DASHBOARD_LOG_LEVEL` | `INFO` | Log verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

## Themes

Change the accent color via the `DENON_DASHBOARD_THEME` environment variable:

| Value | Color |
|---|---|
| `gold` | 🟡 Amber/Gold *(default)* |
| `blue` | 🔵 Blue |
| `red` | 🔴 Red |
| `green` | 🟢 Green |
| `olive` | 🫒 Olive / Yellow-green |
| `violet` | 🟣 Violet |
| `purple` | 💜 Purple |
| `pink` | 🩷 Pink |
| `orange` | 🟠 Orange |

```yaml
environment:
  - DENON_DASHBOARD_THEME=purple
```

---

**How auto-discovery works:** On startup, the dashboard sends an SSDP/UPnP multicast search (`239.255.255.250:1900`) to find Denon/Marantz receivers. If SSDP gets no response, it falls back to a subnet port scan (port 23) — slower (~30s) but works on networks where multicast is blocked. The UI shows a "Searching…" spinner while this happens and connects automatically when found. Requires `network_mode: host`.

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

| Method | Endpoint | Body | Description |
|---|---|---|---|
| `POST` | `/api/v1/media/play` | — | Play |
| `POST` | `/api/v1/media/pause` | — | Pause |
| `POST` | `/api/v1/media/stop` | — | Stop |
| `POST` | `/api/v1/media/next` | — | Next track |
| `POST` | `/api/v1/media/previous` | — | Previous track |
| `GET` | `/api/v1/media/now-playing` | — | Current track info + play state |

### Internet Radio

| Method | Endpoint | Parameters | Description |
|---|---|---|---|
| `GET` | `/api/v1/media/radio/browse` | `?cid=...` (optional) | Browse TuneIn directory. Omit `cid` for top-level categories |
| `GET` | `/api/v1/media/radio/search` | `?q=search+terms` | Search cached stations (multi-word, all must match) |
| `POST` | `/api/v1/media/radio/play` | `{"mid": "s280354"}` | Play a station by TuneIn media ID |
| `POST` | `/api/v1/media/radio/refresh` | — | Clear cache and re-preload all stations |

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
- **Marantz Cinema 60**

Should work with any Denon/Marantz AVR that supports:
- Telnet control on port 23
- HEOS CLI on port 1255 (for media controls)

## Home Assistant Integration

A companion [Home Assistant integration](https://github.com/OxygenLack/denon-dashboard-ha) is available that connects to this dashboard's API, creating `media_player` entities for both zones. Supports full control including volume, source selection, surround modes, and media playback.

Install via [HACS](https://hacs.xyz/) by adding `https://github.com/OxygenLack/denon-dashboard-ha` as a custom repository, or copy the `custom_components/denon_avr_telnet/` folder manually to your HA config directory.

## Roadmap

### Known Limitations
- **HEOS source switching** - the receiver maps all HEOS sources (Bluetooth, Spotify, Internet Radio, etc.) to `SINET` internally. Switching between them via telnet is not possible. The dashboard detects and highlights the active service correctly, but the source buttons can't force-switch between HEOS services ([#2](https://github.com/OxygenLack/denon-dashboard/issues/2))

### Planned
- **Night mode / sub presets** — quick-switch subwoofer profiles (e.g., "Movie" vs "Night" with reduced sub level), or a time-based automatic night mode ([requested](https://reddit.com/r/hometheater/comments/1syh2mn/i_got_tired_of_denons_broken_web_ui_so_i_built_my/oiwhfpt/))
- **Tactile transducer support** — show and control tactile transducer channel on the speaker status page ([requested](https://reddit.com/r/hometheater/comments/1syh2mn/i_got_tired_of_denons_broken_web_ui_so_i_built_my/oiwg22o/))
- **Dirac slot selection** — switch between Dirac Live filter slots for receivers with Dirac support ([requested](https://reddit.com/r/hometheater/comments/1syh2mn/i_got_tired_of_denons_broken_web_ui_so_i_built_my/oixqkvf/))
- **HEOS speaker grouping/ungrouping** — group and ungroup HEOS speakers ([requested](https://github.com/OxygenLack/denon-dashboard/issues/6))
- **Audyssey preset switching** (Preset 1 / Preset 2)
- Feature parity with the original Denon/Marantz web UI

**Want more?** Open an [issue](https://github.com/OxygenLack/denon-dashboard/issues) or submit a PR — contributions welcome.

## License

MIT
