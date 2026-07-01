# xml_parser.py

import time
import xml.etree.ElementTree as ET

from BE.models import RFIDEvent


class XMLParser:
    """
    Responsible only for converting raw XML into RFIDEvent objects.
    """

    def extract_frames(self, buffer: str) -> tuple[list[str], str]:
        """
        Extract complete <frame>...</frame> chunks from TCP stream buffer.
        Returns:
            (frames, remaining_buffer)
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
            buffer = buffer[end:]

            frames.append(frame)

        return frames, buffer
    
    def parse_frame(self, xml: str) -> list[RFIDEvent]:
        try:
            root = ET.fromstring(xml)
        except ET.ParseError as e:
            print("XML Parse Error:", e)
            return []

        events: list[RFIDEvent] = []

        for tag in root.findall(".//tag"):

            epc = tag.findtext("tagID")
            event = tag.findtext("event")
            antenna = tag.findtext("antennaName")
            rssi = tag.findtext("rSSI")

            tid = None
            for field in tag.findall("tagField"):
                if field.findtext("fieldName") == "TID":
                    tid = field.findtext("data")
                    break

            if not tid:
                continue

            events.append(
                RFIDEvent(
                    epc=epc,
                    tid=tid,
                    event=event,
                    antenna=antenna,
                    rssi=float(rssi) if rssi else 0.0,
                    timestamp=time.time(),
                )
            )

        return events