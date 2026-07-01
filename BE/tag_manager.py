from BE.rfid_decode import decode_epc
from BE.models import RFIDTag


class TagManager:
    def __init__(self):
        self.tags: dict[str, RFIDTag] = {}

    def process(self, event):
        epc = event.epc
        tid = event.tid
        timestamp = event.timestamp

        if not epc:
            return

        if epc not in self.tags:
            epc_info = decode_epc(epc)

            self.tags[epc] = RFIDTag(
                epc=epc,
                barcode=epc_info.barcode,
                first_seen_at=timestamp,
                last_seen_at=timestamp,
            )

        tag = self.tags[epc]
        tag.update(tid, timestamp)

    def get_state(self):
        return self.tags

    def clear(self):
        self.tags.clear()