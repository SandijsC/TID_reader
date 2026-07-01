# xml_reader.py
import socket

class XMLReader:
    def __init__(self, connection, parser, event_queue):
        self.conn = connection
        self.parser = parser
        self.event_queue = event_queue
        self.buffer = ""

    def read_loop(self):
        print("Reader loop started")

        while True:
            try:
                data = self.conn.receive(65536)

            except socket.timeout:
                continue  # THIS IS REQUIRED

            except Exception as e:
                print("Reader loop crashed:", e)
                break

            if not data:
                print("Connection closed (no data)")
                break

            self.buffer += data.decode("utf-8", errors="ignore")

            frames, self.buffer = self.parser.extract_frames(self.buffer)

            for frame in frames:
                events = self.parser.parse_frame(frame)

                for event in events:
                    self.event_queue.put(event)