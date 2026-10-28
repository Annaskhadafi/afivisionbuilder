"""MQTT Industrial IoT & SCADA Gateway Publisher Node for AFI Vision Builder.

Menerbitkan telemetry deteksi, alarm K3, atau event counting ke broker MQTT
(Eclipse Mosquitto, EMQX, HiveMQ, Node-RED, Siemens PLC Gateway, Home Assistant).
"""

from __future__ import annotations

import datetime
import json
import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("afi.mqtt_gateway")

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    mqtt = None
    PAHO_AVAILABLE = False


class MqttPublisherClient:
    """Klien MQTT persisten thread-safe per host:port."""

    _clients: Dict[str, "MqttPublisherClient"] = {}
    _lock = threading.Lock()

    @classmethod
    def get_client(cls, host: str, port: int, username: str = "", password: str = "") -> "MqttPublisherClient":
        key = f"{host}:{port}:{username}"
        with cls._lock:
            if key not in cls._clients:
                cls._clients[key] = MqttPublisherClient(host, port, username, password)
            return cls._clients[key]

    def __init__(self, host: str, port: int, username: str = "", password: str = ""):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.connected = False
        self._init_lock = threading.Lock()
        self.published_count = 0
        self.last_published_time: float = 0.0

    def connect_if_needed(self) -> bool:
        if not PAHO_AVAILABLE:
            return False
        if self.connected and self.client is not None:
            return True

        with self._init_lock:
            if self.connected and self.client is not None:
                return True
            try:
                # Support both paho-mqtt v1 and v2 API
                client_id = f"afi_vision_{int(time.time())}"
                if hasattr(mqtt, "CallbackAPIVersion"):
                    self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
                else:
                    self.client = mqtt.Client(client_id=client_id)

                if self.username:
                    self.client.username_pw_set(self.username, self.password)

                self.client.connect(self.host, self.port, keepalive=60)
                self.client.loop_start()
                self.connected = True
                logger.info("Terhubung ke MQTT Broker: %s:%d", self.host, self.port)
                return True
            except Exception as e:
                logger.warning("Gagal terhubung ke MQTT Broker %s:%d: %s", self.host, self.port, e)
                self.connected = False
                return False

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False) -> bool:
        if not PAHO_AVAILABLE:
            logger.warning("MQTT tidak tersedia: pasang paho-mqtt")
            return False

        if not self.connect_if_needed():
            return False

        try:
            info = self.client.publish(topic, payload, qos=qos, retain=retain)
            self.published_count += 1
            self.last_published_time = time.time()
            return info.rc == mqtt.MQTT_ERR_SUCCESS if hasattr(info, "rc") else True
        except Exception as e:
            logger.error("Gagal publish ke MQTT topic %s: %s", topic, e)
            self.connected = False
            return False


def process_mqtt_publisher(
    node: Dict[str, Any],
    candidates: List[Dict[str, Any]],
    state: Dict[str, Any],
    now: float
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Runner eksekusi node MQTT Publisher."""
    config = node.get("config", {})
    node_id = str(node.get("id") or "mqtt_publisher")

    host = config.get("brokerHost", "localhost")
    port = int(config.get("brokerPort", 1883))
    username = config.get("username", "")
    password = config.get("password", "")
    topic = config.get("topic", "afivision/alerts")
    qos = int(config.get("qos", 0))
    retain = bool(config.get("retain", False))
    payload_format = config.get("payloadFormat", "json")
    custom_template = config.get("customTemplate", "")
    publish_mode = config.get("publishMode", "on_event")
    min_interval = float(config.get("minPublishIntervalSeconds", 1.0))

    last_time = state.get("last_publish_time", 0.0)
    if now - last_time < min_interval:
        return {"status": "throttled", "published": False}, []

    # Cek apakah syarat publish terpenuhi
    should_publish = False
    event_reason = "periodic"
    if publish_mode == "always":
        should_publish = True
    elif publish_mode == "on_detection":
        should_publish = len(candidates) > 0
        event_reason = "objects_detected"
    elif publish_mode == "on_event":
        has_alert = any(d.get("isViolation") or d.get("isManDown") or d.get("alert") for d in candidates)
        should_publish = has_alert
        event_reason = "safety_alert"

    events = []
    success = False
    if should_publish:
        client = MqttPublisherClient.get_client(host, port, username, password)

        # Siapkan payload
        if payload_format == "custom" and custom_template:
            # Interpolasi template teks
            sample_class = candidates[0].get("class", "none") if candidates else "none"
            payload_str = custom_template.replace("{class}", sample_class)
            payload_str = payload_str.replace("{count}", str(len(candidates)))
            payload_str = payload_str.replace("{timestamp}", datetime.datetime.now().isoformat())
            payload_str = payload_str.replace("{node_id}", node_id)
        else:
            # JSON format
            summary_list = []
            for d in candidates:
                summary_list.append({
                    "class": d.get("class"),
                    "confidence": round(float(d.get("score", d.get("confidence", 0.0))), 3),
                    "track_id": d.get("trackId", d.get("track_id")),
                    "bbox": d.get("bbox"),
                    "attributes": {k: v for k, v in d.items() if k in ("isManDown", "ppeStatus", "plateNumber", "dominantColor")}
                })
            payload_obj = {
                "source": "AfiVisionBuilder",
                "node_id": node_id,
                "timestamp": datetime.datetime.now().isoformat(),
                "reason": event_reason,
                "count": len(candidates),
                "detections": summary_list
            }
            payload_str = json.dumps(payload_obj)

        success = client.publish(topic, payload_str, qos=qos, retain=retain)
        if success:
            state["last_publish_time"] = now
            state["publish_count"] = state.get("publish_count", 0) + 1
            events.append({
                "event_type": "mqtt_message_published",
                "node_id": node_id,
                "topic": topic,
                "qos": qos,
                "count": len(candidates),
                "timestamp": datetime.datetime.now().isoformat()
            })

    status = {
        "broker": f"{host}:{port}",
        "topic": topic,
        "connected": client.connected if 'client' in locals() else False,
        "paho_available": PAHO_AVAILABLE,
        "published": success,
        "total_published": state.get("publish_count", 0)
    }
    return status, events
