# BE/mqtt_plc_bridge.py

from __future__ import annotations
import threading
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
        self._last_response_epc: str | None = None
        self._last_response_lock = threading.Lock()
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

            # This is the important part:
            # MQTT request comes in -> retrieve current RFID state.
            state = self.state_provider()
            latest_tag = self._get_latest_tag_from_state(state)

            self._print_state(crate_id, state, latest_tag)

            response = self._build_response(crate_id, latest_tag)

            payload = json.dumps(response, separators=(",", ":"))

            client.publish(
                self.response_topic,
                payload,
                qos=self.qos,
                retain=False,
            )

            # print(f"MQTT response sent on {self.response_topic}: {payload}")

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

    @staticmethod
    def _get_latest_tag_from_state(state: dict[str, Any]):
        if not state:
            return None

        return max(
            state.values(),
            key=lambda tag: tag.last_seen_at,
        )
    def _build_response(self, crate_id: Any, latest_tag: Any | None) -> dict[str, Any]:
        def failed_response() -> dict[str, Any]:
            return {
                "msg_type": "rfid_result",
                "crate_id": str(crate_id),
                "crate_rejected": True,
                "status": "FAILED",
                "epc": "NO_EPC",
                "tid_1": "",
                "tid_2": "",
                "barcode": "",
            }

        if latest_tag is None:
            return failed_response()

        current_epc = str(latest_tag.epc)

        with self._last_response_lock:
            if self._last_response_epc == current_epc:
                return failed_response()

            self._last_response_epc = current_epc

        tids = sorted(latest_tag.tids)
        status = latest_tag.status

        return {
            "msg_type": "rfid_result",
            "crate_id": str(crate_id),
            "crate_rejected": status != "PASSED",
            "status": status,
            "epc": current_epc,
            "tid_1": tids[0] if len(tids) > 0 else "",
            "tid_2": tids[1] if len(tids) > 1 else "",
            "barcode": latest_tag.barcode,
        }

    def _print_state(self, crate_id: Any, state: dict[str, Any], latest_tag: Any | None) -> None:
        if latest_tag is None:
            print(f"FAILED NO_EPC TIDs: 0")
            return

        print(f"{latest_tag.status} {latest_tag.barcode} TIDs: {latest_tag.tid_count}")
        # print()
        # print(f"MQTT request received for crate_id={crate_id}")
        # print(f"RFID state contains {len(state)} tag(s)")

        # if latest_tag is None:
        #     print("Latest RFID tag: NONE")
        #     return

        # print("Latest RFID tag:")
        # print(f"  epc:          {latest_tag.epc}")
        # print(f"  barcode:      {latest_tag.barcode}")
        # print(f"  tids:         {sorted(latest_tag.tids)}")
        # print(f"  tid_count:    {latest_tag.tid_count}")
        # print(f"  status:       {latest_tag.status}")
        # print(f"  reading_time: {latest_tag.reading_time:.3f}s")
        # print()