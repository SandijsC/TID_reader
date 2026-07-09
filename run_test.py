# run.py

import time

from rfid_manager import RfidManager


def main():
    rfidManager = RfidManager(use_mqtt=False)

    rfidManager.startDashboard()
    rfidManager.startReading()

    print("RFID manager running.")
    print("RFID state will be printed when an MQTT request is received.")

    print("RFID manager running.")
    print("Enter a crate ID to get its latest data.")
    print("Type 'q' or press Ctrl+C to exit.")

    try:
        while True:
            crate = input("crate_id> ").strip()

            if crate.lower() in ("q"):
                break

            try:
                crate_id = int(crate)
            except ValueError:
                print("Please enter a valid integer crate ID.")
                continue

            data = rfidManager.getLastCrateData(crate_id=crate_id)
            print(data)

    except KeyboardInterrupt:
        print("\nStopping...")

    finally:
        rfidManager.stopReading()
        print("Shutdown complete.")


if __name__ == "__main__":
    main()