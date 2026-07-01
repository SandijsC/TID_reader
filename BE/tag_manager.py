from BE.models import RFIDTag

class TagManager:
    def __init__(self):
        self.tags = {}

    def process(self, event):
        if not event.epc:
            return

        tag = self.tags.get(event.epc)

        if tag is None:
            tag = RFIDTag.from_event(event)
            self.tags[event.epc] = tag

        tag.update(event.tid, event.timestamp)

    def get_state(self):
        return self.tags

    def clear(self):
        self.tags.clear()