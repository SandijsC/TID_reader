# run.py
import threading
import time
from queue import Empty

from FE.dashboard import run_dash, set_dashboard_state_provider
from queue import Queue
from BE.xml_reader import XMLReader
from BE.rfid_decode import decode_epc
from BE.tag_manager import TagManager
from BE.xml_parser import XMLParser


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

    parser = XMLParser()

    reader = XMLReader(
        rfid_queue,
        parser
    )

    try:
        reader.start()

    except KeyboardInterrupt:
        print("Stopping...")

    finally:
        stop_event.set()

        try:
            reader.stop()
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()