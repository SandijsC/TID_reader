# run.py
import threading
import time
from queue import Empty

from FE.dashboard import run_dash, set_dashboard_state_provider
from BE.shared import rfid_queue
from BE.xml_reader import XMLReader
from BE.rfid_decode import decode_epc

epc_map = {}

def process_rfid_queue(stop_event):
    while not stop_event.is_set():
        try:
            while True:
                item = rfid_queue.get_nowait()

                epc = item.epc
                tid = item.tid
                timestamp = item.timestamp

                if not epc:
                    continue

                if epc not in epc_map:
                    epc_map[epc] = {
                        "first_seen_at": timestamp,
                        "tids": set(),
                    }

                if tid:
                    epc_map[epc]["tids"].add(tid)

                epc_info = decode_epc(epc)
                barcode = epc_info.barcode
                epc_map[epc]["barcode"] = barcode
                epc_map[epc]["last_seen_at"] = timestamp
                epc_map[epc]["reading_time"] = epc_map[epc]["last_seen_at"] - epc_map[epc]["first_seen_at"]
                epc_map[epc]["tid_count"] = len(epc_map[epc]["tids"])
                if epc_map[epc]["tid_count"] < 2:
                    epc_map[epc]["status"] = "FAILED"
                else:
                    epc_map[epc]["status"] = "PASSED"

        except Empty:
            pass

        time.sleep(0.02)


def get_dashboard_state():
    return epc_map

def clear_data():
    print(epc_map)
    epc_map.clear()
    print(epc_map)

def main():
    stop_event = threading.Event()

    set_dashboard_state_provider(get_dashboard_state, clear_data)

    dashboard_thread = threading.Thread(
        target=run_dash,
        daemon=True,
    )
    dashboard_thread.start()

    queue_thread = threading.Thread(
        target=process_rfid_queue,
        args=(stop_event,),
        daemon=True,
    )
    queue_thread.start()

    reader = XMLReader()

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