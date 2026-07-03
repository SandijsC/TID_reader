# run.py

import threading
import time
from queue import Queue, Empty

from FE.dashboard import run_dash, set_dashboard_state_provider

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


tag_manager = TagManager()


def process_rfid_queue(stop_event, event_queue, tag_manager: TagManager):
    while not stop_event.is_set():
        try:
            while True:
                event = event_queue.get_nowait()
                tag_manager.process(event)

        except Empty:
            pass

        time.sleep(0.02)


def get_dashboard_state():
    return tag_manager.get_state()


def clear_data():
    tag_manager.clear()


def main():
    stop_event = threading.Event()
    rfid_queue = Queue()

    set_dashboard_state_provider(get_dashboard_state, clear_data)

    dashboard_thread = threading.Thread(
        target=run_dash,
        daemon=True,
    )
    dashboard_thread.start()

    queue_thread = threading.Thread(
        target=process_rfid_queue,
        args=(stop_event, rfid_queue, tag_manager),
        daemon=True,
    )
    queue_thread.start()

    mqtt_bridge = PlcMqttBridge(
        broker=MQTT_BROKER,
        port=MQTT_PORT,
        request_topic=MQTT_REQUEST_TOPIC,
        response_topic=MQTT_RESPONSE_TOPIC,
        state_provider=get_dashboard_state,
        qos=MQTT_QOS,
    )

    connection = Connection()
    parser = XMLParser()

    reader = XMLReader(
        connection=connection,
        parser=parser,
        event_queue=rfid_queue,
    )

    controller = ReaderController(
        connection=connection,
        reader=reader,
        heartbeat_interval=HEARTBEAT_INTERVAL,
    )

    try:
        mqtt_bridge.start()

        controller.start()
        print("Controller started")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        print("Cleaning up...")

        stop_event.set()

        try:
            mqtt_bridge.stop()
        except Exception as e:
            print(f"Error while stopping MQTT bridge: {e}")

        try:
            controller.stop()
        except Exception as e:
            print(f"Error while stopping controller: {e}")

        print("Shutdown complete.")


if __name__ == "__main__":
    main()