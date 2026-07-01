# xml_reader.py

import threading
import time
import socket

from BE.connection import Connection
from BE.messages import Messages
from BE.parser import Parser
from config import HEARTBEAT_INTERVAL


class XMLReader():
    def __init__(self):
        self.conn = Connection()
        self.buffer = ""
        self.running = False
        self.heartbeat_thread = None

    def connect(self):
        """
        Connect to the reader and perform the XML greeting.
        """
        self.conn.connect()
        self.conn.send(Messages.host_greetings())

    def _heartbeat_loop(self):
        """
        Sends heartbeat messages periodically while connected.
        Runs in its own thread.
        """
        while self.running and self.conn.sock:
            try:
                time.sleep(HEARTBEAT_INTERVAL)

                if self.running and self.conn.sock:
                    self.conn.send(Messages.heartbeat())

            except Exception as e:
                print("Heartbeat failed:", e)
                break

    def _start_readpoints(self):
        print("Starting Readpoint_L...")
        self.conn.send(Messages.trigger("Readpoint_L", "Start"))

        time.sleep(0.1)

        print("Starting Readpoint_R...")
        self.conn.send(Messages.trigger("Readpoint_R", "Start"))

    def start(self):
        """
        Main receive loop.
        Automatically reconnects if the socket is lost.
        """
        self.running = True

        while self.running:

            try:
                if not self.conn.sock:
                    print("Connecting to XML reader...")
                    self.connect()

                    self.buffer = ""

                    # Start heartbeat thread
                    self.heartbeat_thread = threading.Thread(
                        target=self._heartbeat_loop,
                        daemon=True
                    )
                    self.heartbeat_thread.start()

                    # Start streaming
                    self._start_readpoints()

                while self.running and self.conn.sock:

                    data = self.conn.receive(65536)

                    # print(data.decode("utf-8", errors="ignore"))

                    if not data:
                        raise ConnectionError("Connection closed by reader")

                    self.buffer += data.decode(
                        "utf-8",
                        errors="ignore"
                    )

                    frames, self.buffer = Parser.extract_revelant_frames(
                        self.buffer
                    )

                    for frame in frames:
                        Parser.populate_queue(frame)

            except (
                socket.timeout,
                TimeoutError,
            ):
                # Normal timeout; continue waiting
                continue

            except Exception as e:

                print(f"XML connection lost: {e}")

                self.conn.close()

                if self.running:
                    print("Reconnecting in 2 seconds...")
                    time.sleep(2)

    def stop(self):
        """
        Stop reader cleanly.
        """
        self.running = False

        try:
            if self.conn.sock:
                self.conn.send(Messages.trigger("Readpoint_L", "Stop"))
                self.conn.send(Messages.trigger("Readpoint_R", "Stop"))
        except Exception:
            pass

        self.conn.close()