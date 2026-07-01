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
    """
    Represents the accumulated state of a unique EPC.
    Business logic will be added in later commits.
    """
    epc: str
    barcode: str
    first_seen_at: float
    last_seen_at: float
    tids: set[str] = field(default_factory=set)