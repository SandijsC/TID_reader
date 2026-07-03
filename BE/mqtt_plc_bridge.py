# BE/mqtt_plc_bridge.py

from __future__ import annotations

import json
from typing import Any, Callable

import paho.mqtt.client as mqtt


StateProvider = Callable[[], dict[str, Any]]


class PlcMqttBridge:
    def __init__(
        self,
        broker: str,
        port: int,
        request_topic: str,
        response_topic: str,
        state_provider: StateProvider,
        qos: int = 0,
        client_id: str = "tid-reader-plc-bridge",
    ):
        self.broker = broker
        self.port = port
        self.request_topic = request_topic
        self.response_topic = response_topic
        self.state_provider = state_provider
        self.qos = qos

        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def start(self):
        self.client.connect(self.broker, self.port, keepalive=30)
        self.client.loop_start()
        print(f"MQTT bridge started: {self.broker}:{self.port}")

    def stop(self):
        try:
            self.client.disconnect()
        finally:
            self.client.loop_stop()
            print("MQTT bridge stopped")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"MQTT connected: {reason_code}")
        client.subscribe(self.request_topic, qos=self.qos)
        print(f"Subscribed to MQTT topic: {self.request_topic}")

    def _on_message(self, client, userdata, msg):
        try:
            request = self._parse_request(msg.payload)

            if request.get("msg_type") != "rfid_result":
                return

            crate_id = request.get("crate_id")
            if crate_id is None:
                print("MQTT request ignored: missing crate_id")
                return

            response = self._build_response(crate_id)
            payload = json.dumps(response, separators=(",", ":"))

            client.publish(
                self.response_topic,
                payload,
                qos=self.qos,
                retain=False,
            )

            print(f"MQTT response sent on {self.response_topic}: {payload}")

        except Exception as e:
            print(f"MQTT message handling error: {e}")

    @staticmethod
    def _parse_request(payload: bytes) -> dict[str, Any]:
        text = payload.decode("utf-8").strip()
        data = json.loads(text)

        if not isinstance(data, dict):
            raise ValueError("MQTT payload must be a JSON object")

        request = data.get("request", data)

        if isinstance(request, list):
            if len(request) != 1 or not isinstance(request[0], dict):
                raise ValueError("request list must contain exactly one object")
            request = request[0]

        if not isinstance(request, dict):
            raise ValueError("request must be a JSON object")

        return request

    def _build_response(self, crate_id: Any) -> dict[str, Any]:
        latest_tag = self._get_latest_tag()

        if latest_tag is None:
            return {
                "msg_type": "rfid_result",
                "crate_id": str(crate_id),
                "crate_rejected": True,
                "epc": "",
                "tid_1": "",
                "tid_2": "",
                "barcode": "",
            }

        tids = sorted(latest_tag.tids)

        return {
            "msg_type": "rfid_result",
            "crate_id": str(crate_id),
            "crate_rejected": latest_tag.status != "PASSED",
            "epc": latest_tag.epc,
            "tid_1": tids[0] if len(tids) > 0 else "",
            "tid_2": tids[1] if len(tids) > 1 else "",
            "barcode": latest_tag.barcode,
        }

    def _get_latest_tag(self):
        state = self.state_provider()

        if not state:
            return None

        return max(
            state.values(),
            key=lambda tag: tag.last_seen_at,
        )