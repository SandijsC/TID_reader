from dataclasses import dataclass, field


@dataclass(slots=True)
class RFIDEvent:
    """
    Represents a single RFID read event coming from the XML reader.
    """
    epc: str
    tid: str | None
    event: str | None
    antenna: str | None
    rssi: float
    timestamp: float


@dataclass(slots=True)
class RFIDTag:
    epc: str
    barcode: str
    first_seen_at: float
    last_seen_at: float
    tids: set[str] = field(default_factory=set)

    def update(self, tid: str | None, timestamp: float):
        self.last_seen_at = timestamp

        if tid:
            self.tids.add(tid)

    @property
    def reading_time(self) -> float:
        return self.last_seen_at - self.first_seen_at

    @property
    def tid_count(self) -> int:
        return len(self.tids)

    @property
    def status(self) -> str:
        return "PASSED" if self.tid_count >= 2 else "FAILED"