"""SSDP-based discovery for Denon/Marantz AVR receivers."""
from __future__ import annotations

import asyncio
import logging
import re
import socket
import time
from typing import Any

_LOGGER = logging.getLogger(__name__)

SSDP_ADDR = "239.255.255.255"
SSDP_PORT = 1900
HEOS_PORT = 1255
TELNET_PORT = 23

SSDP_TARGETS = [
    "urn:schemas-denon-com:device:ACT-Denon:1",
    "urn:schemas-denon-com:device:ZoneDevice:1",
    "urn:schemas-denon-com:device:MediaRenderer:1",
]


def _send_ssdp(st: str, timeout: float) -> list[dict[str, Any]]:
    """Send SSDP M-SEARCH and collect responses (blocking)."""
    msg = (
        "M-SEARCH * HTTP/1.1\r\n"
        f"HOST: {SSDP_ADDR}:{SSDP_PORT}\r\n"
        'MAN: "ssdp:discover"\r\n'
        "MX: 2\r\n"
        f"ST: {st}\r\n"
        "\r\n"
    ).encode()

    results: list[dict[str, Any]] = []
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 4)
        sock.settimeout(timeout)
        sock.sendto(msg, (SSDP_ADDR, SSDP_PORT))

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                data, addr = sock.recvfrom(4096)
                text = data.decode(errors="ignore")
                ip = addr[0]
                location = re.search(r"(?i)LOCATION:\s*(.+)", text)
                server = re.search(r"(?i)SERVER:\s*(.+)", text)
                usn = re.search(r"(?i)USN:\s*(.+)", text)
                results.append({
                    "ip": ip,
                    "location": location.group(1).strip() if location else None,
                    "server": server.group(1).strip() if server else None,
                    "usn": usn.group(1).strip() if usn else None,
                })
            except socket.timeout:
                break
        sock.close()
    except Exception as exc:
        _LOGGER.debug("SSDP error for %s: %s", st, exc)

    return results


def _probe_port(ip: str, port: int, timeout: float = 1.0) -> bool:
    """Check if a TCP port is open."""
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False


def _get_model_from_location(location: str | None) -> str | None:
    """Fetch UPnP device description and extract model/friendly name."""
    if not location:
        return None
    try:
        import ssl
        import urllib.request
        import xml.etree.ElementTree as ET

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(location, timeout=2, context=ctx) as r:
            xml_data = r.read().decode(errors="ignore")
        root = ET.fromstring(xml_data)
        for path in (".//{*}modelName", ".//{*}friendlyName", ".//modelName", ".//friendlyName"):
            el = root.find(path)
            if el is not None and el.text:
                return el.text.strip()
    except Exception:
        pass
    return None


async def discover_receivers(timeout: float = 4.0) -> list[dict[str, Any]]:
    """
    Discover Denon/Marantz AVR receivers on the local network via SSDP/UPnP.
    Returns list of dicts: {ip, model, telnet_port, heos_available}
    """
    seen: dict[str, dict] = {}

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(None, _send_ssdp, st, timeout - 1.0)
        for st in SSDP_TARGETS
    ]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    for results in results_list:
        if isinstance(results, Exception):
            continue
        for r in results:
            ip = r["ip"]
            if ip not in seen:
                seen[ip] = r

    if not seen:
        _LOGGER.info("SSDP discovery found no devices")
        return []

    async def enrich(ip: str, info: dict) -> dict:
        model = await loop.run_in_executor(None, _get_model_from_location, info.get("location"))
        telnet_ok = await loop.run_in_executor(None, _probe_port, ip, TELNET_PORT, 1.0)
        heos_ok = await loop.run_in_executor(None, _probe_port, ip, HEOS_PORT, 1.0)
        return {
            "ip": ip,
            "model": model or "Denon/Marantz AVR",
            "telnet_port": TELNET_PORT if telnet_ok else None,
            "heos_available": heos_ok,
        }

    enriched = await asyncio.gather(*[enrich(ip, info) for ip, info in seen.items()])
    found = [d for d in enriched if d["telnet_port"] is not None]
    _LOGGER.info("Discovery found %d receiver(s): %s", len(found), [d["ip"] for d in found])
    return found
