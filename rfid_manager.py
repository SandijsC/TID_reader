# rfid_manager.py

from __future__ import annotations

import copy
import threading
import time
from queue import Queue, Empty
from typing import Optional

from FE.dashboard import run_dash, set_dashboard_state_provider

from BE.models import RFIDTag
from BE.xml_reader import XMLReader
from BE.tag_manager import TagManager
from BE.xml_parser import XMLParser
from BE.reader_controller import ReaderController
from BE.connection import Connection
from BE.mqtt_plc_bridge import PlcMqttBridge

from config import (
    HEARTBEAT_INTERVAL,
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_REQUEST_TOPIC,
    MQTT_RESPONSE_TOPIC,
    MQTT_QOS,
)


class RfidManager:
    def __init__(self, use_mqtt: bool = True):
        self.use_mqtt = use_mqtt

        self.tag_manager = TagManager()
        self._lock = threading.RLock()

        self._stop_event: Optional[threading.Event] = None
        self._rfid_queue: Optional[Queue] = None
        self._queue_thread: Optional[threading.Thread] = None
        self._dashboard_thread: Optional[threading.Thread] = None

        self.connection: Optional[Connection] = None
        self.parser: Optional[XMLParser] = None
        self.reader: Optional[XMLReader] = None
        self.controller: Optional[ReaderController] = None
        self.mqtt_bridge: Optional[PlcMqttBridge] = None

        self._reading_started = False
        self._dashboard_started = False

        set_dashboard_state_provider(
            self.getDashboardState,
            self.clearData,
        )

    def startReading(self) -> None:
        if self._reading_started:
            return

        self._stop_event = threading.Event()
        self._rfid_queue = Queue()

        self.connection = Connection()
        self.parser = XMLParser()

        self.reader = XMLReader(
            connection=self.connection,
            parser=self.parser,
            event_queue=self._rfid_queue,
        )

        self.controller = ReaderController(
            connection=self.connection,
            reader=self.reader,
            heartbeat_interval=HEARTBEAT_INTERVAL,
        )

        self._queue_thread = threading.Thread(
            target=self._processRfidQueue,
            args=(self._stop_event, self._rfid_queue),
            daemon=True,
        )
        self._queue_thread.start()

        if self.use_mqtt:
            self.mqtt_bridge = PlcMqttBridge(
                broker=MQTT_BROKER,
                port=MQTT_PORT,
                request_topic=MQTT_REQUEST_TOPIC,
                response_topic=MQTT_RESPONSE_TOPIC,
                state_provider=self.getDashboardState,
                qos=MQTT_QOS,
            )
            self.mqtt_bridge.start()

        try:
            self.controller.start()
            self._reading_started = True
            print("RFID reading started")

        except Exception:
            self.stopReading()
            raise

    def stopReading(self) -> None:
        if self._stop_event:
            self._stop_event.set()

        if self.mqtt_bridge:
            try:
                self.mqtt_bridge.stop()
            except Exception as e:
                print(f"Error while stopping MQTT bridge: {e}")

        if self.controller:
            try:
                self.controller.stop()
            except Exception as e:
                print(f"Error while stopping RFID controller: {e}")

            try:
                if self.controller.thread and self.controller.thread.is_alive():
                    self.controller.thread.join(timeout=2)
            except Exception as e:
                print(f"Error while joining RFID reader thread: {e}")

        if self._queue_thread and self._queue_thread.is_alive():
            self._queue_thread.join(timeout=1)

        self.connection = None
        self.parser = None
        self.reader = None
        self.controller = None
        self.mqtt_bridge = None
        self._rfid_queue = None
        self._stop_event = None
        self._queue_thread = None
        self._reading_started = False

        print("RFID reading stopped")

    def startDashboard(self) -> None:
        if self._dashboard_started:
            return

        self._dashboard_thread = threading.Thread(
            target=run_dash,
            daemon=True,
        )
        self._dashboard_thread.start()

        self._dashboard_started = True
        print("RFID dashboard started")

    def getCrateData(self) -> RFIDTag | None:
        with self._lock:
            state = self.tag_manager.get_state()

            if not state:
                return None

            latest_tag = max(
                state.values(),
                key=lambda tag: tag.last_seen_at,
            )

            return copy.deepcopy(latest_tag)

    def getDashboardState(self) -> dict[str, RFIDTag]:
        with self._lock:
            return copy.deepcopy(self.tag_manager.get_state())

    def clearData(self) -> None:
        with self._lock:
            self.tag_manager.clear()

    def _processRfidQueue(
        self,
        stop_event: threading.Event,
        event_queue: Queue,
    ) -> None:
        while not stop_event.is_set():
            try:
                while True:
                    event = event_queue.get_nowait()

                    with self._lock:
                        self.tag_manager.process(event)

            except Empty:
                pass

            time.sleep(0.02)