# run.py

import time

from rfid_manager import RfidManager


def main():
    rfidManager = RfidManager()

    rfidManager.startDashboard()
    rfidManager.startReading()

    print("RFID manager running.")
    print("RFID state will be printed when an MQTT request is received.")

    try:
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        rfidManager.stopReading()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()