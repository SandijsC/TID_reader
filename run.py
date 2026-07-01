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
from config import HEARTBEAT_INTERVAL


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
        controller.start()
        print("Controller started")

        # Keep the main thread alive until Ctrl+C
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        print("Cleaning up...")

        stop_event.set()

        try:
            controller.stop()
        except Exception as e:
            print(f"Error while stopping controller: {e}")

        print("Shutdown complete.")


if __name__ == "__main__":
    main()