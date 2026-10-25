"""Media Gateway and Consumer IP Camera (Ezviz, Tapo, Dahua/Imou) Manager.

Supports:
- go2rtc / MediaMTX / NVR integration
- Ezviz, TP-Link Tapo, Dahua/Imou, Generic RTSP URL construction
- Public IP, DDNS domain, and LAN addressing with custom ports
- Stream probing and connectivity testing
- Dynamic stream registration to go2rtc via REST API
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import cv2

logger = logging.getLogger("visonode.media_gateway")


def sanitize_host(host: str) -> str:
    """Strip protocol prefixes or slashes if user typed http:// or rtsp:// in host field."""
    h = (host or "").strip()
    h = re.sub(r"^[a-zA-Z]+://", "", h)
    return h.split("/")[0].strip()


def build_camera_rtsp_url(
    brand: str,
    host: str,
    port: int | str = 554,
    username: str = "admin",
    password: str = "",
    quality: str = "main",  # "main" | "sub"
    custom_path: str = "",
) -> str:
    """Build standardized RTSP/HLS URL for consumer IP cameras (Ezviz, Tapo, Dahua, Generic).

    Supports Local LAN IPs, Public IPs, DDNS hostnames with custom ports, and full HTTP/HTTPS/HLS stream URLs.
    """
    raw_host = (host or "").strip()
    if raw_host.startswith(("http://", "https://", "rtsp://", "rtsps://")):
        return resolve_stream_url(raw_host)

    clean_host = sanitize_host(host)
    if not clean_host:
        raise ValueError("Host/IP kamera tidak boleh kosong.")

    try:
        port_num = int(port or 554)
    except (ValueError, TypeError):
        port_num = 554

    brand_norm = (brand or "generic").lower().strip()
    u_enc = urllib.parse.quote(username or "admin")
    p_enc = urllib.parse.quote(password or "")
    auth = f"{u_enc}:{p_enc}@" if password else f"{u_enc}@"

    if brand_norm == "ezviz":
        # Ezviz standard RTSP port is 554. Username is always 'admin', password is the 6-letter verification code.
        # Main stream (HD): /h264_stream or /live/main
        # Sub stream (Smooth/SD): /live/sub or /Streaming/Channels/102
        auth = f"admin:{p_enc}@"
        if quality == "sub":
            path = "Streaming/Channels/102"
        else:
            path = "h264_stream"
        return f"rtsp://{auth}{clean_host}:{port_num}/{path}"

    elif brand_norm == "tapo":
        # TP-Link Tapo: requires camera account created in Tapo App -> Device Settings -> Advanced -> Camera Account
        # Stream 1 = 1080p/2K (Main), Stream 2 = 360p (Sub)
        stream_name = "stream2" if quality == "sub" else "stream1"
        return f"rtsp://{auth}{clean_host}:{port_num}/{stream_name}"

    elif brand_norm in ("dahua", "imou"):
        # Dahua / Imou standard: /cam/realmonitor?channel=1&subtype=0 (main) or subtype=1 (sub)
        subtype = "1" if quality == "sub" else "0"
        return f"rtsp://{auth}{clean_host}:{port_num}/cam/realmonitor?channel=1&subtype={subtype}"

    else:
        # Generic RTSP or custom path
        path = (custom_path or "").lstrip("/")
        if not path:
            path = "live/main" if quality != "sub" else "live/sub"
        return f"rtsp://{auth}{clean_host}:{port_num}/{path}"


