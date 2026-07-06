# run.py

import time

from rfid_manager import RfidManager


def main():
    rfidManager = RfidManager()

    rfidManager.startDashboard()
    rfidManager.startReading()

    try:
        while True:
            crateData = rfidManager.getCrateData()

            if crateData:
                print(crateData)

            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        rfidManager.stopReading()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()