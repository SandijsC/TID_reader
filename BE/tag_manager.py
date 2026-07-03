import threading

from BE.models import RFIDTag


class TagManager:
    def __init__(self):
        self.tags = {}
        self._lock = threading.RLock()

    def process(self, event):
        if not event.epc:
            return

        with self._lock:
            tag = self.tags.get(event.epc)

            if tag is None:
                tag = RFIDTag.from_event(event)
                self.tags[event.epc] = tag

            tag.update(event.tid, event.timestamp)

    def get_state(self):
        with self._lock:
            return {
                epc: self._copy_tag(tag)
                for epc, tag in self.tags.items()
            }

    def clear(self):
        with self._lock:
            self.tags.clear()

    @staticmethod
    def _copy_tag(tag: RFIDTag) -> RFIDTag:
        return RFIDTag(
            epc=tag.epc,
            barcode=tag.barcode,
            first_seen_at=tag.first_seen_at,
            last_seen_at=tag.last_seen_at,
            tids=set(tag.tids),
        )