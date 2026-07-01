import threading
import time

from BE.messages import Messages
from BE.heartbeat_service import HeartbeatService


class ReaderController:
    def __init__(self, connection, reader, heartbeat_interval):
        self.connection = connection
        self.reader = reader
        self.heartbeat = HeartbeatService(connection, heartbeat_interval)
        self.thread = None
        self.running = False

    def start(self):
        self.connection.connect()
        self.connection.send(Messages.host_greetings())

        self._start_readpoints()

        self.heartbeat.start()

        self.running = True
        self.thread = threading.Thread(target=self.reader.read_loop, daemon=False)
        self.thread.start()

    def _start_readpoints(self):
        self.connection.send(Messages.trigger("Readpoint_L", "Start"))
        time.sleep(0.1)
        self.connection.send(Messages.trigger("Readpoint_R", "Start"))\
        
    def stop(self):
        self.running = False

        try:
            self.connection.send(Messages.trigger("Readpoint_L", "Stop"))
            self.connection.send(Messages.trigger("Readpoint_R", "Stop"))
        except Exception:
            pass

        self.heartbeat.stop()
        self.connection.close()