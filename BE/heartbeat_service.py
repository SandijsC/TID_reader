import time
import threading

from BE.messages import Messages


class HeartbeatService:
    def __init__(self, connection, interval: float):
        self.connection = connection
        self.interval = interval
        self.running = False
        self.thread = None

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while self.running and self.connection.sock:
            try:
                time.sleep(self.interval)
                if self.running and self.connection.sock:
                    self.connection.send(Messages.heartbeat())
            except Exception as e:
                print("Heartbeat failed:", e)
                break

    def stop(self):
        self.running = False