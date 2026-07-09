import threading

from BE.models import RFIDTag


class TagManager:
    def __init__(self):
        self.tags = {}
        self._lock = threading.RLock()
        self.previousEpc= "NOT_AVAILABLE"

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

    def get_latest_tag(self, crate_id: str):
        state = self.get_state()

        if not state:
            return RFIDTag.empty(crate_id=crate_id)

        latest_tag = max(
            state.values(),
            key=lambda tag: tag.last_seen_at,
        )

        latest_tag.crate_id = crate_id

        if latest_tag.tid_count < 1 or self.previousEpc == latest_tag.epc:
            latest_tag.is_rejected = True
        else:
            latest_tag.is_rejected = False

        self.previousEpc = latest_tag.epc
        return latest_tag

    def clear(self):
        with self._lock:
            self.tags.clear()

    @staticmethod
    def _copy_tag(tag: RFIDTag) -> RFIDTag:
        return RFIDTag(
            crate_id=tag.crate_id,
            epc=tag.epc,
            barcode=tag.barcode,
            first_seen_at=tag.first_seen_at,
            last_seen_at=tag.last_seen_at,
            tids=set(tag.tids),
            is_rejected=tag.is_rejected
        )