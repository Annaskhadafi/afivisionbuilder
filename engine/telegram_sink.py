"""Telegram Bot Notification Sink.

Dispatches instant visual alerts with dynamic captions and JPEG snapshots
directly to Telegram chats, groups, or channels via Telegram Bot API (sendPhoto / sendMessage).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional
import cv2
import numpy as np


def build_multipart_form_data(
    fields: Dict[str, str],
    files: Dict[str, Tuple[str, bytes, str]],
) -> Tuple[bytes, str]:
    """Encode fields and files into multipart/form-data payload with random boundary."""
    boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
    body = bytearray()

    # Append standard string fields
    for name, value in fields.items():
        if value is None:
            continue
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(str(value).encode("utf-8"))
        body.extend(b"\r\n")

    # Append file fields
    for name, (filename, file_bytes, content_type) in files.items():
        if not file_bytes:
            continue
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode("utf-8"))
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode("utf-8"))
        body.extend(file_bytes)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))
    content_type_header = f"multipart/form-data; boundary={boundary}"
    return bytes(body), content_type_header


def send_telegram_photo(
    bot_token: str,
    chat_id: str,
    photo_bytes: bytes,
    caption: str = "",
    parse_mode: str = "HTML",
    disable_notification: bool = False,
    timeout: int = 6,
) -> Dict[str, Any]:
    """Send photo with caption to Telegram chat via sendPhoto API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    fields = {
        "chat_id": chat_id,
        "caption": caption[:1024],  # Telegram max caption length is 1024
        "parse_mode": parse_mode,
    }
    if disable_notification:
        fields["disable_notification"] = "true"

    files = {
        "photo": ("snapshot.jpg", photo_bytes, "image/jpeg"),
    }

    body, content_type = build_multipart_form_data(fields, files)
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type, "User-Agent": "AfiVisionBuilder/Telegram"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": resp_data.get("ok", False),
                "status": "delivered" if resp_data.get("ok") else "error",
                "response": resp_data,
            }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        return {"ok": False, "status": "api_error", "code": e.code, "error": err_msg}
    except Exception as e:
        return {"ok": False, "status": "connection_error", "error": str(e)}


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    parse_mode: str = "HTML",
    disable_notification: bool = False,
    timeout: int = 5,
) -> Dict[str, Any]:
    """Send text message fallback to Telegram chat via sendMessage API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text[:4096],
        "parse_mode": parse_mode,
    }
    if disable_notification:
        payload["disable_notification"] = True

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "AfiVisionBuilder/Telegram"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            return {
                "ok": resp_data.get("ok", False),
                "status": "delivered" if resp_data.get("ok") else "error",
                "response": resp_data,
            }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="ignore")
        return {"ok": False, "status": "api_error", "code": e.code, "error": err_msg}
    except Exception as e:
        return {"ok": False, "status": "connection_error", "error": str(e)}


def format_telegram_caption(template: str, event: Dict[str, Any]) -> str:
    """Interpolate dynamic event properties into template string."""
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")

    ev_type = str(event.get("type", event.get("kind", "ALERT")))
    zone_name = str(event.get("zoneName", event.get("zone_name", event.get("bay_id", "Default Zone"))))
    msg = str(event.get("message", ""))
    track_id = str(event.get("track_id", event.get("trackId", "-")))
    cls = str(event.get("class", event.get("target_class", "-")))
    conf = event.get("confidence", event.get("score"))
    conf_str = f"{float(conf):.2f}" if conf is not None else "-"

    caption = template.replace("{event.type}", ev_type)
    caption = caption.replace("{event.zoneName}", zone_name)
    caption = caption.replace("{zone_name}", zone_name)
    caption = caption.replace("{timestamp}", now_str)
    caption = caption.replace("{event.message}", msg)
    caption = caption.replace("{track_id}", track_id)
    caption = caption.replace("{class}", cls)
    caption = caption.replace("{confidence}", conf_str)
    return caption


def dispatch_telegram_alert(
    event: Dict[str, Any],
    image: Optional[np.ndarray],
    config: Dict[str, Any],
    node_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Dispatch alert to Telegram with anti-spam cooldown and dual snapshot support."""
    bot_token = str(config.get("botToken") or os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    chat_id = str(config.get("chatId") or os.environ.get("TELEGRAM_CHAT_ID") or "").strip()

    template = str(config.get("messageCaption") or config.get("messageTemplate") or
                   "🚨 <b>PERINGATAN SISTEM VISI</b>\n\n"
                   "📌 <b>Kejadian:</b> {event.type}\n"
                   "📍 <b>Zona:</b> {event.zoneName}\n"
                   "🕒 <b>Waktu:</b> {timestamp}\n"
                   "🔍 <b>Detail:</b> {event.message}")

    parse_mode = str(config.get("parseMode", "HTML")).strip()
    cooldown = max(1.0, float(config.get("cooldownSeconds", 5.0) or 5.0))
    disable_notif = bool(config.get("disableNotification", False))

    now = time.time()
    last_sent = float(node_state.get("last_telegram_time", 0.0))

    if last_sent != 0.0 and (now - last_sent) < cooldown:
        return {
            "status": "throttled",
            "cooldownRemaining": round(cooldown - (now - last_sent), 1),
            "timestamp": now,
        }

    caption = format_telegram_caption(template, event)

    # 1. Check if snapshot_bytes was provided by upstream Screenshot Node
    photo_bytes = event.get("snapshot_bytes")

    # 2. If not, fallback to encoding current frame (dual support)
    if not photo_bytes and image is not None and hasattr(image, "shape"):
        try:
            success, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if success:
                photo_bytes = buf.tobytes()
        except Exception:
            photo_bytes = None

    # Delivery execution
    if not bot_token or not chat_id:
        # Mock / simulated delivery mode when tokens not configured
        node_state["last_telegram_time"] = now
        return {
            "status": "simulated_delivered",
            "reason": "Missing Bot Token or Chat ID; simulated successfully",
            "caption": caption,
            "hasPhoto": photo_bytes is not None,
            "timestamp": now,
        }

    # Real dispatch via Telegram API
    if photo_bytes:
        res = send_telegram_photo(bot_token, chat_id, photo_bytes, caption, parse_mode, disable_notif)
    else:
        res = send_telegram_message(bot_token, chat_id, caption, parse_mode, disable_notif)

    node_state["last_telegram_time"] = now

    return {
        "status": res.get("status", "unknown"),
        "ok": res.get("ok", False),
        "caption": caption,
        "hasPhoto": photo_bytes is not None,
        "timestamp": now,
    }
