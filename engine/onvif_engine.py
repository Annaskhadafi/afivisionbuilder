# -*- coding: utf-8 -*-
"""ONVIF Engine for AFI Vision Builder.

Provides lightweight, robust ONVIF camera discovery, authentication (HTTP Digest & WS-Security),
profile inspection, and RTSP stream URI resolution adapted from Open-NVR.
Pure Python implementation with httpx and standard socket library (zero heavy zeep dependencies).
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import html
import logging
import re
import secrets
import socket
import uuid
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger("afivision.onvif")

# Common ONVIF candidate ports across major vendors (Hikvision, Dahua, Uniview, Tiandy, Bardi, TP-Link Tapo)
ONVIF_CANDIDATE_PORTS: tuple[int, ...] = (80, 554, 8000, 8080, 8899, 2020, 8088, 443, 8443)

# Namespaces
SOAP_NS = "http://www.w3.org/2003/05/soap-envelope"
TDS_NS = "http://www.onvif.org/ver10/device/wsdl"
TRT_NS = "http://www.onvif.org/ver10/media/wsdl"
TT_NS = "http://www.onvif.org/ver10/schema"
TPT_NS = "http://www.onvif.org/ver20/ptz/wsdl"


def _soap_envelope(body: str) -> str:
    """Wrap body XML in standard ONVIF SOAP envelope."""
    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<soap:Envelope xmlns:soap="{SOAP_NS}" '
        f'xmlns:tds="{TDS_NS}" '
        f'xmlns:trt="{TRT_NS}" '
        f'xmlns:tt="{TT_NS}" '
        f'xmlns:tptz="{TPT_NS}">\n'
        f'  <soap:Body>\n    {body}\n  </soap:Body>\n'
        f"</soap:Envelope>"
    )


def _soap_envelope_wsse(body: str, username: str, password: str) -> str:
    """Wrap request with WS-Security UsernameToken PasswordDigest."""
    nonce_raw = secrets.token_bytes(20)
    nonce = base64.b64encode(nonce_raw).decode("ascii")
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    password_digest = base64.b64encode(
        hashlib.sha1(nonce_raw + created.encode("utf-8") + password.encode("utf-8")).digest()
    ).decode("ascii")

    return (
        f'<?xml version="1.0" encoding="utf-8"?>\n'
        f'<soap:Envelope xmlns:soap="{SOAP_NS}" '
        f'xmlns:tds="{TDS_NS}" '
        f'xmlns:trt="{TRT_NS}" '
        f'xmlns:tt="{TT_NS}" '
        f'xmlns:tptz="{TPT_NS}" '
        f'xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd" '
        f'xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">\n'
        f"  <soap:Header>\n"
        f'    <wsse:Security soap:mustUnderstand="1">\n'
        f"      <wsse:UsernameToken>\n"
        f"        <wsse:Username>{html.escape(username)}</wsse:Username>\n"
        f'        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest">{password_digest}</wsse:Password>\n'
        f'        <wsse:Nonce EncodingType="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary">{nonce}</wsse:Nonce>\n'
        f"        <wsu:Created>{created}</wsu:Created>\n"
        f"      </wsse:UsernameToken>\n"
        f"    </wsse:Security>\n"
        f"  </soap:Header>\n"
        f'  <soap:Body>\n    {body}\n  </soap:Body>\n'
        f"</soap:Envelope>"
    )


async def _onvif_request(
    url: str,
    body: str,
    username: str = "",
    password: str = "",
    timeout: float = 3.5,
) -> tuple[int, str]:
    """Execute ONVIF SOAP POST request with HTTP Digest auth and WSSE fallback."""
    headers = {"Content-Type": "application/soap+xml; charset=utf-8"}

    async def _post(client: httpx.AsyncClient, payload: str) -> tuple[int, str]:
        resp = await client.post(url, content=payload, headers=headers)
        return resp.status_code, resp.text

    # 1. Try plain or HTTP Digest
    auth = httpx.DigestAuth(username, password) if username and password else None
    try:
        async with httpx.AsyncClient(timeout=timeout, verify=False, auth=auth) as client:
            status, text = await _post(client, _soap_envelope(body))
            if status in (200, 400, 404, 500) and "Fault" not in text:
                return status, text
            if status == 200:
                return status, text
    except Exception as e:
        logger.debug(f"HTTP Digest attempt failed for {url}: {e}")

    # 2. Fallback to WS-Security if credentials provided
    if username and password:
        try:
            async with httpx.AsyncClient(timeout=timeout, verify=False) as client:
                status, text = await _post(client, _soap_envelope_wsse(body, username, password))
                return status, text
        except Exception as e:
            logger.debug(f"WSSE attempt failed for {url}: {e}")

    return 0, ""


async def probe_onvif_endpoint(
    ip: str, port: int = 80, timeout: float = 0.8, scheme: str = "http"
) -> dict[str, Any] | None:
    """Probe an IP:port for ONVIF service by sending unauthenticated GetSystemDateAndTime."""
    url = f"{scheme}://{ip}:{port}/onvif/device_service"
    body = "<tds:GetSystemDateAndTime/>"
    try:
        status, text = await _onvif_request(url, body, timeout=timeout)
        # Any standard ONVIF device answers 200 or 401 with SOAP XML
        if status in (200, 401) and ("Envelope" in text or "GetSystemDateAndTimeResponse" in text):
            return {
                "ip": ip,
                "port": port,
                "scheme": scheme,
                "service_url": url,
                "needs_auth": status == 401 or "Fault" in text,
            }
    except Exception:
        pass
    return None


def get_local_ip_subnets() -> list[str]:
    """Retrieve local network IPv4 subnet prefixes (e.g. ['192.168.1'])."""
    subnets = set()
    try:
        hostname = socket.gethostname()
        for addr_info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ip = addr_info[4][0]
            if not ip.startswith("127."):
                parts = ip.split(".")
                if len(parts) == 4:
                    subnets.add(f"{parts[0]}.{parts[1]}.{parts[2]}")
    except Exception:
        pass

    # Fallback standard private subnets if detection empty
    if not subnets:
        subnets.add("192.168.1")
    return list(subnets)


async def discover_onvif_devices(timeout: float = 2.5) -> list[dict[str, Any]]:
    """Discover ONVIF cameras on local network via WS-Discovery UDP Multicast and Fast Port Probe."""
    discovered_devices: dict[str, dict[str, Any]] = {}

    # 1. WS-Discovery Multicast UDP probe
    probe_id = str(uuid.uuid4())
    ws_probe = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
        'xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing" '
        'xmlns:tns="http://schemas.xmlsoap.org/ws/2005/04/discovery">\n'
        "  <soap:Header>\n"
        "    <wsa:Action>http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action>\n"
        f"    <wsa:MessageID>urn:uuid:{probe_id}</wsa:MessageID>\n"
        "    <wsa:To>urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>\n"
        "  </soap:Header>\n"
        "  <soap:Body>\n"
        "    <tns:Probe/>\n"
        "  </soap:Body>\n"
        "</soap:Envelope>"
    ).encode("utf-8")

    def _listen_multicast():
        hits = []
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            # Send multicast to 239.255.255.250:3702
            sock.sendto(ws_probe, ("239.255.255.250", 3702))
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < timeout:
                try:
                    data, addr = sock.recvfrom(4096)
                    resp_text = data.decode("utf-8", errors="ignore")
                    if "ProbeMatches" in resp_text:
                        # Extract XAddrs
                        xaddrs = re.findall(r"<(?:\w+:)?XAddrs>([^<]+)</(?:\w+:)?XAddrs>", resp_text)
                        for xa in xaddrs:
                            for url in xa.split():
                                p = urlparse(url)
                                hits.append({
                                    "ip": p.hostname or addr[0],
                                    "port": p.port or 80,
                                    "scheme": p.scheme or "http",
                                    "service_url": url,
                                    "source": "ws-discovery",
                                })
                except socket.timeout:
                    break
                except Exception:
                    break
        except Exception as e:
            logger.debug(f"Multicast discovery exception: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass
        return hits

    try:
        loop = asyncio.get_running_loop()
        ws_hits = await loop.run_in_executor(None, _listen_multicast)
        for hit in ws_hits:
            key = f"{hit['ip']}:{hit['port']}"
            discovered_devices[key] = hit
    except Exception as e:
        logger.debug(f"WS-Discovery failed: {e}")

    # 2. Targeted candidate port probe for discovered devices or local gateway
    subnets = get_local_ip_subnets()
    probe_targets = []
    # Probe common router / camera IPs
    for s in subnets:
        for last_octet in [1, 10, 50, 64, 100, 108, 128, 200]:
            target_ip = f"{s}.{last_octet}"
            for p in (80, 554, 8000, 8080):
                probe_targets.append((target_ip, p))

    # Fast async gather bounded
    semaphore = asyncio.Semaphore(20)

    async def _bound_probe(tip: str, tport: int):
        async with semaphore:
            res = await probe_onvif_endpoint(tip, tport, timeout=0.4)
            if res:
                res["source"] = "probe"
                k = f"{res['ip']}:{res['port']}"
                discovered_devices[k] = res

    probe_tasks = [_bound_probe(tip, tp) for tip, tp in probe_targets[:40]]
    if probe_tasks:
        await asyncio.gather(*probe_tasks, return_exceptions=True)

    return list(discovered_devices.values())


async def get_device_information(
    ip: str, username: str, password: str, port: int = 80, scheme: str = "http"
) -> dict[str, str]:
    """Retrieve camera device info (Manufacturer, Model, Firmware, Serial)."""
    url = f"{scheme}://{ip}:{port}/onvif/device_service"
    body = "<tds:GetDeviceInformation/>"
    status, text = await _onvif_request(url, body, username, password)

    info = {
        "manufacturer": "Universal ONVIF",
        "model": "Generic IP Camera",
        "firmware": "Unknown",
        "serial": "Unknown",
    }
    if status == 200 and text:
        for field, key in [
            ("Manufacturer", "manufacturer"),
            ("Model", "model"),
            ("FirmwareVersion", "firmware"),
            ("SerialNumber", "serial"),
        ]:
            match = re.search(rf"<(?:\w+:)?{field}>([^<]*)</(?:\w+:)?{field}>", text)
            if match:
                info[key] = html.unescape(match.group(1).strip())
    return info


async def get_camera_profiles_and_rtsp(
    ip: str, username: str, password: str, port: int = 80, scheme: str = "http"
) -> dict[str, Any]:
    """Test credentials, fetch profiles, and resolve RTSP stream URIs."""
    device_info = await get_device_information(ip, username, password, port, scheme)

    # Resolve Media Service URL
    media_url = f"{scheme}://{ip}:{port}/onvif/media_service"
    # Also check via GetCapabilities if possible
    cap_body = "<tds:GetCapabilities><tds:Category>Media</tds:Category></tds:GetCapabilities>"
    status_cap, text_cap = await _onvif_request(
        f"{scheme}://{ip}:{port}/onvif/device_service", cap_body, username, password
    )
    if status_cap == 200 and text_cap:
        m_xaddr = re.search(r"<(?:\w+:)?Media>.*?<(?:\w+:)?XAddr>([^<]+)</(?:\w+:)?XAddr>", text_cap, re.DOTALL)
        if m_xaddr:
            media_url = html.unescape(m_xaddr.group(1).strip())

    # Get Profiles
    prof_body = "<trt:GetProfiles/>"
    status_prof, text_prof = await _onvif_request(media_url, prof_body, username, password)
    if status_prof != 200 or not text_prof:
        # Try alternate path
        alt_url = f"{scheme}://{ip}:{port}/onvif/Media"
        status_prof, text_prof = await _onvif_request(alt_url, prof_body, username, password)

    profiles: list[dict[str, Any]] = []
    if status_prof == 200 and text_prof:
        # Regex parse profiles tolerant of attribute order
        for m in re.finditer(r"<(?:\\w+:)?Profiles\\b([^>]*)>(.*?)</(?:\\w+:)?Profiles>", text_prof, re.DOTALL):
            attrs, block = m.group(1), m.group(2)
            tok_match = re.search(r'token="([^"]+)"', attrs)
            if not tok_match:
                continue
            token = tok_match.group(1)
            name_m = re.search(r"<(?:\\w+:)?Name>([^<]+)</(?:\\w+:)?Name>", block)
            p_name = html.unescape(name_m.group(1).strip()) if name_m else token

            width, height = 640, 360
            bounds_match = re.search(r'width="(\d+)"\s+height="(\d+)"', block)
            if bounds_match:
                width = int(bounds_match.group(1))
                height = int(bounds_match.group(2))

            fps = 25
            fps_m = re.search(r"<(?:\\w+:)?FrameRateLimit>(\d+)</(?:\\w+:)?FrameRateLimit>", block)
            if fps_m:
                fps = int(fps_m.group(1))

            # Fetch Stream URI for this profile
            uri_body = (
                f"<trt:GetStreamUri>\n"
                f"  <trt:StreamSetup>\n"
                f"    <tt:Stream>RTP-Unicast</tt:Stream>\n"
                f"    <tt:Transport><tt:Protocol>RTSP</tt:Protocol></tt:Transport>\n"
                f"  </trt:StreamSetup>\n"
                f"  <trt:ProfileToken>{token}</trt:ProfileToken>\n"
                f"</trt:GetStreamUri>"
            )
            uri_status, uri_text = await _onvif_request(media_url, uri_body, username, password)
            stream_uri = ""
            if uri_status == 200 and uri_text:
                u_match = re.search(r"<(?:\w+:)?Uri>([^<]+)</(?:\w+:)?Uri>", uri_text)
                if u_match:
                    stream_uri = html.unescape(u_match.group(1).strip())
                    # Embed username & password into RTSP URI if omitted
                    if username and password and "://" in stream_uri and "@" not in stream_uri:
                        parts = stream_uri.split("://", 1)
                        stream_uri = f"{parts[0]}://{username}:{password}@{parts[1]}"

            is_substream = (width <= 1280 and height <= 720) or "sub" in p_name.lower() or "ch1_sub" in stream_uri.lower()

            profiles.append({
                "token": token,
                "name": p_name,
                "width": width,
                "height": height,
                "fps": fps,
                "stream_uri": stream_uri,
                "is_ai_recommended": is_substream,
                "profile_label": f"{p_name} ({width}x{height} - {'⚡ Rekomendasi AI Vision' if is_substream else 'HD Penuh'})",
            })

    # Sort profiles so AI recommended / sub stream appears first
    profiles.sort(key=lambda p: (not p["is_ai_recommended"], p["width"] * p["height"]))

    return {
        "ip": ip,
        "port": port,
        "scheme": scheme,
        "device_info": device_info,
        "profiles": profiles,
        "authenticated": True,
    }


async def ptz_continuous_move(
    ip: str,
    username: str,
    password: str,
    profile_token: str,
    x: float = 0.0,
    y: float = 0.0,
    zoom: float = 0.0,
    port: int = 80,
    scheme: str = "http",
) -> bool:
    """Send PTZ ContinuousMove vector to camera."""
    ptz_url = f"{scheme}://{ip}:{port}/onvif/ptz_service"
    body = (
        f"<tptz:ContinuousMove>\n"
        f"  <tptz:ProfileToken>{profile_token}</tptz:ProfileToken>\n"
        f"  <tptz:Velocity>\n"
        f'    <tt:PanTilt x="{x:.2f}" y="{y:.2f}" space="http://www.onvif.org/ver10/tptz/PanTiltSpaces/VelocityGenericSpace"/>\n'
        f'    <tt:Zoom x="{zoom:.2f}" space="http://www.onvif.org/ver10/tptz/ZoomSpaces/VelocityGenericSpace"/>\n'
        f"  </tptz:Velocity>\n"
        f"</tptz:ContinuousMove>"
    )
    status, _ = await _onvif_request(ptz_url, body, username, password)
    return status == 200


async def ptz_stop(
    ip: str, username: str, password: str, profile_token: str, port: int = 80, scheme: str = "http"
) -> bool:
    """Send PTZ Stop command to camera."""
    ptz_url = f"{scheme}://{ip}:{port}/onvif/ptz_service"
    body = (
        f"<tptz:Stop>\n"
        f"  <tptz:ProfileToken>{profile_token}</tptz:ProfileToken>\n"
        f"  <tptz:PanTilt>true</tptz:PanTilt>\n"
        f"  <tptz:Zoom>true</tptz:Zoom>\n"
        f"</tptz:Stop>"
    )
    status, _ = await _onvif_request(ptz_url, body, username, password)
    return status == 200
