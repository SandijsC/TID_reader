# connection.py

import socket
import threading
import time

from config import HOST, PORT


class Connection:
    def __init__(self):
        self.sock = None
        self.send_lock = threading.Lock()

    def connect(self):
        """
        Connect to the Siemens XML-Ident server.
        Retries until a connection is established.
        """
        while True:
            try:
                print(f"Connecting to {HOST}:{PORT}...")

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # Reuse socket quickly after reconnects
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                # Detect dead peers
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

                # Prevent recv() from blocking forever
                sock.settimeout(2.0)

                sock.connect((HOST, PORT))

                self.sock = sock

                print("Connected!")

                return self.sock

            except Exception as e:
                print(f"Connection failed: {e}")
                print("Retrying in 3 seconds...")
                time.sleep(3)

    def send(self, message):
        """
        Thread-safe send.
        """
        if not self.sock:
            raise ConnectionError("Socket is not connected")

        try:
            with self.send_lock:
                self.sock.sendall(message.encode("utf-8"))

        except Exception:
            self.close()
            raise

    def receive(self, buffer_size=65536):
        """
        Receive data from the socket.

        Returns bytes.
        Raises socket.timeout if no data arrives before timeout.
        """
        if not self.sock:
            raise ConnectionError("Socket is not connected")

        try:
            return self.sock.recv(buffer_size)

        except socket.timeout:
            raise

        except Exception:
            self.close()
            raise

    def send_and_receive(self, message, buffer_size=65536):
        """
        Send a request and wait for one response.

        Mostly useful for initialization commands.
        """
        self.send(message)
        return self.receive(buffer_size)

    def close(self):
        """
        Close the socket safely.
        """
        if self.sock:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                # Socket may already be closed
                pass
            except Exception:
                pass

            try:
                self.sock.close()
            except Exception:
                pass

            self.sock = None