def resolve_stream_url(url: str) -> str:
    """Resolve camera URLs to direct playable media streams.

    If the user inputs an HTML web player page (e.g. Dishub ATCS, MediaMTX web player,
    such as 'https://itscctv-dishub.bogorkab.go.id/stream/SENTUL2/'),
    this automatically resolves it to the underlying HLS stream ('.../index.m3u8').
    """
    url = (url or "").strip()
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        if url.endswith((".m3u8", ".flv", ".mp4", ".ts", ".mjpeg", ".cgi")):
            return url
        # Check {url}/index.m3u8 directly first (MediaMTX standard used by Dishub/ATCS)
        candidate = f"{url.rstrip('/')}/index.m3u8"
        try:
            import urllib.request
            req = urllib.request.Request(candidate, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    ct = str(resp.headers.get("Content-Type", "")).lower()
                    if "mpegurl" in ct or "apple" in ct or True:
                        return candidate
        except Exception:
            pass

        # Check HTML content for HLS source references
        try:
            import urllib.request
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
                m = re.search(r"loadSource\(['\"]([^'\"?]+)", html)
                if m:
                    return urllib.parse.urljoin(url, m.group(1))
                m_src = re.search(r"<source[^>]+src=['\"]([^'\"]+\.m3u8)", html)
                if m_src:
                    return urllib.parse.urljoin(url, m_src.group(1))
        except Exception:
            pass
    return url


def test_camera_connection(rtsp_url: str, timeout_seconds: float = 4.0) -> Dict[str, Any]:
    """Probe an RTSP or HTTP camera stream to verify reachability and credentials."""
    import os
    import time

    if not rtsp_url:
        return {"success": False, "error": "URL kamera kosong."}

    # Automatically resolve web CCTV player pages (e.g. Dishub / MediaMTX HLS)
    resolved_url = resolve_stream_url(rtsp_url)

    # Force TCP transport for reliable testing through firewalls/WAN/IP Public
    prev_opts = os.environ.get("OPENCV_FFMPEG_CAPTURE_OPTIONS")
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    cap = None
    start_time = time.monotonic()
    try:
        cap = cv2.VideoCapture(resolved_url)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Attempt to read a frame
        ret, frame = cap.read()
        elapsed = round(time.monotonic() - start_time, 2)

        if ret and frame is not None and frame.size > 0:
            h, w = frame.shape[:2]
            msg = f"Koneksi berhasil! Resolusi {w}x{h} ({elapsed}s)"
            if resolved_url != rtsp_url:
                msg += f" [Auto-resolved: {resolved_url}]"
            return {
                "success": True,
                "width": int(w),
                "height": int(h),
                "latency_seconds": elapsed,
                "message": msg,
                "resolved_url": resolved_url,
            }
        else:
            return {
                "success": False,
                "latency_seconds": elapsed,
                "error": "Kamera merespons tetapi tidak dapat mengirimkan frame gambar. Periksa Verification Code / Password atau port forwarding.",
            }
    except Exception as exc:
        elapsed = round(time.monotonic() - start_time, 2)
        return {
            "success": False,
            "latency_seconds": elapsed,
            "error": f"Gagal terhubung ke kamera: {str(exc)}",
        }
    finally:
        if cap is not None:
            cap.release()
        if prev_opts is not None:
            os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = prev_opts
        elif "OPENCV_FFMPEG_CAPTURE_OPTIONS" in os.environ:
            del os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"]


class MediaGatewayClient:
    """Client for querying and managing streams on a go2rtc / RTSP Gateway instance."""

    def __init__(self, gateway_url: str = "http://127.0.0.1:1984", rtsp_base: str = "rtsp://127.0.0.1:8554") -> None:
        self.gateway_url = (gateway_url or "http://127.0.0.1:1984").rstrip("/")
        self.rtsp_base = (rtsp_base or "rtsp://127.0.0.1:8554").rstrip("/")

    def get_status(self) -> Dict[str, Any]:
        """Check if go2rtc API is reachable."""
        import urllib.request
        import json

        api_url = f"{self.gateway_url}/api"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "AfiVisionBuilder"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                return {
                    "online": True,
                    "url": self.gateway_url,
                    "version": data.get("version", "go2rtc"),
                }
        except Exception as exc:
            return {
                "online": False,
                "url": self.gateway_url,
                "error": str(exc),
            }

    def list_streams(self) -> List[Dict[str, Any]]:
        """List all configured and active streams from go2rtc REST API."""
        import urllib.request
        import json

        api_url = f"{self.gateway_url}/api/streams"
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "AfiVisionBuilder"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
                streams = []
                # go2rtc returns dict of {stream_name: stream_info}
                if isinstance(data, dict):
                    for name, details in data.items():
                        producers = details.get("producers", []) if isinstance(details, dict) else []
                        consumers = details.get("consumers", []) if isinstance(details, dict) else []
                        streams.append({
                            "name": name,
                            "rtsp_url": f"{self.rtsp_base}/{name}",
                            "producers_count": len(producers),
                            "consumers_count": len(consumers),
                            "is_online": len(producers) > 0 or details is not None,
                        })
                return streams
        except Exception as exc:
            logger.debug("Failed to list streams from go2rtc at %s: %s", self.gateway_url, exc)
            return []

    def register_stream(self, stream_name: str, source_url: str) -> Dict[str, Any]:
        """Register or update a stream on go2rtc dynamically via PUT /api/streams."""
        import urllib.request
        import urllib.parse
        import json

        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", (stream_name or "camera").strip())
        query = urllib.parse.urlencode({"name": clean_name, "src": source_url})
        api_url = f"{self.gateway_url}/api/streams?{query}"

        try:
            req = urllib.request.Request(api_url, method="PUT", headers={"User-Agent": "AfiVisionBuilder"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                status = resp.status
                return {
                    "success": 200 <= status < 300,
                    "name": clean_name,
                    "rtsp_url": f"{self.rtsp_base}/{clean_name}",
                    "gateway_url": self.gateway_url,
                }
        except Exception as exc:
            return {
                "success": False,
                "name": clean_name,
                "error": f"Gagal mendaftarkan stream ke gateway: {str(exc)}",
            }
