from BE.rfid_decode import decode_epc


class TagManager:
    def __init__(self):
        self.tags = {}

    def process(self, event):
        """
        Processes a single RFIDEvent.
        """

        epc = event.epc
        tid = event.tid
        timestamp = event.timestamp

        if not epc:
            return

        if epc not in self.tags:
            self.tags[epc] = {
                "first_seen_at": timestamp,
                "tids": set(),
            }

        tag = self.tags[epc]

        if tid:
            tag["tids"].add(tid)

        epc_info = decode_epc(epc)

        tag["barcode"] = epc_info.barcode
        tag["last_seen_at"] = timestamp
        tag["reading_time"] = tag["last_seen_at"] - tag["first_seen_at"]
        tag["tid_count"] = len(tag["tids"])

        tag["status"] = (
            "PASSED" if tag["tid_count"] >= 2 else "FAILED"
        )

    def get_state(self):
        return self.tags

    def clear(self):
        self.tags.clear()