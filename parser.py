# xml_api/parser.py

import time
import xml.etree.ElementTree as ET

from shared import rfid_queue


class Parser:
    @staticmethod
    def extract_revelant_frames(buffer):
        """
        Extract complete <frame>...</frame> messages from the TCP stream.

        Since TCP is a byte stream, a recv() may contain:
            - half a frame
            - one frame
            - multiple frames

        This function returns all complete frames while leaving any
        incomplete XML in the buffer for the next recv().
        """
        frames = []

        while True:
            start = buffer.find("<frame>")
            if start == -1:
                break

            end = buffer.find("</frame>", start)
            if end == -1:
                break

            end += len("</frame>")

            frame = buffer[start:end]

            # Remove processed portion
            buffer = buffer[end:]

            # Only keep frames containing TID data
            if "<fieldName>TID</fieldName>" in frame:
                frames.append(frame)

        return frames, buffer

    @staticmethod
    def populate_queue(xml):
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as e:
            print("XML Parse Error:", e)
            return

        tags = root.findall(".//tag")

        for tag in tags:
            tag_id = tag.findtext("tagID")
            event = tag.findtext("event")
            antenna = tag.findtext("antennaName")
            rssi = tag.findtext("rSSI")

            tid = None

            for field in tag.findall("tagField"):

                if field.findtext("fieldName") == "TID":
                    tid = field.findtext("data")

            if not tid:
                continue

            rfid_queue.put({
                "tag_id": tag_id,
                "tid": tid,
                "event": event,
                "antenna": antenna,
                "rssi": float(rssi) if rssi else 0.0,
                "timestamp": time.time(),
            })