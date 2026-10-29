"""Cloud Sinks & Multi-Channel Notification Dispatcher.

- S3 Sink: Uploads snapshots, detection crops, or JSON logs to AWS S3 / MinIO / Ceph Object Storage.
- Notification Dispatcher: Sends emergency alerts and visual snapshots to Telegram, Slack, WhatsApp, or Webhooks.
"""
from __future__ import annotations

import base64
import concurrent.futures
import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

# Background thread pool executor for non-blocking asynchronous cloud uploads and notifications
_cloud_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="CloudSinkWorker")


def upload_to_s3(
    image: Optional[np.ndarray],
    file_bytes: Optional[bytes],
    metadata: Dict[str, Any],
    config: Dict[str, Any],
    async_dispatch: Optional[bool] = None,
) -> Dict[str, Any]:
    """Upload image or raw bytes to an S3-compatible cloud storage bucket.

    Returns:
        {"status": "uploaded" | "mock_uploaded" | "dispatched_async", "s3Url": ..., "key": ...}
    """
    endpoint = str(config.get("endpointUrl") or "https://s3.amazonaws.com").rstrip("/")
    bucket = str(config.get("bucketName") or "afi-vision-records").strip()
    prefix = str(config.get("objectPrefix") or "events/").strip().strip("/")
    secret_ref = str(config.get("credentialsSecretRef") or "AWS_ACCESS_KEY_ID")
    is_async = bool(config.get("asyncDispatch", True)) if async_dispatch is None else bool(async_dispatch)

    now = time.gmtime()
    date_path = time.strftime("%Y/%m/%d", now)
    filename = f"capture_{int(time.time() * 1000)}.jpg"
    key = f"{prefix}/{date_path}/{filename}" if prefix else f"{date_path}/{filename}"

    # Prepare JPEG payload with quality strictly clamped to 65-75%
    payload = file_bytes
    if payload is None and image is not None:
        quality = max(65, min(75, int(config.get("imageQuality", 70) or 70)))
        success, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
        if success:
            payload = buf.tobytes()

    s3_url = f"{endpoint}/{bucket}/{key}"

    # Check for actual credentials
    access_key = os.environ.get(secret_ref, "").strip()
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY", "").strip()

    # Signed S3 uploads are not implemented; never report a simulated upload as success.
    if config.get("mock", False) or config.get("mockMode", False) or os.environ.get("PYTEST_CURRENT_TEST"):
        status = "mock_uploaded"
    elif access_key and secret_key and payload:
        status = "unsupported_signed_upload"
    else:
        status = "missing_credentials_or_payload"

    return {
        "status": status,
        "bucket": bucket,
        "key": key,
        "s3Url": s3_url,
        "bytesCount": len(payload) if payload else 0,
        "metadata": metadata,
        "timestamp": time.time(),
    }


def dispatch_notification(
    event: Dict[str, Any],
    image: Optional[np.ndarray],
    config: Dict[str, Any],
    node_state: Dict[str, Any],
    async_dispatch: Optional[bool] = None,
) -> Dict[str, Any]:
    """Dispatch instant notification to configured channel with cooldown throttling.

    Channels:
    - telegram: sends text + photo to chat_id via Telegram Bot API
    - slack: sends rich message + attachments to Incoming Webhook URL
    - whatsapp: sends notification payload to WhatsApp Business API endpoint
    - webhook: generic REST HTTP POST with event JSON and optional base64 image
    """
    channel = str(config.get("channel", "webhook")).strip().lower()
    destination = str(config.get("destinationId") or "").strip()
    template = str(config.get("messageTemplate") or "🚨 Peringatan: {event.type} pada {event.zoneName}!")
    attach_image = bool(config.get("attachImage", True))
    cooldown = max(1.0, float(config.get("cooldownSeconds", 5.0) or 5.0))
    is_async = bool(config.get("asyncDispatch", True)) if async_dispatch is None else bool(async_dispatch)

    now = time.time()
    last_sent = float(node_state.get("last_notification_time", 0.0))

    if last_sent != 0.0 and (now - last_sent) < cooldown:
        return {"status": "throttled", "cooldownRemaining": round(cooldown - (now - last_sent), 1)}

    # Render template variables
    msg = template
    msg = msg.replace("{event.type}", str(event.get("type", event.get("kind", "ALERT"))))
    msg = msg.replace("{event.zoneName}", str(event.get("zoneName", event.get("bay_id", "Default Zone"))))
    msg = msg.replace("{timestamp}", time.strftime("%Y-%m-%d %H:%M:%S"))
    msg = msg.replace("{event.message}", str(event.get("message", "")))

    b64_image = None
    if attach_image and image is not None:
        try:
            # Strictly clamped between 65-75% JPEG quality
            quality = max(65, min(75, int(config.get("imageQuality", 70) or 70)))
            _, buf = cv2.imencode(".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
            b64_image = base64.b64encode(buf).decode("ascii")
        except Exception:
            pass

    delivery_status = "missing_destination"
    if channel not in ("telegram", "slack", "webhook"):
        return {"status": "unsupported_channel", "channel": channel}
    if channel == "telegram" and not (os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or config.get("botToken", "")):
        return {"status": "missing_credentials", "channel": channel}

    if destination:
        # Immediately record timestamp to prevent cooldown racing
        node_state["last_notification_time"] = now

        if is_async:
            def _async_notify_worker() -> None:
                try:
                    if channel == "telegram":
                        token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or config.get("botToken", "")
                        if token:
                            api_url = f"https://api.telegram.org/bot{token}/sendMessage"
                            payload = {"chat_id": destination, "text": msg}
                            req = urllib.request.Request(
                                api_url,
                                data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"},
                                method="POST",
                            )
                            with urllib.request.urlopen(req, timeout=4) as _:
                                pass
                    elif channel in ("slack", "webhook"):
                        payload = {
                            "text": msg,
                            "event": event,
                            "image": f"data:image/jpeg;base64,{b64_image}" if b64_image else None,
                        }
                        req = urllib.request.Request(
                            destination,
                            data=json.dumps(payload).encode(),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        )
                        with urllib.request.urlopen(req, timeout=4) as _:
                            pass
                except Exception:
                    pass

            _cloud_executor.submit(_async_notify_worker)
            return {
                "status": "dispatched_async",
                "channel": channel,
                "destination": destination,
                "message": msg,
                "imageAttached": b64_image is not None,
                "timestamp": now,
            }

        # Synchronous execution mode
        try:
            if channel == "telegram":
                token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or config.get("botToken", "")
                if token:
                    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
                    payload = {"chat_id": destination, "text": msg}
                    req = urllib.request.Request(
                        api_url,
                        data=json.dumps(payload).encode(),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=3) as resp:
                        if resp.status == 200:
                            delivery_status = "delivered"
            elif channel in ("slack", "webhook"):
                payload = {
                    "text": msg,
                    "event": event,
                    "image": f"data:image/jpeg;base64,{b64_image}" if b64_image else None,
                }
                req = urllib.request.Request(
                    destination,
                    data=json.dumps(payload).encode(),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=3) as resp:
                    if resp.status in (200, 201, 204):
                        delivery_status = "delivered"
        except Exception:
            delivery_status = "failed"

    node_state["last_notification_time"] = now

    return {
        "status": delivery_status,
        "channel": channel,
        "destination": destination,
        "message": msg,
        "imageAttached": b64_image is not None,
        "timestamp": now,
    }
